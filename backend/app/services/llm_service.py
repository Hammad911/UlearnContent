import openai
import asyncio
import time
from typing import Dict, Any, List
import logging
import json
import google.generativeai as genai
from datetime import datetime
import requests
import re

from app.core.config import settings
from app.services.image_service import ImageService
from app.services.s3_service import upload_image_bytes

logger = logging.getLogger(__name__)

class LLMService:
    """Simplified service for LLM text processing and educational content generation"""
    
    def __init__(self):
        # Configure OpenAI client
        if settings.OPENAI_API_KEY:
            openai.api_key = settings.OPENAI_API_KEY
        else:
            logger.warning("OpenAI API key not configured")
        
        # Configure Gemini client
        if settings.GEMINI_API_KEY:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            self.gemini_model = genai.GenerativeModel(settings.GEMINI_MODEL)
        else:
            self.gemini_model = None
            logger.warning("Gemini API key not configured")
        # Image generation service (fal.ai)
        self.image_service = ImageService()
        
        # S3 service for image uploads
        self.s3_service = S3Service()
    
        # Rate limiting
        self.last_gemini_call = 0
        self.gemini_calls_this_minute = 0
        self.minute_start = time.time()
    
    def _check_gemini_rate_limit(self) -> bool:
        """Check if we can make a Gemini API call without hitting rate limits"""
        current_time = time.time()
        
        # Reset counter if a minute has passed
        if current_time - self.minute_start >= 60:
            self.gemini_calls_this_minute = 0
            self.minute_start = current_time
        
        # Check if we're under the limit (8 calls per minute to be safe)
        if self.gemini_calls_this_minute >= 8:
            logger.warning("Gemini rate limit approaching, using OpenAI fallback")
            return False
        
        # Add minimum delay between calls
        if current_time - self.last_gemini_call < 2:  # 2 second minimum delay
            time.sleep(2 - (current_time - self.last_gemini_call))
        
        return True
    
    def _increment_gemini_calls(self):
        """Increment the Gemini call counter"""
        self.gemini_calls_this_minute += 1
        self.last_gemini_call = time.time()

    # ---------- Subtopic governance helpers ----------
    def _compute_target_subtopic_count(self, text: str) -> int:
        """Return an adaptive subtopic count based on content length.
        Heuristic in words:
        - <= 300 words: 1
        - 301-800: 2
        - 801-1400: 3-4
        - 1401-2400: 5-6
        - 2401-4000: 7-9
        - > 4000: up to 12 (cap)
        """
        words = len(re.findall(r"\w+", text))
        if words <= 300:
            return 1
        if words <= 800:
            return 2
        if words <= 1400:
            return 4
        if words <= 2400:
            return 6
        if words <= 4000:
            return 9
        return 12

    def _normalize_subtopic(self, name: str) -> str:
        name = name.strip()
        # Remove trailing punctuation and multiple dots
        name = re.sub(r"\.{2,}$", "", name)
        # Title-case key phrases but keep acronyms
        return re.sub(r"\s+", " ", name)

    def _root_key(self, name: str) -> str:
        """Return a root key for merging similar subtopics (e.g., 'peptidoglycan')."""
        lowered = re.sub(r"[^a-z0-9\s]", " ", name.lower())
        tokens = [t for t in lowered.split() if t not in {
            'the','a','an','of','in','and','on','to','for','with','by','about','overview','introduction','basics','basic','concepts','role','nature'
        }]
        if not tokens:
            return lowered.strip()
        # Prefer longest informative token (captures things like 'peptidoglycan')
        return max(tokens, key=len)

    def _dedupe_and_limit_subtopics(self, raw_subtopics: List[str], target_count: int) -> List[str]:
        """Normalize, de-duplicate near-duplicates (by root key), and limit to target_count."""
        seen_norm = set()
        seen_roots = set()
        result: List[str] = []
        for s in raw_subtopics:
            if not s or not isinstance(s, str):
                continue
            norm = self._normalize_subtopic(s)
            root = self._root_key(norm)
            if norm.lower() in seen_norm:
                continue
            if root in seen_roots:
                # Already have a variant of this concept; skip to avoid repeats like many 'peptidoglycan'
                continue
            result.append(norm)
            seen_norm.add(norm.lower())
            seen_roots.add(root)
            if len(result) >= target_count:
                break
        # Ensure at least one subtopic
        if not result:
            result = ["Main Content"]
        return result
    
    async def generate_educational_content(self, text: str, topic: str = None) -> Dict[str, Any]:
        """
        Generate educational content from OCR extracted text - optimized for speed
        
        Args:
            text: OCR extracted text
            topic: Topic or subject area (optional)
            
        Returns:
            Dictionary containing generated content and metadata
        """
        try:
            start_time = time.time()
            
            # Limit text length for faster processing
            max_text_length = 2000  # Reduced from 3000
            processed_text = text[:max_text_length]
            
            # Quick content type detection
            is_math_content = any(keyword in text.lower() for keyword in [
                'equation', 'formula', 'theorem', 'proof', 'mathematics', 'algebra', 
                'calculus', 'geometry', 'trigonometry', 'complex', 'polynomial'
            ])
            
            # Convert formulas to MathJax only for mathematical content
            if is_math_content:
                processed_text = await self._convert_formulas_with_mathpix(processed_text)
            
            # Simplified, faster analysis prompt
            analysis_prompt = f"""
            Quickly analyze this educational text and identify 5-7 specific subtopics.
            
            Text: {processed_text}
            
            Return JSON:
            {{
                "main_chapter": "Chapter name",
                "subtopics": ["Subtopic 1", "Subtopic 2", "Subtopic 3", "Subtopic 4", "Subtopic 5"]
            }}
            
            Guidelines:
            - Identify specific, concrete subtopics
            - Focus on main concepts, definitions, processes, or topics
            - Keep subtopic names concise and clear
            - Aim for 5-7 subtopics maximum
            """
            
            # Get structure analysis with timeout
            try:
                if self.gemini_model and self._check_gemini_rate_limit():
                    try:
                        structure_response = await asyncio.wait_for(
                            self._call_gemini(analysis_prompt), 
                            timeout=30.0  # 30 second timeout
                        )
                        self._increment_gemini_calls()
                    except Exception as gemini_error:
                        if "429" in str(gemini_error) or "quota" in str(gemini_error).lower():
                            logger.warning("Gemini rate limit hit, falling back to OpenAI")
                            if settings.OPENAI_API_KEY:
                                structure_response = await asyncio.wait_for(
                                    self._call_openai(analysis_prompt), 
                                    timeout=30.0
                                )
                            else:
                                raise gemini_error
                        else:
                            raise gemini_error
                else:
                    structure_response = await asyncio.wait_for(
                        self._call_openai(analysis_prompt), 
                        timeout=30.0
                    )
            except asyncio.TimeoutError:
                logger.warning("Structure analysis timed out, using fallback")
                structure_response = '{"main_chapter": "' + (topic or 'General Content') + '", "subtopics": ["Introduction", "Main Concepts", "Key Definitions", "Important Processes", "Applications"]}'
            
            # Parse structure
            try:
                cleaned_structure = structure_response.strip()
                if cleaned_structure.startswith('```json'):
                    cleaned_structure = cleaned_structure[7:]
                if cleaned_structure.endswith('```'):
                    cleaned_structure = cleaned_structure[:-3]
                cleaned_structure = cleaned_structure.strip()
                
                structure_data = json.loads(cleaned_structure)
                # Always keep topic constant: prefer explicit topic, else main_chapter from model, else default
                main_chapter = topic or structure_data.get('main_chapter') or 'General Content'
                raw_subtopics = structure_data.get('subtopics', [])
                if not isinstance(raw_subtopics, list):
                    raw_subtopics = []
                
                # Compute adaptive cap and normalize/dedupe
                target_count = self._compute_target_subtopic_count(text)
                subtopics = self._dedupe_and_limit_subtopics(raw_subtopics, target_count)
                
                # Ensure we have subtopics
                if not subtopics or len(subtopics) < 1:
                    subtopics = await self._generate_quick_subtopics(processed_text, main_chapter)
                    subtopics = self._dedupe_and_limit_subtopics(subtopics, target_count)
                    
            except Exception as e:
                logger.warning(f"Structure parsing failed: {str(e)}")
                main_chapter = topic or 'General Content'
                target_count = self._compute_target_subtopic_count(text)
                subtopics = await self._generate_quick_subtopics(processed_text, main_chapter)
                subtopics = self._dedupe_and_limit_subtopics(subtopics, target_count)
            
            # Generate content for each subtopic with timeout
            content_items = []
            
            for i, subtopic in enumerate(subtopics):
                # Respect adaptive cap
                if len(content_items) >= target_count:
                    break
                
                # Add delay between calls to prevent rate limiting
                if i > 0:
                    await asyncio.sleep(1)  # 1 second delay between calls
                
                # Simplified, faster content prompt
                content_prompt = f"""
                Create brief educational content for "{subtopic}" based on this text.
                
                Chapter: {main_chapter}
                Subtopic: {subtopic}
                Text: {processed_text[:1000]}  # Reduced text length
                
                Guidelines:
                - Write 2-3 concise paragraphs (100-200 words)
                - Focus only on this specific subtopic
                - Use clear, simple language
                - Include key points and examples
                - Keep it educational but brief
                """
                
                try:
                    if self.gemini_model and self._check_gemini_rate_limit():
                        try:
                            content_response = await asyncio.wait_for(
                                self._call_gemini(content_prompt), 
                                timeout=45.0  # 45 second timeout per subtopic
                            )
                            self._increment_gemini_calls()
                        except Exception as gemini_error:
                            if "429" in str(gemini_error) or "quota" in str(gemini_error).lower():
                                logger.warning(f"Gemini rate limit hit for subtopic {subtopic}, falling back to OpenAI")
                                if settings.OPENAI_API_KEY:
                                    content_response = await asyncio.wait_for(
                                        self._call_openai(content_prompt), 
                                        timeout=45.0
                                    )
                                else:
                                    raise gemini_error
                            else:
                                raise gemini_error
                    else:
                        content_response = await asyncio.wait_for(
                            self._call_openai(content_prompt), 
                            timeout=45.0
                        )
                    
                    generated_text = content_response.strip()

                    # Conditionally generate an image if it's likely helpful
                    image_url: str = ""
                    if self.image_service.is_configured() and self._needs_image(subtopic, generated_text):
                        try:
                            diagram_prompt = self._build_image_prompt(main_chapter, subtopic, generated_text)
                            img_bytes = self.image_service.generate_diagram_png(diagram_prompt)
                            if img_bytes:
                                image_url = self.s3_service.upload_image_bytes(img_bytes, main_chapter, subtopic)
                        except Exception as img_err:
                            logger.warning(f"Image generation/upload failed for '{subtopic}': {str(img_err)}")

                    # Always include the generated content, and add image URL if available
                    content_value = generated_text
                    if image_url:
                        # Add the image URL to the content where it's most relevant
                        content_value += f"\n\n[Image: {image_url}]"
                    
                    content_items.append({
                        'topic': main_chapter,  # constant topic
                        'subtopic': subtopic,
                        'content': content_value,
                        'image_url': image_url
                    })
                    
                except asyncio.TimeoutError:
                    logger.warning(f"Content generation timed out for subtopic: {subtopic}")
                    # Add fallback content
                    content_items.append({
                        'topic': main_chapter,
                        'subtopic': subtopic,
                        'content': f"Content for {subtopic} based on the provided educational material."
                    })
                except Exception as e:
                    logger.warning(f"Error generating content for {subtopic}: {str(e)}")
                    # Add fallback content
                    content_items.append({
                        'topic': main_chapter,
                        'subtopic': subtopic,
                        'content': f"Content for {subtopic} based on the provided educational material."
                    })
                    continue
            
            # Ensure we have at least some content
            if len(content_items) == 0:
                content_items = [{
                    'topic': main_chapter,
                    'subtopic': 'Main Content',
                    'content': processed_text[:500] + "..." if len(processed_text) > 500 else processed_text
                }]
            
            processing_time = time.time() - start_time
            
            return {
                'success': True,
                'original_text': text,
                'content_items': content_items,
                'topic': main_chapter,
                'processed_at': datetime.now(),
                'processing_time': processing_time,
                'total_items': len(content_items)
            }
            
        except Exception as e:
            logger.error(f"Error generating educational content: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'original_text': text,
                'content_items': []
            }
    
    async def _generate_quick_subtopics(self, text: str, main_chapter: str) -> List[str]:
        """Generate subtopics quickly with timeout"""
        try:
            prompt = f"""
            Quickly suggest 5-6 specific subtopics for this educational content.
            
            Chapter: {main_chapter}
            Text: {text[:1000]}
            
            Return JSON array: ["Subtopic 1", "Subtopic 2", "Subtopic 3", "Subtopic 4", "Subtopic 5"]
            
            Focus on main concepts, definitions, processes, or key topics.
            """
            
            if self.gemini_model and self._check_gemini_rate_limit():
                try:
                    response = await asyncio.wait_for(
                        self._call_gemini(prompt), 
                        timeout=20.0
                    )
                    self._increment_gemini_calls()
                except Exception as gemini_error:
                    if "429" in str(gemini_error) or "quota" in str(gemini_error).lower():
                        logger.warning("Gemini rate limit hit in quick subtopics, falling back to OpenAI")
                        if settings.OPENAI_API_KEY:
                            response = await asyncio.wait_for(
                                self._call_openai(prompt), 
                                timeout=20.0
                            )
                        else:
                            raise gemini_error
                    else:
                        raise gemini_error
            else:
                response = await asyncio.wait_for(
                    self._call_openai(prompt), 
                    timeout=20.0
                )
            
            try:
                cleaned_response = response.strip()
                if cleaned_response.startswith('```json'):
                    cleaned_response = cleaned_response[7:]
                if cleaned_response.endswith('```'):
                    cleaned_response = cleaned_response[:-3]
                cleaned_response = cleaned_response.strip()
                
                subtopics = json.loads(cleaned_response)
                if isinstance(subtopics, list) and len(subtopics) > 0:
                    return subtopics[:6]  # Limit to 6 subtopics
            except:
                pass
            
            # Quick fallback subtopics
            return [
                "Introduction",
                "Main Concepts", 
                "Key Definitions",
                "Important Processes",
                "Applications",
                "Summary"
            ]
                
        except Exception as e:
            logger.warning(f"Quick subtopic generation failed: {str(e)}")
            return [
                "Introduction",
                "Main Concepts",
                "Key Definitions", 
                "Important Processes",
                "Applications"
            ]
    
    async def _convert_formulas_with_mathpix(self, text: str) -> str:
        """
        Convert mathematical formulas in text to MathJax format using MathPix
        
        Args:
            text: Text that may contain mathematical formulas
            
        Returns:
            Text with formulas converted to MathJax format
        """
        try:
            # Check if MathPix API key is available
            if not hasattr(settings, 'MATHPIX_API_KEY') or not settings.MATHPIX_API_KEY:
                return text
            
            # Look for potential mathematical expressions
            
            # Simple pattern to identify potential formulas
            formula_patterns = [
                r'[A-Z]\([a-z]\)\s*=\s*[^.!?]+',  # P(z) = ...
                r'[a-zA-Z]_{[^}]+}',  # a_{n}
                r'\\[a-zA-Z]+',  # LaTeX commands
                r'[a-zA-Z]\^[0-9]+',  # x^2
                r'√[^.!?]+',  # Square roots
            ]
            
            formulas_found = []
            for pattern in formula_patterns:
                matches = re.findall(pattern, text)
                formulas_found.extend(matches)
            
            if not formulas_found:
                return text
            
            # Use MathPix to convert formulas
            converted_text = text
            for formula in set(formulas_found):  # Remove duplicates
                try:
                    mathpix_response = await self._call_mathpix(formula)
                    if mathpix_response:
                        converted_text = converted_text.replace(formula, mathpix_response)
                except Exception as e:
                    logger.warning(f"MathPix conversion failed for {formula}: {str(e)}")
                    continue
            
            return converted_text
            
        except Exception as e:
            logger.warning(f"MathPix conversion failed: {str(e)}")
            return text
    
    async def _call_mathpix(self, formula: str) -> str:
        """
        Call MathPix API to convert formula to MathJax
        
        Args:
            formula: Mathematical formula to convert
            
        Returns:
            MathJax formatted formula
        """
        try:
            url = "https://api.mathpix.com/v3/text"
            headers = {
                "app_id": settings.MATHPIX_APP_ID,
                "app_key": settings.MATHPIX_API_KEY,
                "Content-type": "application/json"
            }
            
            data = {
                "src": formula,
                "formats": ["text", "data"]
            }
            
            # Run the request in a thread pool
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, 
                lambda: requests.post(url, headers=headers, json=data, timeout=10)
            )
            
            if response.status_code == 200:
                result = response.json()
                # Return the LaTeX format if available
                if 'data' in result and result['data']:
                    return result['data'][0]['value']
                elif 'text' in result:
                    return result['text']
            
            return formula
            
        except Exception as e:
            logger.warning(f"MathPix API call failed: {str(e)}")
            return formula
    
    async def _call_gemini(self, prompt: str) -> str:
        """
        Make API call to Gemini
        
        Args:
            prompt: Input prompt
            
        Returns:
            Response from Gemini
        """
        try:
            if self.gemini_model:
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(None, self.gemini_model.generate_content, prompt)
                return response.text.strip()
            else:
                raise Exception("Gemini API key not configured")
            
        except Exception as e:
            logger.error(f"Gemini API error: {str(e)}")
            raise
    
    async def _call_openai(self, prompt: str) -> str:
        """
        Make API call to OpenAI (fallback)
        
        Args:
            prompt: Input prompt
            
        Returns:
            Response from OpenAI
        """
        try:
            if settings.OPENAI_API_KEY:
                response = openai.ChatCompletion.create(
                    model=settings.OPENAI_MODEL,
                    messages=[
                        {"role": "system", "content": "You are a helpful educational content generator."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=1000,
                    temperature=0.3
                )
                
                return response.choices[0].message.content.strip()
            else:
                raise Exception("OpenAI API key not configured")
            
        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
            raise

    def _needs_image(self, subtopic: str, content: str) -> bool:
        """Heuristic: generate image for diagrams/processes/structures/geometry etc."""
        text = f"{subtopic} {content}".lower()
        keywords = [
            "diagram", "flow", "process", "cycle", "structure", "anatomy", "map",
            "timeline", "geometry", "graph", "chart", "circuit", "network", "ecosystem",
            "cell", "molecule", "atom", "vector", "force", "free body", "ellipse", "triangle"
        ]
        return any(k in text for k in keywords)

    def _build_image_prompt(self, topic: str, subtopic: str, content: str) -> str:
        return (
            f"Create a clean educational line diagram with labels for the subtopic '{subtopic}' "
            f"under the chapter '{topic}'. White background, high contrast, minimal colors, vector-like, "
            f"suitable for textbooks. Include only essential elements. Content summary to base the diagram on: {content[:400]}"
        )

    async def generate_educational_content_excel(self, text: str, topic: str = None) -> Dict[str, Any]:
        """
        Generate educational content and create Excel file
        
        Args:
            text: OCR extracted text
            topic: Topic or subject area (optional)
            
        Returns:
            Dictionary containing Excel file information
        """
        try:
            # First generate the educational content
            content_result = await self.generate_educational_content(text, topic)
            
            if not content_result['success']:
                return {
                    'success': False,
                    'error': content_result.get('error', 'Content generation failed')
                }
            
            # Create Excel file
            excel_result = await self._create_excel_file_from_content(
                content_result['content_items'],
                topic or content_result.get('topic', 'Educational Content')
            )
            
            return {
                'success': True,
                'filename': excel_result['filename'],
                'file_url': excel_result['file_url'],
                'topic': topic or content_result.get('topic'),
                'total_items': len(content_result['content_items']),
                'generated_at': datetime.utcnow()
            }
            
        except Exception as e:
            logger.error(f"Excel generation error: {str(e)}")
            return {
                'success': False,
                'error': f"Excel generation failed: {str(e)}"
            }

    async def _create_excel_file_from_content(self, content_items: List[Dict[str, str]], topic: str) -> Dict[str, Any]:
        """
        Create Excel file from educational content items
        """
        try:
            import openpyxl
            from openpyxl.styles import Font, PatternFill, Alignment
            import os
            
            # Create workbook and worksheet
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Educational Content"
            
            # Set headers
            headers = ["Topic", "Subtopic", "Content", "Video Link"]
            for col, header in enumerate(headers, 1):
                cell = ws.cell(row=1, column=col, value=header)
                cell.font = Font(bold=True)
                cell.fill = PatternFill(start_color="CCCCCC", end_color="CCCCCC", fill_type="solid")
                cell.alignment = Alignment(horizontal="center")
            
            # Add content items
            for row, item in enumerate(content_items, 2):
                ws.cell(row=row, column=1, value=item.get('topic', topic))
                ws.cell(row=row, column=2, value=item.get('subtopic', ''))
                ws.cell(row=row, column=3, value=item.get('content', ''))
                ws.cell(row=row, column=4, value=item.get('video_link', ''))
            
            # Auto-adjust column widths
            for column in ws.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)  # Cap at 50 characters
                ws.column_dimensions[column_letter].width = adjusted_width
            
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"educational_content_{topic.replace(' ', '_')}_{timestamp}.xlsx"
            
            # Save file
            file_path = os.path.join(settings.UPLOAD_DIR, filename)
            wb.save(file_path)
            
            # Return file information
            return {
                'success': True,
                'filename': filename,
                'file_url': f"/api/v1/llm/download-excel/{filename}"
            }
            
        except Exception as e:
            logger.error(f"Excel file creation error: {str(e)}")
            raise

    async def generate_qna_excel(self, text: str, topic: str = None) -> Dict[str, Any]:
        """
        Generate Q&A pairs and create Excel file
        
        Args:
            text: OCR extracted text
            topic: Topic or subject area (optional)
            
        Returns:
            Dictionary containing Excel file information
        """
        try:
            # First generate the educational content to get subtopics
            content_result = await self.generate_educational_content(text, topic)
            
            if not content_result['success']:
                return {
                    'success': False,
                    'error': content_result.get('error', 'Content generation failed')
                }
            
            # Generate Q&A pairs for each content item
            qna_pairs = []
            for item in content_result['content_items']:
                qna_result = await self._generate_qna_for_content(
                    item['content'], 
                    item.get('topic', topic or 'Educational Content'),
                    item.get('subtopic', 'Main Content')
                )
                qna_pairs.extend(qna_result)
            
            # Create Excel file
            excel_result = await self._create_qna_excel_file(
                qna_pairs,
                topic or content_result.get('topic', 'Educational Content')
            )
            
            return {
                'success': True,
                'filename': excel_result['filename'],
                'file_url': excel_result['file_url'],
                'topic': topic or content_result.get('topic'),
                'total_questions': len(qna_pairs),
                'generated_at': datetime.utcnow()
            }
            
        except Exception as e:
            logger.error(f"Q&A Excel generation error: {str(e)}")
            return {
                'success': False,
                'error': f"Q&A Excel generation failed: {str(e)}"
            }

    async def _generate_qna_for_content(self, content: str, topic: str, subtopic: str) -> List[Dict[str, str]]:
        """
        Generate Q&A pairs for a specific content item
        """
        try:
            # Limit content length for faster processing
            max_content_length = 1000
            processed_content = content[:max_content_length]
            
            # Create Q&A generation prompt
            qna_prompt = f"""
            Generate 3-5 educational question-answer pairs based on this content.
            
            Topic: {topic}
            Subtopic: {subtopic}
            Content: {processed_content}
            
            Return JSON format:
            {{
                "qa_pairs": [
                    {{
                        "question": "Question 1",
                        "answer": "Answer 1"
                    }},
                    {{
                        "question": "Question 2", 
                        "answer": "Answer 2"
                    }}
                ]
            }}
            
            Guidelines:
            - Create clear, educational questions
            - Provide comprehensive, accurate answers
            - Focus on key concepts and important information
            - Make questions specific to the content
            - Keep answers informative but concise (2-3 sentences)
            - Generate 3-5 Q&A pairs maximum
            """
            
            # Generate Q&A pairs
            try:
                if self.gemini_model and self._check_gemini_rate_limit():
                    qna_response = await asyncio.wait_for(
                        self._call_gemini(qna_prompt), 
                        timeout=60.0
                    )
                    self._increment_gemini_calls()
                else:
                    qna_response = await asyncio.wait_for(
                        self._call_openai(qna_prompt), 
                        timeout=60.0
                    )
            except Exception as e:
                logger.error(f"Q&A generation failed: {str(e)}")
                # Fallback: create basic Q&A pairs
                return [{
                    'topic': topic,
                    'subtopic': subtopic,
                    'question': f"What is the main concept discussed in {subtopic}?",
                    'answer': processed_content[:200] + "..." if len(processed_content) > 200 else processed_content
                }]
            
            # Parse Q&A response
            try:
                cleaned_response = qna_response.strip()
                if cleaned_response.startswith('```json'):
                    cleaned_response = cleaned_response[7:]
                if cleaned_response.endswith('```'):
                    cleaned_response = cleaned_response[:-3]
                cleaned_response = cleaned_response.strip()
                
                qna_data = json.loads(cleaned_response)
                qa_pairs = qna_data.get('qa_pairs', [])
                
                # Format Q&A pairs with topic and subtopic
                formatted_pairs = []
                for pair in qa_pairs:
                    formatted_pairs.append({
                        'topic': topic,
                        'subtopic': subtopic,
                        'question': pair.get('question', ''),
                        'answer': pair.get('answer', '')
                    })
                
                return formatted_pairs
                
            except json.JSONDecodeError:
                logger.error("Failed to parse Q&A JSON response")
                # Fallback: create basic Q&A pairs
                return [{
                    'topic': topic,
                    'subtopic': subtopic,
                    'question': f"What is the main concept discussed in {subtopic}?",
                    'answer': processed_content[:200] + "..." if len(processed_content) > 200 else processed_content
                }]
                
        except Exception as e:
            logger.error(f"Q&A generation error: {str(e)}")
            return [{
                'topic': topic,
                'subtopic': subtopic,
                'question': f"What is the main concept discussed in {subtopic}?",
                'answer': content[:200] + "..." if len(content) > 200 else content
            }]

    async def _create_qna_excel_file(self, qna_pairs: List[Dict[str, str]], topic: str) -> Dict[str, Any]:
        """
        Create Excel file from Q&A pairs
        """
        try:
            import openpyxl
            from openpyxl.styles import Font, PatternFill, Alignment
            import os
            
            # Create workbook and worksheet
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Q&A Content"
            
            # Set headers
            headers = ["Topic", "Sub-Topic", "Question", "Answer"]
            for col, header in enumerate(headers, 1):
                cell = ws.cell(row=1, column=col, value=header)
                cell.font = Font(bold=True)
                cell.fill = PatternFill(start_color="CCCCCC", end_color="CCCCCC", fill_type="solid")
                cell.alignment = Alignment(horizontal="center")
            
            # Add Q&A pairs
            for row, pair in enumerate(qna_pairs, 2):
                ws.cell(row=row, column=1, value=pair.get('topic', topic))
                ws.cell(row=row, column=2, value=pair.get('subtopic', ''))
                ws.cell(row=row, column=3, value=pair.get('question', ''))
                ws.cell(row=row, column=4, value=pair.get('answer', ''))
            
            # Auto-adjust column widths
            for column in ws.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 60)  # Cap at 60 characters for Q&A
                ws.column_dimensions[column_letter].width = adjusted_width
            
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"qa_content_{topic.replace(' ', '_')}_{timestamp}.xlsx"
            
            # Save file
            file_path = os.path.join(settings.UPLOAD_DIR, filename)
            wb.save(file_path)
            
            # Return file information
            return {
                'success': True,
                'filename': filename,
                'file_url': f"/api/v1/llm/download-qna-excel/{filename}"
            }
            
        except Exception as e:
            logger.error(f"Q&A Excel file creation error: {str(e)}")
            raise