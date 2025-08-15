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
                main_chapter = structure_data.get('main_chapter', topic or 'General Content')
                subtopics = structure_data.get('subtopics', [])
                
                # Ensure we have subtopics
                if not subtopics or len(subtopics) < 3:
                    subtopics = await self._generate_quick_subtopics(processed_text, main_chapter)
                    
            except Exception as e:
                logger.warning(f"Structure parsing failed: {str(e)}")
                main_chapter = topic or 'General Content'
                subtopics = await self._generate_quick_subtopics(processed_text, main_chapter)
            
            # Generate content for each subtopic with timeout
            content_items = []
            
            for i, subtopic in enumerate(subtopics):
                # Skip if we already have enough content items
                if len(content_items) >= 6:
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
                    
                    content_items.append({
                        'topic': main_chapter,
                        'subtopic': subtopic,
                        'content': content_response.strip()
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