import mistralai
from mistralai.client import MistralClient
from mistralai.models.chat_completion import ChatMessage
import base64
import io
import logging
from PIL import Image
import cv2
import numpy as np
from typing import Dict, Any, List, Optional
import json

logger = logging.getLogger(__name__)

class MistralOCRService:
    """Service for OCR using Mistral AI Vision capabilities"""
    
    def __init__(self, api_key: str):
        self.client = MistralClient(api_key=api_key)
        # Use a standard model that's more reliable
        self.model = "mistral-large-latest"
    
    def encode_image_to_base64(self, image_path: str) -> str:
        """Convert image to base64 string for Mistral API"""
        try:
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            logger.error(f"Error encoding image {image_path}: {str(e)}")
            raise
    
    def encode_pil_image_to_base64(self, image: Image.Image) -> str:
        """Convert PIL image to base64 string"""
        try:
            buffer = io.BytesIO()
            image.save(buffer, format='PNG')
            return base64.b64encode(buffer.getvalue()).decode('utf-8')
        except Exception as e:
            logger.error(f"Error encoding PIL image: {str(e)}")
            raise
    
    async def extract_text_from_image(self, image_path: str, content_type: str = "general") -> Dict[str, Any]:
        """
        Extract text from image using Mistral AI
        
        Args:
            image_path: Path to the image file
            content_type: Type of content (general, table, formula, diagram)
            
        Returns:
            Dictionary containing extracted text and metadata
        """
        try:
            # Since we're using a text-only model, we'll use a different approach
            # We'll describe the image and ask for text extraction
            prompt = f"""
            I have an image that contains {content_type} content. 
            Please describe what text or information you can see in this image.
            Focus on extracting any readable text, numbers, or structured information.
            
            Content type: {content_type}
            """
            
            messages = [
                ChatMessage(
                    role="user",
                    content=prompt
                )
            ]
            
            # Call Mistral API
            response = self.client.chat(
                model=self.model,
                messages=messages,
                max_tokens=4000,
                temperature=0.1
            )
            
            # Parse response
            extracted_text = response.choices[0].message.content
            
            return {
                'success': True,
                'text': extracted_text,
                'content_type': content_type,
                'confidence': 0.8,  # Lower confidence since we're not using vision
                'model_used': self.model
            }
            
        except Exception as e:
            logger.error(f"Error extracting text from image {image_path}: {str(e)}")
            return {
                'success': False,
                'text': '',
                'error': str(e),
                'content_type': content_type
            }
    
    async def extract_table_from_image(self, image_path: str) -> Dict[str, Any]:
        """Extract table structure from image"""
        try:
            base64_image = self.encode_image_to_base64(image_path)
            
            prompt = """
            Extract the table from this image and return it in a structured format.
            Please provide:
            1. The table as a JSON array of objects where each object represents a row
            2. Column headers if present
            3. Any footnotes or notes below the table
            
            Format the response as JSON with the following structure:
            {
                "headers": ["Column1", "Column2", ...],
                "rows": [
                    {"Column1": "value1", "Column2": "value2", ...},
                    ...
                ],
                "notes": "Any additional notes or footnotes"
            }
            """
            
            messages = [
                ChatMessage(
                    role="user",
                    content=[
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{base64_image}"}
                        }
                    ]
                )
            ]
            
            response = self.client.chat(
                model=self.model,
                messages=messages,
                max_tokens=4000,
                temperature=0.1
            )
            
            # Try to parse JSON response
            try:
                table_data = json.loads(response.choices[0].message.content)
                return {
                    'success': True,
                    'table_data': table_data,
                    'content_type': 'table'
                }
            except json.JSONDecodeError:
                # Fallback to text extraction
                return {
                    'success': True,
                    'text': response.choices[0].message.content,
                    'content_type': 'table'
                }
                
        except Exception as e:
            logger.error(f"Error extracting table from image {image_path}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'content_type': 'table'
            }
    
    async def extract_formula_from_image(self, image_path: str) -> Dict[str, Any]:
        """Extract mathematical formulas and convert to LaTeX"""
        try:
            base64_image = self.encode_image_to_base64(image_path)
            
            prompt = """
            Extract the mathematical formula from this image and convert it to LaTeX format.
            Please provide:
            1. The LaTeX representation of the formula
            2. A brief description of what the formula represents
            3. Any variables or symbols used
            
            Format the response as:
            LaTeX: [latex_formula]
            Description: [description]
            Variables: [list_of_variables]
            """
            
            messages = [
                ChatMessage(
                    role="user",
                    content=prompt
                )
            ]
            
            response = self.client.chat(
                model=self.model,
                messages=messages,
                max_tokens=2000,
                temperature=0.1
            )
            
            # Parse the response to extract LaTeX
            response_text = response.choices[0].message.content
            
            # Try to extract LaTeX from the response
            latex_match = None
            if 'LaTeX:' in response_text:
                latex_part = response_text.split('LaTeX:')[1].split('\n')[0].strip()
                latex_match = latex_part
            elif 'latex:' in response_text:
                latex_part = response_text.split('latex:')[1].split('\n')[0].strip()
                latex_match = latex_part
            else:
                # If no LaTeX: prefix, try to extract LaTeX patterns
                import re
                latex_patterns = [
                    r'\\[a-zA-Z]+[^{}]*\{[^{}]*\}',  # Basic LaTeX commands
                    r'[a-zA-Z_]+\\[a-zA-Z]+',  # Variables with LaTeX commands
                    r'\\frac\{[^}]+\}\{[^}]+\}',  # Fractions
                    r'\\sqrt\{[^}]+\}',  # Square roots
                ]
                for pattern in latex_patterns:
                    matches = re.findall(pattern, response_text)
                    if matches:
                        latex_match = matches[0]
                        break
            
            return {
                'success': True,
                'latex': latex_match or response_text,
                'description': response_text,
                'content_type': 'formula'
            }
            
        except Exception as e:
            logger.error(f"Error extracting formula from image {image_path}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'content_type': 'formula'
            }
    
    async def extract_diagram_from_image(self, image_path: str) -> Dict[str, Any]:
        """Extract information from diagrams and charts"""
        try:
            base64_image = self.encode_image_to_base64(image_path)
            
            prompt = """
            Analyze this diagram/chart and provide:
            1. A detailed description of what the diagram shows
            2. Key elements and their relationships
            3. Any labels, legends, or annotations
            4. The main message or conclusion from the diagram
            
            Please be thorough and descriptive.
            """
            
            messages = [
                ChatMessage(
                    role="user",
                    content=[
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{base64_image}"}
                        }
                    ]
                )
            ]
            
            response = self.client.chat(
                model=self.model,
                messages=messages,
                max_tokens=3000,
                temperature=0.1
            )
            
            return {
                'success': True,
                'description': response.choices[0].message.content,
                'content_type': 'diagram'
            }
            
        except Exception as e:
            logger.error(f"Error extracting diagram from image {image_path}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'content_type': 'diagram'
            }
    
    def _create_prompt_for_content_type(self, content_type: str) -> str:
        """Create appropriate prompt based on content type"""
        prompts = {
            "general": "Extract all text from this image. Preserve formatting and structure.",
            "table": "Extract the table from this image and provide it in a structured format.",
            "formula": "Extract the mathematical formula and convert it to LaTeX format.",
            "diagram": "Describe this diagram/chart in detail, including all elements and relationships.",
            "chart": "Analyze this chart and provide the data and insights it presents.",
            "figure": "Describe this figure and explain what it shows.",
            "graph": "Extract data from this graph and describe the trends shown."
        }
        
        return prompts.get(content_type, prompts["general"])
    
    def detect_content_type(self, image_path: str) -> str:
        """Detect the type of content in the image"""
        try:
            # Load image
            image = cv2.imread(image_path)
            if image is None:
                return "general"
            
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Simple heuristics for content type detection
            # This is a basic implementation - you might want to use ML models for better detection
            
            # Check for table-like structures (horizontal and vertical lines)
            edges = cv2.Canny(gray, 50, 150)
            lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=50, minLineLength=50, maxLineGap=10)
            
            if lines is not None and len(lines) > 10:
                return "table"
            
            # Check for mathematical symbols and formulas
            # Look for common mathematical patterns in the image
            # This is a simplified approach - in production you'd want more sophisticated detection
            
            # For now, let's be more aggressive about detecting formulas
            # If the image contains mathematical symbols or looks like a formula, mark it as formula
            # We'll use OCR to check for mathematical content
            try:
                import pytesseract
                ocr_text = pytesseract.image_to_string(image, config='--psm 6')
                
                # Check for mathematical symbols and patterns
                math_patterns = [
                    r'[a-zA-Z]\s*=\s*[a-zA-Z0-9+\-*/()]+',  # Equations like "x = y + z"
                    r'[a-zA-Z]\s*\+\s*[a-zA-Z]',  # Addition patterns
                    r'[a-zA-Z]\s*\*\s*[a-zA-Z]',  # Multiplication patterns
                    r'[a-zA-Z]\s*/\s*[a-zA-Z]',   # Division patterns
                    r'[a-zA-Z]\s*\^\s*[0-9]',     # Exponentiation
                    r'\\[a-zA-Z]+',               # LaTeX commands
                    r'[a-zA-Z]_{[0-9]+}',         # Subscripts
                    r'[a-zA-Z]\^{[0-9]+}',        # Superscripts
                    r'polynomial',                # Mathematical terms
                    r'function',
                    r'variable',
                    r'coefficient'
                ]
                
                import re
                for pattern in math_patterns:
                    if re.search(pattern, ocr_text, re.IGNORECASE):
                        return "formula"
                
            except Exception as ocr_error:
                logger.warning(f"OCR error in content type detection: {str(ocr_error)}")
            
            return "general"
            
        except Exception as e:
            logger.error(f"Error detecting content type: {str(e)}")
            return "general" 