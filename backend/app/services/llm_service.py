import openai
import asyncio
import time
from typing import Dict, Any, List, Optional
import logging
import json
import google.generativeai as genai
from datetime import datetime

from app.core.config import settings

logger = logging.getLogger(__name__)

class LLMService:
    """Service for LLM text processing and analysis"""
    
    def __init__(self):
        # Configure OpenAI client
        if settings.OPENAI_API_KEY:
            openai.api_key = settings.OPENAI_API_KEY
        else:
            logger.warning("OpenAI API key not configured")
        
        # Configure Gemini client
        if settings.GEMINI_API_KEY:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            # Use the model from settings
            self.gemini_model = genai.GenerativeModel(settings.GEMINI_MODEL)
        else:
            self.gemini_model = None
            logger.warning("Gemini API key not configured")
    
    async def process_text(self, text: str, task_type: str, additional_context: Optional[Dict[str, Any]] = None) -> str:
        """
        Process text through LLM based on task type
        
        Args:
            text: Text to process
            task_type: Type of processing task
            additional_context: Additional context or parameters
            
        Returns:
            Processed result from LLM
        """
        start_time = time.time()
        
        try:
            # Create prompt based on task type
            prompt = self._create_prompt(text, task_type, additional_context)
            
            # Try Gemini first, fallback to OpenAI
            try:
                if self.gemini_model:
                    response = await self._call_gemini(prompt, task_type)
                elif settings.OPENAI_API_KEY:
                    response = await self._call_openai(prompt, task_type)
                else:
                    raise ValueError("No LLM API keys configured (Gemini or OpenAI)")
            except Exception as llm_error:
                # Fallback to OpenAI if Gemini fails
                if settings.OPENAI_API_KEY and self.gemini_model:
                    logger.warning(f"Gemini failed, falling back to OpenAI: {str(llm_error)}")
                    response = await self._call_openai(prompt, task_type)
                else:
                    raise llm_error
            
            processing_time = time.time() - start_time
            logger.info(f"LLM processing completed in {processing_time:.2f}s for task: {task_type}")
            
            return response
            
        except Exception as e:
            logger.error(f"Error in LLM processing: {str(e)}")
            raise
    
    async def analyze_text(self, text: str, analysis_type: str, language: str = "en") -> Dict[str, Any]:
        """
        Perform comprehensive text analysis
        
        Args:
            text: Text to analyze
            analysis_type: Type of analysis
            language: Language of the text
            
        Returns:
            Analysis results
        """
        try:
            if analysis_type == "sentiment":
                return await self._analyze_sentiment(text, language)
            elif analysis_type == "entities":
                return await self._extract_entities(text)
            elif analysis_type == "topics":
                return await self._extract_topics(text)
            elif analysis_type == "summary":
                return await self._generate_summary(text)
            else:
                raise ValueError(f"Unsupported analysis type: {analysis_type}")
                
        except Exception as e:
            logger.error(f"Error in text analysis: {str(e)}")
            raise
    
    async def summarize_text(self, text: str, max_length: int = 200) -> str:
        """
        Generate a summary of the text
        
        Args:
            text: Text to summarize
            max_length: Maximum length of summary
            
        Returns:
            Generated summary
        """
        prompt = f"""
        Please provide a concise summary of the following text in approximately {max_length} characters:
        
        {text}
        
        Summary:
        """
        
        return await self._call_openai(prompt, "summarize")
    
    async def translate_text(self, text: str, target_language: str) -> str:
        """
        Translate text to target language
        
        Args:
            text: Text to translate
            target_language: Target language
            
        Returns:
            Translated text
        """
        prompt = f"""
        Translate the following text to {target_language}:
        
        {text}
        
        Translation:
        """
        
        return await self._call_openai(prompt, "translate")
    
    async def extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract named entities from text
        
        Args:
            text: Text to extract entities from
            
        Returns:
            List of extracted entities
        """
        prompt = f"""
        Extract named entities from the following text. Return the result as a JSON array with objects containing:
        - entity: the entity name
        - type: the entity type (PERSON, ORGANIZATION, LOCATION, DATE, etc.)
        - confidence: confidence score (0-1)
        
        Text: {text}
        
        JSON result:
        """
        
        response = await self._call_openai(prompt, "extract_entities")
        
        try:
            # Try to parse JSON response
            entities = json.loads(response)
            return entities if isinstance(entities, list) else []
        except json.JSONDecodeError:
            # Fallback: return simple entity list
            return [{"entity": response.strip(), "type": "UNKNOWN", "confidence": 0.8}]
    
    def _create_prompt(self, text: str, task_type: str, additional_context: Optional[Dict[str, Any]] = None) -> str:
        """
        Create appropriate prompt based on task type
        
        Args:
            text: Input text
            task_type: Type of task
            additional_context: Additional context
            
        Returns:
            Formatted prompt
        """
        base_prompt = f"Task: {task_type}\n\nText: {text}\n\n"
        
        if task_type == "summarize":
            max_length = additional_context.get("max_length", 200) if additional_context else 200
            return f"{base_prompt}Please provide a concise summary in approximately {max_length} characters."
        
        elif task_type == "analyze":
            analysis_type = additional_context.get("analysis_type", "general") if additional_context else "general"
            return f"{base_prompt}Please provide a {analysis_type} analysis of this text."
        
        elif task_type == "translate":
            target_lang = additional_context.get("target_language", "English") if additional_context else "English"
            return f"{base_prompt}Please translate this text to {target_lang}."
        
        elif task_type == "extract_entities":
            return f"{base_prompt}Please extract named entities (people, organizations, locations, dates) from this text."
        
        else:
            return f"{base_prompt}Please process this text according to the task: {task_type}"
    
    async def _call_gemini(self, prompt: str, task_type: str) -> str:
        """
        Make API call to Gemini for content generation
        
        Args:
            prompt: Input prompt
            task_type: Type of task for logging
            
        Returns:
            Response from Gemini
        """
        try:
            if self.gemini_model:
                # Run the synchronous Gemini call in a thread pool
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(None, self.gemini_model.generate_content, prompt)
                return response.text.strip()
            else:
                raise Exception("Gemini API key not configured")
            
        except Exception as e:
            logger.error(f"Gemini API error for task {task_type}: {str(e)}")
            raise
    
    async def _call_openai(self, prompt: str, task_type: str) -> str:
        """
        Make API call to OpenAI (fallback)
        
        Args:
            prompt: Input prompt
            task_type: Type of task for logging
            
        Returns:
            Response from OpenAI
        """
        try:
            if settings.OPENAI_API_KEY:
                response = openai.ChatCompletion.create(
                    model=settings.OPENAI_MODEL,
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant that processes text according to specific tasks."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=1000,
                    temperature=0.3
                )
                
                return response.choices[0].message.content.strip()
            else:
                raise Exception("OpenAI API key not configured")
            
        except Exception as e:
            logger.error(f"OpenAI API error for task {task_type}: {str(e)}")
            raise
    
    async def _analyze_sentiment(self, text: str, language: str) -> Dict[str, Any]:
        """
        Analyze sentiment of text
        
        Args:
            text: Text to analyze
            language: Language of text
            
        Returns:
            Sentiment analysis results
        """
        prompt = f"""
        Analyze the sentiment of the following text in {language}. Return the result as JSON with:
        - sentiment: overall sentiment (positive, negative, neutral)
        - confidence: confidence score (0-1)
        - emotions: list of detected emotions
        - intensity: sentiment intensity (low, medium, high)
        
        Text: {text}
        
        JSON result:
        """
        
        response = await self._call_gemini(prompt, "sentiment_analysis")
        
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {
                "sentiment": "neutral",
                "confidence": 0.5,
                "emotions": [],
                "intensity": "medium"
            }
    
    async def _extract_topics(self, text: str) -> Dict[str, Any]:
        """
        Extract main topics from text
        
        Args:
            text: Text to analyze
            
        Returns:
            Topic extraction results
        """
        prompt = f"""
        Extract the main topics from the following text. Return the result as JSON with:
        - topics: list of main topics
        - keywords: list of important keywords
        - theme: overall theme of the text
        
        Text: {text}
        
        JSON result:
        """
        
        response = await self._call_gemini(prompt, "topic_extraction")
        
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {
                "topics": [],
                "keywords": [],
                "theme": "general"
            }
    
    async def _generate_summary(self, text: str) -> Dict[str, Any]:
        """
        Generate comprehensive summary
        
        Args:
            text: Text to summarize
            
        Returns:
            Summary results
        """
        summary = await self.summarize_text(text)
        
        return {
            "summary": summary,
            "original_length": len(text),
            "summary_length": len(summary),
            "compression_ratio": len(summary) / len(text) if text else 0
        }
    
    async def generate_educational_content(self, text: str, content_type: str = "educational", topic: str = None, difficulty_level: str = "intermediate", target_audience: str = "students") -> Dict[str, Any]:
        """
        Generate educational content from OCR extracted text
        
        Args:
            text: OCR extracted text
            content_type: Type of content to generate (educational, summary, explanation, quiz)
            topic: Topic or subject area
            difficulty_level: Difficulty level (beginner, intermediate, advanced)
            target_audience: Target audience (students, teachers, professionals)
            
        Returns:
            Dictionary containing generated content and metadata
        """
        try:
            start_time = time.time()
            
            # Create appropriate prompt based on content type
            if content_type == "educational":
                prompt = f"""
                Generate comprehensive educational content based on the following OCR-extracted text.
                
                Topic: {topic or "General"}
                Difficulty Level: {difficulty_level}
                Target Audience: {target_audience}
                
                Please create:
                1. A clear explanation of the concepts
                2. Key points and definitions
                3. Examples or applications
                4. Learning objectives
                5. Key concepts to remember
                
                OCR Text: {text}
                
                Generate educational content that is engaging, accurate, and appropriate for the specified audience and difficulty level.
                """
            elif content_type == "summary":
                prompt = f"""
                Create a comprehensive summary of the following OCR-extracted text.
                
                Difficulty Level: {difficulty_level}
                Target Audience: {target_audience}
                
                Please include:
                1. Main points and key concepts
                2. Important details and examples
                3. Clear structure and organization
                
                OCR Text: {text}
                
                Generate a summary that captures the essential information in a clear, organized manner.
                """
            elif content_type == "explanation":
                prompt = f"""
                Provide a detailed explanation of the concepts found in the following OCR-extracted text.
                
                Topic: {topic or "General"}
                Difficulty Level: {difficulty_level}
                Target Audience: {target_audience}
                
                Please include:
                1. Step-by-step explanations
                2. Definitions of key terms
                3. Context and background information
                4. Practical applications
                
                OCR Text: {text}
                
                Generate explanations that are clear, thorough, and appropriate for the specified audience.
                """
            elif content_type == "quiz":
                prompt = f"""
                Create a quiz based on the following OCR-extracted text.
                
                Topic: {topic or "General"}
                Difficulty Level: {difficulty_level}
                Target Audience: {target_audience}
                
                Please include:
                1. Multiple choice questions
                2. True/False questions
                3. Short answer questions
                4. Answer key with explanations
                
                OCR Text: {text}
                
                Generate quiz questions that test understanding of the key concepts and are appropriate for the specified difficulty level.
                """
            else:
                prompt = f"""
                Generate educational content based on the following OCR-extracted text.
                
                Content Type: {content_type}
                Topic: {topic or "General"}
                Difficulty Level: {difficulty_level}
                Target Audience: {target_audience}
                
                OCR Text: {text}
                
                Generate content that is educational, engaging, and appropriate for the specified parameters.
                """
            
            response = await self._call_gemini(prompt, "content_generation")
            
            processing_time = time.time() - start_time
            
            # Extract key concepts
            key_concepts_prompt = f"""
            Extract the key concepts from the following generated content. Return as a JSON array of strings.
            
            Content: {response}
            
            JSON result:
            """
            
            try:
                key_concepts_response = await self._call_gemini(key_concepts_prompt, "key_concepts_extraction")
                key_concepts = json.loads(key_concepts_response) if key_concepts_response.startswith('[') else []
            except:
                key_concepts = []
            
            return {
                'success': True,
                'original_text': text,
                'generated_content': response,
                'content_type': content_type,
                'topic': topic,
                'difficulty_level': difficulty_level,
                'target_audience': target_audience,
                'processed_at': datetime.now(),
                'word_count': len(response.split()),
                'key_concepts': key_concepts,
                'processing_time': processing_time,
                'model_used': 'gemini-2.5-flash'
            }
            
        except Exception as e:
            logger.error(f"Error generating educational content: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'original_text': text,
                'content_type': content_type
            }
    
    async def generate_structured_content(self, text: str, topic: str = None, difficulty_level: str = "intermediate", target_audience: str = "students") -> List[Dict[str, str]]:
        """
        Generate structured content broken down into subtopics
        
        Args:
            text: OCR extracted text
            topic: Main topic or chapter title
            difficulty_level: Difficulty level (beginner, intermediate, advanced)
            target_audience: Target audience (students, teachers, professionals)
            
        Returns:
            List of dictionaries containing structured content with subtopics
        """
        try:
            start_time = time.time()
            
            prompt = f"""
            Analyze the following text and break it down into structured educational content.
            
            Topic: {topic or "General Content"}
            Difficulty Level: {difficulty_level}
            Target Audience: {target_audience}
            
            Please identify the main subtopics and create separate content entries for each subtopic.
            Return the result as a JSON array with the following structure:
            
            [
                {{
                    "topic": "Main Topic Name",
                    "subtopic": "Subtopic 1 Name",
                    "content": "Detailed content for subtopic 1",
                    "video_link": ""
                }},
                {{
                    "topic": "Main Topic Name", 
                    "subtopic": "Subtopic 2 Name",
                    "content": "Detailed content for subtopic 2",
                    "video_link": ""
                }}
            ]
            
            CRITICAL REQUIREMENTS FOR MATHEMATICAL FORMULAS:
            - All mathematical formulas MUST be written in proper LaTeX format
            - Use LaTeX syntax for all mathematical expressions
            - Examples of correct LaTeX:
              * Polynomial: P(z) = a_n z^n + a_{{n-1}} z^{{n-1}} + \\cdots + a_1 z + a_0
              * Fractions: \\frac{{a}}{{b}}
              * Square roots: \\sqrt{{x}}
              * Subscripts: a_n, a_{{n-1}}
              * Superscripts: z^n, z^{{n-1}}
              * Greek letters: \\alpha, \\beta, \\gamma
              * Summation: \\sum_{{i=1}}^{{n}} x_i
              * Integrals: \\int_{{a}}^{{b}} f(x) dx
            
            Guidelines:
            1. Keep the main topic name consistent across all entries
            2. Identify natural subtopics in the content
            3. Each subtopic should have focused, specific content
            4. Content should be educational and well-structured
            5. Avoid putting all content in one cell
            6. Make sure each subtopic has meaningful, separate content
            7. ALL mathematical expressions must use proper LaTeX syntax
            
            Text to analyze: {text}
            
            JSON result:
            """
            
            response = await self._call_gemini(prompt, "structured_content_generation")
            
            processing_time = time.time() - start_time
            
            # Try to parse JSON response with better error handling
            try:
                # Clean the response - remove any markdown formatting
                cleaned_response = response.strip()
                if cleaned_response.startswith('```json'):
                    cleaned_response = cleaned_response[7:]
                if cleaned_response.endswith('```'):
                    cleaned_response = cleaned_response[:-3]
                cleaned_response = cleaned_response.strip()
                
                logger.info(f"Cleaned response: {cleaned_response[:200]}...")
                
                structured_content = json.loads(cleaned_response)
                if isinstance(structured_content, list):
                    logger.info(f"Successfully generated {len(structured_content)} structured content items")
                    
                    # Convert mathematical formulas in content to MathJax format
                    for item in structured_content:
                        if 'content' in item:
                            item['content'] = self._convert_formulas_to_mathjax(item['content'])
                    
                    return structured_content
                else:
                    logger.warning("LLM response is not a list, creating fallback structure")
                    return [{
                        'topic': topic or 'General Content',
                        'subtopic': 'Main Content',
                        'content': self._convert_formulas_to_mathjax(response),
                        'video_link': ''
                    }]
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse JSON response: {str(e)}")
                logger.warning(f"Raw response: {response[:500]}...")
                
                # Try to extract JSON from the response if it's embedded in text
                try:
                    # Look for JSON array in the response
                    start_idx = response.find('[')
                    end_idx = response.rfind(']')
                    if start_idx != -1 and end_idx != -1:
                        json_part = response[start_idx:end_idx+1]
                        structured_content = json.loads(json_part)
                        if isinstance(structured_content, list):
                            logger.info(f"Successfully extracted JSON and generated {len(structured_content)} structured content items")
                            return structured_content
                except:
                    pass
                
                # Final fallback - create basic structure
                return [{
                    'topic': topic or 'General Content',
                    'subtopic': 'Main Content',
                    'content': response,
                    'video_link': ''
                }]
            
        except Exception as e:
            logger.error(f"Error generating structured content: {str(e)}")
            # Return basic fallback content
            return [{
                'topic': topic or 'General Content',
                'subtopic': 'Main Content',
                'content': text[:500] + "..." if len(text) > 500 else text,
                'video_link': ''
            }]
    
    def _convert_formulas_to_mathjax(self, content: str) -> str:
        """
        Convert mathematical formulas in text content to MathJax format
        
        Args:
            content: Text content that may contain mathematical formulas
            
        Returns:
            Content with formulas converted to MathJax format
        """
        import re
        
        # Patterns to match mathematical formulas
        formula_patterns = [
            # Pattern for LaTeX formulas that are already properly formatted
            (r'(\\[a-zA-Z]+{[^}]*})', r'$$\1$$'),
            
            # Pattern for polynomial formulas like P(z) = a_n z^n + a_{n-1} z^{n-1} + ... + a_1 z + a_0
            (r'([A-Z]\([a-z]\)\s*=\s*[a-zA-Z0-9_{}\^+\-*/()\s\.\\]+)', r'$$\1$$'),
            
            # Pattern for equations with variables and subscripts
            (r'([a-zA-Z]_{[a-zA-Z0-9+\-]+}\s*[+\-*/=]\s*[a-zA-Z0-9_{}\^+\-*/()\s\.\\]+)', r'$$\1$$'),
            
            # Pattern for LaTeX commands
            (r'(\\[a-zA-Z]+)', r'$$\1$$'),
            
            # Pattern for simple equations like x = y + z
            (r'([a-zA-Z]\s*=\s*[a-zA-Z0-9+\-*/()\s\\]+)', r'$$\1$$'),
            
            # Pattern for fractions
            (r'([a-zA-Z0-9]+\s*/\s*[a-zA-Z0-9]+)', r'$$\1$$'),
            
            # Pattern for square roots
            (r'(√[a-zA-Z0-9+\-*/()\s]+)', r'$$\1$$'),
            
            # Pattern for exponents
            (r'([a-zA-Z]\^[0-9]+)', r'$$\1$$'),
        ]
        
        # Apply each pattern
        for pattern, replacement in formula_patterns:
            content = re.sub(pattern, replacement, content)
        
        # Also look for specific mathematical terms and wrap them
        math_terms = [
            'polynomial', 'function', 'equation', 'formula', 'coefficient',
            'variable', 'exponent', 'root', 'derivative', 'integral'
        ]
        
        for term in math_terms:
            # Look for patterns like "P(z) = ..." and wrap them
            pattern = rf'({term[0].upper()}\([a-z]\)\s*=\s*[^.!?]+)'
            content = re.sub(pattern, r'$$\1$$', content, flags=re.IGNORECASE)
        
        return content 