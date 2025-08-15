import openai
import asyncio
import time
from typing import Dict, Any, List, Optional
import logging
import json
import google.generativeai as genai
from datetime import datetime
import requests

from app.core.config import settings

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
    
    async def generate_educational_content(self, text: str, topic: str = None) -> Dict[str, Any]:
        """
        Generate educational content from OCR extracted text - improved version
        
        Args:
            text: OCR extracted text
            topic: Topic or subject area (optional)
            
        Returns:
            Dictionary containing generated content and metadata
        """
        try:
            start_time = time.time()
            
            # Convert formulas to MathJax using MathPix if available
            processed_text = await self._convert_formulas_with_mathpix(text)
            
            # First, analyze the text to identify chapter structure
            analysis_prompt = f"""
            Analyze this educational text and identify the main chapter/topic structure.
            
            Text: {processed_text[:2000]}  # Limit for analysis
            
            Return a JSON object with:
            {{
                "main_chapter": "Chapter name or main topic",
                "subtopics": ["Subtopic 1", "Subtopic 2", "Subtopic 3"],
                "content_type": "textbook|curriculum|lesson|other"
            }}
            
            Look for:
            - Chapter titles, headings, or main topics
            - Natural divisions in the content
            - Educational structure patterns
            """
            
            # Get structure analysis
            if self.gemini_model:
                structure_response = await self._call_gemini(analysis_prompt)
            else:
                structure_response = await self._call_openai(analysis_prompt)
            
            # Parse structure
            try:
                cleaned_structure = structure_response.strip()
                if cleaned_structure.startswith('```json'):
                    cleaned_structure = cleaned_structure[7:]
                if cleaned_structure.endswith('```'):
                    cleaned_structure = cleaned_structure[:-3]
                cleaned_structure = cleaned_structure.strip()
                
                structure_data = json.loads(cleaned_structure)
                main_chapter = structure_data.get('main_chapter', topic or 'General Content')
                subtopics = structure_data.get('subtopics', ['Main Content'])
                content_type = structure_data.get('content_type', 'textbook')
            except:
                main_chapter = topic or 'General Content'
                subtopics = ['Main Content']
                content_type = 'textbook'
            
            # Generate content for each subtopic
            content_items = []
            
            for subtopic in subtopics:
                content_prompt = f"""
                Generate educational content for the subtopic "{subtopic}" based on this text.
                
                Chapter: {main_chapter}
                Subtopic: {subtopic}
                Content Type: {content_type}
                
                Original Text: {processed_text}
                
                Create educational content that:
                1. Explains the concepts clearly and concisely
                2. Provides examples or applications where appropriate
                3. Uses proper educational language
                4. Maintains mathematical formulas in LaTeX format
                5. Is suitable for students
                
                Return the content as a well-structured educational explanation.
                """
                
                if self.gemini_model:
                    content_response = await self._call_gemini(content_prompt)
                else:
                    content_response = await self._call_openai(content_prompt)
                
                content_items.append({
                    'topic': main_chapter,
                    'subtopic': subtopic,
                    'content': content_response.strip()
                })
            
            # If no subtopics were found, create a single comprehensive content item
            if len(content_items) == 0 or (len(content_items) == 1 and content_items[0]['subtopic'] == 'Main Content'):
                comprehensive_prompt = f"""
                Create comprehensive educational content from this text.
                
                Chapter: {main_chapter}
                Text: {processed_text}
                
                Generate educational content that:
                1. Explains the main concepts clearly
                2. Breaks down complex ideas into understandable parts
                3. Provides relevant examples
                4. Uses proper educational structure
                5. Maintains mathematical formulas in LaTeX format
                
                Return well-structured educational content.
                """
                
                if self.gemini_model:
                    comprehensive_response = await self._call_gemini(comprehensive_prompt)
                else:
                    comprehensive_response = await self._call_openai(comprehensive_prompt)
                
                content_items = [{
                    'topic': main_chapter,
                    'subtopic': 'Comprehensive Content',
                    'content': comprehensive_response.strip()
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
            import re
            
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