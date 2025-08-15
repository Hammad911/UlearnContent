import pdfplumber
import PyPDF2
import fitz  # PyMuPDF
from PIL import Image
import io
import os
import re
from typing import List, Dict, Any, Tuple
import logging
from app.services.ocr_service import OCRService
from app.services.mistral_ocr_service import MistralOCRService
from app.core.config import settings

logger = logging.getLogger(__name__)

class PDFService:
    """Service for processing PDF files and extracting text and images"""
    
    def __init__(self):
        self.ocr_service = OCRService()
        # Initialize Mistral OCR if API key is available
        if hasattr(settings, 'MISTRAL_API_KEY') and settings.MISTRAL_API_KEY:
            self.mistral_ocr = MistralOCRService(settings.MISTRAL_API_KEY)
        else:
            self.mistral_ocr = None
            logger.warning("Mistral API key not configured, using fallback OCR")
    
    async def extract_text_from_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """
        Extract text from PDF file, including text from images
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Dictionary containing extracted text and metadata
        """
        try:
            if not os.path.exists(pdf_path):
                raise FileNotFoundError(f"PDF file not found: {pdf_path}")
            
            # Extract text using pdfplumber
            text_content = await self._extract_text_with_pdfplumber(pdf_path)
            
            # Extract images and perform OCR
            image_results = await self._extract_images_and_ocr(pdf_path)
            
            # Process image results and combine with text
            image_texts = []
            tables = []
            formulas = []
            diagrams = []
            
            for result in image_results:
                if result['content_type'] == 'table':
                    tables.append(result)
                    if 'table_data' in result:
                        image_texts.append(f"[Table from page {result.get('page', 'unknown')}]: {result['table_data']}")
                    else:
                        image_texts.append(f"[Table from page {result.get('page', 'unknown')}]: {result.get('text', '')}")
                elif result['content_type'] == 'formula':
                    formulas.append(result)
                    image_texts.append(f"[Formula from page {result.get('page', 'unknown')}]: {result.get('latex', result.get('text', ''))}")
                elif result['content_type'] == 'diagram':
                    diagrams.append(result)
                    image_texts.append(f"[Diagram from page {result.get('page', 'unknown')}]: {result.get('description', result.get('text', ''))}")
                else:
                    image_texts.append(f"[Image from page {result.get('page', 'unknown')}]: {result.get('text', '')}")
            
            # Combine all text
            all_text = text_content['text'] + '\n\n' + '\n\n'.join(image_texts)
            
            # Extract structure (chapters and sections)
            structure = await self._extract_structure(text_content['text'])
            
            return {
                'success': True,
                'text': all_text,
                'structure': structure,
                'pages': text_content['pages'],
                'image_count': len(image_results),
                'total_pages': text_content['total_pages'],
                'content_breakdown': {
                    'tables': len(tables),
                    'formulas': len(formulas),
                    'diagrams': len(diagrams),
                    'general_images': len(image_results) - len(tables) - len(formulas) - len(diagrams)
                },
                'detailed_content': {
                    'tables': tables,
                    'formulas': formulas,
                    'diagrams': diagrams
                }
            }
            
        except Exception as e:
            logger.error(f"Error extracting text from PDF {pdf_path}: {str(e)}")
            raise
    
    async def _extract_text_with_pdfplumber(self, pdf_path: str) -> Dict[str, Any]:
        """Extract text using pdfplumber"""
        text_parts = []
        pages_info = []
        
        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)
            
            for page_num, page in enumerate(pdf.pages, 1):
                try:
                    # Extract text from page
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(f"--- Page {page_num} ---\n{page_text}")
                        pages_info.append({
                            'page': page_num,
                            'text_length': len(page_text),
                            'has_images': len(page.images) > 0
                        })
                    else:
                        pages_info.append({
                            'page': page_num,
                            'text_length': 0,
                            'has_images': len(page.images) > 0
                        })
                        
                except Exception as e:
                    logger.warning(f"Error extracting text from page {page_num}: {str(e)}")
                    pages_info.append({
                        'page': page_num,
                        'text_length': 0,
                        'has_images': False,
                        'error': str(e)
                    })
        
        return {
            'text': '\n\n'.join(text_parts),
            'pages': pages_info,
            'total_pages': total_pages
        }
    
    async def _extract_images_and_ocr(self, pdf_path: str) -> List[Dict[str, Any]]:
        """Extract images from PDF and perform advanced OCR with content type detection"""
        image_results = []
        
        try:
            # Use PyMuPDF for image extraction
            doc = fitz.open(pdf_path)
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                
                # Get images from page
                image_list = page.get_images()
                
                for img_index, img in enumerate(image_list):
                    try:
                        # Get image data
                        xref = img[0]
                        pix = fitz.Pixmap(doc, xref)
                        
                        try:
                            if pix.n - pix.alpha < 4:  # GRAY or RGB
                                img_data = pix.tobytes("png")
                            else:  # CMYK: convert to RGB first
                                pix1 = fitz.Pixmap(fitz.csRGB, pix)
                                img_data = pix1.tobytes("png")
                                pix1 = None
                            
                            # Save image temporarily
                            temp_img_path = f"temp_image_{page_num}_{img_index}.png"
                            with open(temp_img_path, "wb") as img_file:
                                img_file.write(img_data)
                                
                        except Exception as img_error:
                            logger.warning(f"Error processing image {img_index} on page {page_num}: {str(img_error)}")
                            pix = None
                            continue
                        
                        # Detect content type
                        content_type = self._detect_content_type(temp_img_path)
                        
                        # Use Mistral OCR for formulas, regular OCR for other content
                        try:
                            if content_type == "formula" and self.mistral_ocr:
                                # Use Mistral for formula extraction
                                ocr_result = await self.mistral_ocr.extract_formula_from_image(temp_img_path)
                                ocr_result['page'] = page_num + 1
                                ocr_result['image_index'] = img_index
                            else:
                                # Use regular OCR for other content
                                ocr_text = await self.ocr_service.extract_text(temp_img_path)
                                ocr_result = {
                                    'success': True,
                                    'text': ocr_text,
                                    'content_type': content_type,
                                    'page': page_num + 1,
                                    'image_index': img_index
                                }
                        except Exception as ocr_error:
                            logger.error(f"OCR failed for image {img_index} on page {page_num}: {str(ocr_error)}")
                            ocr_result = {
                                'success': False,
                                'text': '',
                                'error': str(ocr_error),
                                'content_type': content_type,
                                'page': page_num + 1,
                                'image_index': img_index
                            }
                        
                        if ocr_result['success']:
                            image_results.append(ocr_result)
                        
                        # Clean up
                        os.remove(temp_img_path)
                        pix = None
                        
                    except Exception as e:
                        logger.warning(f"Error processing image {img_index} on page {page_num}: {str(e)}")
                        continue
            
            doc.close()
            
        except Exception as e:
            logger.error(f"Error extracting images from PDF: {str(e)}")
        
        return image_results
    
    async def _process_image_with_mistral(self, image_path: str, content_type: str) -> Dict[str, Any]:
        """Process image using Mistral AI based on content type"""
        try:
            if content_type == "table":
                return await self.mistral_ocr.extract_table_from_image(image_path)
            elif content_type == "formula":
                return await self.mistral_ocr.extract_formula_from_image(image_path)
            elif content_type == "diagram":
                return await self.mistral_ocr.extract_diagram_from_image(image_path)
            else:
                return await self.mistral_ocr.extract_text_from_image(image_path, content_type)
        except Exception as e:
            logger.error(f"Error processing image with Mistral: {str(e)}")
            # Fallback to regular OCR
            ocr_text = await self.ocr_service.extract_text(image_path)
            return {
                'success': True,
                'text': ocr_text,
                'content_type': content_type,
                'error': str(e)
            }
    
    def _detect_content_type(self, image_path: str) -> str:
        """Detect the type of content in the image"""
        if self.mistral_ocr:
            return self.mistral_ocr.detect_content_type(image_path)
        else:
            # Basic detection without Mistral
            return "general"
    
    async def _extract_structure(self, text: str) -> Dict[str, Any]:
        """Extract chapter and section structure from text"""
        structure = {
            'chapters': [],
            'sections': []
        }
        
        # Enhanced chapter patterns for educational content
        chapter_patterns = [
            r'^Chapter\s+(\d+)[:\s]*(.+)$',
            r'^CHAPTER\s+(\d+)[:\s]*(.+)$',
            r'^(\d+)\.\s*(.+)$',
            r'^(\d+)\s+(.+)$',
            r'^Unit\s+(\d+)[:\s]*(.+)$',
            r'^UNIT\s+(\d+)[:\s]*(.+)$',
            r'^Lesson\s+(\d+)[:\s]*(.+)$',
            r'^LESSON\s+(\d+)[:\s]*(.+)$',
            r'^Topic\s+(\d+)[:\s]*(.+)$',
            r'^TOPIC\s+(\d+)[:\s]*(.+)$',
            r'^Section\s+(\d+)[:\s]*(.+)$',
            r'^SECTION\s+(\d+)[:\s]*(.+)$',
            # For curriculum documents
            r'^(\d+\.\d+)\s*(.+)$',  # 1.1, 1.2, etc.
            r'^(\d+\.\d+\.\d+)\s*(.+)$',  # 1.1.1, 1.1.2, etc.
        ]
        
        # Enhanced section patterns
        section_patterns = [
            r'^(\d+\.\d+\.\d+)\s*(.+)$',
            r'^(\d+\.\d+\.\d+\.\d+)\s*(.+)$',
            r'^([A-Z][A-Z\s]+)$',
            r'^([A-Z][a-z\s]+)$',
            r'^([a-z][a-z\s]+)$',
            r'^([A-Z][a-z]+[A-Z][a-z\s]+)$',  # CamelCase headings
        ]
        
        lines = text.split('\n')
        
        for line_num, line in enumerate(lines):
            line = line.strip()
            
            # Skip empty lines and very short lines
            if not line or len(line) < 3:
                continue
                
            # Check for chapters
            for pattern in chapter_patterns:
                match = re.match(pattern, line, re.IGNORECASE)
                if match:
                    chapter_title = match.group(2).strip() if len(match.groups()) > 1 else match.group(1)
                    # Skip if the title is too short or looks like a page number
                    if len(chapter_title) > 2 and not chapter_title.isdigit():
                        structure['chapters'].append({
                            'number': match.group(1),
                            'title': chapter_title,
                            'line': line_num + 1
                        })
                    break
            
            # Check for sections (only if no chapter was found)
            if not any(re.match(pattern, line, re.IGNORECASE) for pattern in chapter_patterns):
                for pattern in section_patterns:
                    match = re.match(pattern, line)
                    if match:
                        section_title = match.group(2).strip() if len(match.groups()) > 1 else match.group(1)
                        # Skip if the title is too short
                        if len(section_title) > 2:
                            structure['sections'].append({
                                'number': match.group(1),
                                'title': section_title,
                                'line': line_num + 1
                            })
                        break
        
        # Sort chapters and sections by line number
        structure['chapters'].sort(key=lambda x: x['line'])
        structure['sections'].sort(key=lambda x: x['line'])
        
        logger.info(f"Extracted {len(structure['chapters'])} chapters and {len(structure['sections'])} sections")
        
        return structure
    
    async def create_excel_content(self, pdf_text: str, structure: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create structured content for Excel based on PDF text and structure
        
        Args:
            pdf_text: Extracted text from PDF
            structure: Extracted structure information
            
        Returns:
            Dictionary containing Excel-ready data with multiple rows per chapter
        """
        try:
            # Use LLM to analyze and structure the content
            content_analysis = await self._analyze_content_with_llm(pdf_text, structure)
            
            # Create Excel data structure - each subtopic gets its own row
            excel_data = []
            
            for item in content_analysis:
                # Each item represents a different subtopic and gets its own row
                excel_data.append({
                    'Topic': item.get('topic', ''),
                    'Subtopic': item.get('subtopic', ''),
                    'Content': item.get('content', ''),
                    'Video_Link': item.get('video_link', '')
                })
            
            logger.info(f"Created {len(excel_data)} Excel rows from {len(content_analysis)} content items")
            
            return {
                'success': True,
                'data': excel_data,
                'total_items': len(excel_data)
            }
            
        except Exception as e:
            logger.error(f"Error creating Excel content: {str(e)}")
            raise
    
    async def _analyze_content_with_llm(self, text: str, structure: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Use LLM to analyze content and create structured data
        """
        try:
            from app.services.llm_service import LLMService
            
            llm_service = LLMService()
            content_items = []
            
            logger.info(f"Starting LLM content analysis. Text length: {len(text)}")
            logger.info(f"Structure: {structure}")
            
            # Split text into chunks based on structure
            if structure.get('chapters'):
                logger.info(f"Found {len(structure['chapters'])} chapters")
                for i, chapter in enumerate(structure['chapters']):
                    logger.info(f"Processing chapter {i+1}: {chapter}")
                    
                    # Get chapter content
                    chapter_start = chapter['line']
                    chapter_end = len(text.split('\n')) if chapter == structure['chapters'][-1] else structure['chapters'][structure['chapters'].index(chapter) + 1]['line']
                    
                    # Extract chapter text
                    lines = text.split('\n')
                    chapter_text = '\n'.join(lines[chapter_start-1:chapter_end-1])
                    
                    logger.info(f"Chapter {i+1} text length: {len(chapter_text)}")
                    
                    # Generate structured content for this chapter with subtopics
                    try:
                        # Use the new improved content generation method
                        content_result = await llm_service.generate_educational_content(
                            text=chapter_text,
                            topic=f"Chapter {chapter['number']}: {chapter['title']}"
                        )
                        
                        if content_result['success']:
                            logger.info(f"Generated {len(content_result['content_items'])} content items for chapter {i+1}")
                            
                            # Add all content items to the list
                            for item in content_result['content_items']:
                                content_items.append({
                                    'topic': item.get('topic', f"Chapter {chapter['number']}: {chapter['title']}"),
                                    'subtopic': item.get('subtopic', ''),
                                    'content': item.get('content', ''),
                                    'video_link': item.get('video_link', '')
                                })
                        else:
                            logger.error(f"Content generation failed for chapter {i+1}: {content_result.get('error', 'Unknown error')}")
                            # Fallback to basic content
                            content_items.append({
                                'topic': f"Chapter {chapter['number']}: {chapter['title']}",
                                'subtopic': 'Main Content',
                                'content': chapter_text[:1000] + "..." if len(chapter_text) > 1000 else chapter_text,
                                'video_link': ''
                            })
                            
                    except Exception as chapter_error:
                        logger.error(f"Error processing chapter {i+1}: {str(chapter_error)}")
                        # Fallback to basic content
                        content_items.append({
                            'topic': f"Chapter {chapter['number']}: {chapter['title']}",
                            'subtopic': 'Main Content',
                            'content': chapter_text[:1000] + "..." if len(chapter_text) > 1000 else chapter_text,
                            'video_link': ''
                        })
            else:
                # No chapters found, process entire text
                logger.info("No chapters found, processing entire text")
                try:
                    content_result = await llm_service.generate_educational_content(text=text)
                    
                    if content_result['success']:
                        logger.info(f"Generated {len(content_result['content_items'])} content items")
                        
                        for item in content_result['content_items']:
                            content_items.append({
                                'topic': item.get('topic', 'General Content'),
                                'subtopic': item.get('subtopic', ''),
                                'content': item.get('content', ''),
                                'video_link': item.get('video_link', '')
                            })
                    else:
                        logger.error(f"Content generation failed: {content_result.get('error', 'Unknown error')}")
                        # Fallback to basic content
                        content_items.append({
                            'topic': 'General Content',
                            'subtopic': 'Main Content',
                            'content': text[:1000] + "..." if len(text) > 1000 else text,
                            'video_link': ''
                        })
                        
                except Exception as e:
                    logger.error(f"Error processing entire text: {str(e)}")
                    # Final fallback
                    content_items.append({
                        'topic': 'General Content',
                        'subtopic': 'Main Content',
                        'content': text[:1000] + "..." if len(text) > 1000 else text,
                        'video_link': ''
                    })
            
            logger.info(f"Total content items generated: {len(content_items)}")
            return content_items
            
        except Exception as e:
            logger.error(f"Error in LLM content analysis: {str(e)}")
            # Return basic fallback
            return [{
                'topic': 'General Content',
                'subtopic': 'Main Content',
                'content': text[:1000] + "..." if len(text) > 1000 else text,
                'video_link': ''
            }]