import asyncio
import time
import logging
import json
import re
from typing import Dict, Any, List, Optional
from datetime import datetime
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter
import os

from app.services.llm_service import LLMService
from app.core.config import settings

logger = logging.getLogger(__name__)

class QuizService:
    """Service for generating quiz questions from OCR extracted text"""
    
    def __init__(self):
        self.llm_service = LLMService()
    
    async def generate_quiz_from_text(
        self, 
        text: str, 
        chapter: str,  # This is the chapter name (topic in Excel)
        topic: str = "",  # This will be deduced from content
        num_questions: int = 10,
        language: str = "urdu"
    ) -> Dict[str, Any]:
        """
        Generate quiz questions from OCR extracted text
        
        Args:
            text: OCR extracted text
            topic: Topic name (constant throughout Excel)
            chapter: Chapter name
            num_questions: Number of questions to generate (max 10)
            language: Language for questions (urdu/english)
            
        Returns:
            Dictionary containing generated quiz questions
        """
        try:
            start_time = time.time()
            
            # Limit text length for faster processing
            max_text_length = 3000
            processed_text = text[:max_text_length]
            
            # Limit questions to max 10
            num_questions = min(num_questions, 10)
            
            # First, detect subtopic from content if not provided
            if not topic:
                topic = await self._detect_subtopic_from_content(processed_text, language)
            
            # Create quiz generation prompt
            quiz_prompt = self._create_quiz_prompt(
                processed_text, chapter, topic, num_questions, language
            )
            
            # Generate quiz questions
            try:
                if self.llm_service.gemini_model and self.llm_service._check_gemini_rate_limit():
                    quiz_response = await asyncio.wait_for(
                        self.llm_service._call_gemini(quiz_prompt), 
                        timeout=60.0
                    )
                    self.llm_service._increment_gemini_calls()
                else:
                    quiz_response = await asyncio.wait_for(
                        self.llm_service._call_openai(quiz_prompt), 
                        timeout=60.0
                    )
            except Exception as e:
                logger.error(f"Quiz generation failed: {str(e)}")
                raise
            
            # Parse quiz questions
            questions = self._parse_quiz_response(quiz_response, topic, chapter)
            
            # Ensure we have the requested number of questions
            if len(questions) < num_questions:
                # Generate additional questions if needed
                additional_questions = await self._generate_additional_questions(
                    processed_text, topic, chapter, num_questions - len(questions), language
                )
                questions.extend(additional_questions)
            
            # Limit to requested number
            questions = questions[:num_questions]
            
            processing_time = time.time() - start_time
            
            return {
                'success': True,
                'topic': topic,
                'chapter': chapter,
                'questions': questions,
                'total_questions': len(questions),
                'generated_at': datetime.now(),
                'processing_time': processing_time,
                'original_text': text
            }
            
        except Exception as e:
            logger.error(f"Error generating quiz: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'topic': topic,
                'chapter': chapter,
                'questions': []
            }
    
    def _create_quiz_prompt(
        self, 
        text: str, 
        chapter: str,  # Chapter name (topic in Excel)
        topic: str,    # Subtopic (deduced from content)
        num_questions: int,
        language: str
    ) -> str:
        """Create prompt for quiz generation"""
        
        if language.lower() == "urdu":
            prompt = f"""
            آپ کو اس متن سے {num_questions} سوالات بنانے ہیں۔ ہر سوال کے 4 آپشن ہوں گے۔ صرف صحیح جواب کے شروع میں "Y*" لگائیں۔

            متن: {text}
            باب: {chapter}
            سب ٹاپک: {topic}

            فارمیٹ:
            {{
                "questions": [
                    {{
                        "question": "سوال کا متن",
                        "option_1": "پہلا آپشن",
                        "option_2": "Y*دوسرا آپشن (صحیح جواب)",
                        "option_3": "تیسرا آپشن",
                        "option_4": "چوتھا آپشن",
                        "explanation": "صحیح جواب کی وضاحت"
                    }}
                ]
            }}

            ہدایات:
            - صرف صحیح جواب کے شروع میں "Y*" لگائیں
            - سوالات متن سے متعلق ہوں
            - آپشنز واضح اور مختلف ہوں
            - وضاحت مختصر اور واضح ہو
            """
        else:
            prompt = f"""
            Generate {num_questions} multiple choice questions from this text. Each question should have 4 options. Only mark the correct answer with "Y*" at the beginning.

            Text: {text}
            Chapter: {chapter}
            Subtopic: {topic}

            Format:
            {{
                "questions": [
                    {{
                        "question": "Question text",
                        "option_1": "First option",
                        "option_2": "Y*Second option (correct answer)",
                        "option_3": "Third option",
                        "option_4": "Fourth option",
                        "explanation": "Explanation for correct answer"
                    }}
                ]
            }}

            Guidelines:
            - Only mark correct answer with "Y*" at the beginning
            - Questions should be relevant to the text
            - Options should be clear and distinct
            - Explanation should be brief and clear
            """
        
        return prompt
    
    async def _detect_subtopic_from_content(self, text: str, language: str) -> str:
        """Detect subtopic from content using AI"""
        try:
            if language.lower() == "urdu":
                prompt = f"""
                اس متن سے سب ٹاپک کا نام تلاش کریں۔
                
                متن: {text[:1000]}
                
                ممکنہ سب ٹاپکس:
                - خلاصہ
                - تشریح
                - تعریف اور طریقہ استعمال
                - تفصیل
                - وضاحت
                
                صرف سب ٹاپک کا نام واپس کریں، کوئی اضافی متن نہیں۔
                """
            else:
                prompt = f"""
                Find the subtopic name from this text.
                
                Text: {text[:1000]}
                
                Possible subtopics:
                - Summary
                - Explanation
                - Definition and Usage
                - Details
                - Description
                
                Return only the subtopic name, no additional text.
                """
            
            # Use LLM to detect subtopic
            if self.llm_service.gemini_model and self.llm_service._check_gemini_rate_limit():
                try:
                    response = await asyncio.wait_for(
                        self.llm_service._call_gemini(prompt), 
                        timeout=30.0
                    )
                    self.llm_service._increment_gemini_calls()
                except Exception as gemini_error:
                    if "429" in str(gemini_error) or "quota" in str(gemini_error).lower():
                        logger.warning("Gemini rate limit hit in subtopic detection, falling back to OpenAI")
                        if hasattr(self.llm_service, 'settings') and hasattr(self.llm_service.settings, 'OPENAI_API_KEY'):
                            response = await asyncio.wait_for(
                                self.llm_service._call_openai(prompt), 
                                timeout=30.0
                            )
                        else:
                            raise gemini_error
                    else:
                        raise gemini_error
            else:
                response = await asyncio.wait_for(
                    self.llm_service._call_openai(prompt), 
                    timeout=30.0
                )
            
            # Clean response
            subtopic = response.strip()
            if subtopic.startswith('"') and subtopic.endswith('"'):
                subtopic = subtopic[1:-1]
            
            # Validate subtopic
            valid_subtopics = {
                'urdu': ['خلاصہ', 'تشریح', 'تعریف اور طریقہ استعمال', 'تفصیل', 'وضاحت'],
                'english': ['Summary', 'Explanation', 'Definition and Usage', 'Details', 'Description']
            }
            
            lang_key = 'urdu' if language.lower() == 'urdu' else 'english'
            if subtopic in valid_subtopics[lang_key]:
                return subtopic
            else:
                # Return default subtopic
                return valid_subtopics[lang_key][0]  # First option as default
                
        except Exception as e:
            logger.warning(f"Failed to detect subtopic: {str(e)}")
            # Return default subtopic based on language
            if language.lower() == "urdu":
                return "خلاصہ"
            else:
                return "Summary"
    
    def _parse_quiz_response(self, response: str, topic: str, chapter: str) -> List[Dict[str, Any]]:
        """Parse quiz response from LLM"""
        questions = []
        
        try:
            # Clean response
            cleaned_response = response.strip()
            if cleaned_response.startswith('```json'):
                cleaned_response = cleaned_response[7:]
            if cleaned_response.endswith('```'):
                cleaned_response = cleaned_response[:-3]
            cleaned_response = cleaned_response.strip()
            
            # Parse JSON
            data = json.loads(cleaned_response)
            
            if 'questions' in data and isinstance(data['questions'], list):
                for q in data['questions']:
                    if isinstance(q, dict):
                        # Extract correct option (marked with Y*)
                        correct_option = 1
                        options = []
                        
                        for i in range(1, 5):
                            option_key = f'option_{i}'
                            if option_key in q:
                                option_text = q[option_key]
                                if option_text.startswith('Y*'):
                                    correct_option = i
                                    option_text = option_text[2:]  # Remove Y*
                                options.append(option_text)
                        
                        # Ensure we have 4 options
                        while len(options) < 4:
                            options.append(f"Option {len(options) + 1}")
                        
                        question_data = {
                            'chapter': chapter,
                            'topic': topic,
                            'question': q.get('question', ''),
                            'option_1': options[0] if len(options) > 0 else '',
                            'option_2': options[1] if len(options) > 1 else '',
                            'option_3': options[2] if len(options) > 2 else '',
                            'option_4': options[3] if len(options) > 3 else '',
                            'explanation': q.get('explanation', ''),
                            'correct_option': correct_option
                        }
                        
                        questions.append(question_data)
            
        except Exception as e:
            logger.warning(f"Failed to parse quiz response: {str(e)}")
            # Create fallback questions
            questions = self._create_fallback_questions(topic, chapter)
        
        return questions
    
    def _create_fallback_questions(self, topic: str, chapter: str) -> List[Dict[str, Any]]:
        """Create fallback questions if parsing fails"""
        return [
            {
                'chapter': chapter,
                'topic': topic,
                'question': f'سوال 1: {topic} کے بارے میں',
                'option_1': 'Y*صحیح جواب',
                'option_2': 'غلط جواب',
                'option_3': 'غلط جواب',
                'option_4': 'غلط جواب',
                'explanation': 'یہ صحیح جواب ہے',
                'correct_option': 1
            }
        ]
    
    async def _generate_additional_questions(
        self, 
        text: str, 
        topic: str, 
        chapter: str, 
        num_additional: int,
        language: str
    ) -> List[Dict[str, Any]]:
        """Generate additional questions if needed"""
        try:
            additional_prompt = self._create_quiz_prompt(text, topic, chapter, num_additional, language)
            
            if self.llm_service.gemini_model and self.llm_service._check_gemini_rate_limit():
                response = await asyncio.wait_for(
                    self.llm_service._call_gemini(additional_prompt), 
                    timeout=30.0
                )
                self.llm_service._increment_gemini_calls()
            else:
                response = await asyncio.wait_for(
                    self.llm_service._call_openai(additional_prompt), 
                    timeout=30.0
                )
            
            return self._parse_quiz_response(response, topic, chapter)
            
        except Exception as e:
            logger.warning(f"Failed to generate additional questions: {str(e)}")
            return []
    
    async def generate_excel_file(
        self, 
        questions: List[Dict[str, Any]], 
        topic: str, 
        chapter: str,
        filename: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate Excel file with quiz questions
        
        Args:
            questions: List of quiz questions
            topic: Topic name
            chapter: Chapter name
            filename: Custom filename (optional)
            
        Returns:
            Dictionary containing file information
        """
        try:
            # Create filename
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"quiz_{topic}_{chapter}_{timestamp}.xlsx"
            
            # Ensure uploads directory exists
            os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
            file_path = os.path.join(settings.UPLOAD_DIR, filename)
            
            # Create Excel workbook
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Quiz Questions"
            
            # Define styles
            header_font = Font(bold=True, color="FFFFFF")
            header_fill = PatternFill(start_color="FF0000", end_color="FF0000", fill_type="solid")
            header_alignment = Alignment(horizontal="center", vertical="center")
            
            # Set column headers
            headers = ["Chapter", "Topic", "Question", "Option 1", "Option 2", "Option 3", "Option 4", "Explanation"]
            for col, header in enumerate(headers, 1):
                cell = ws.cell(row=1, column=col, value=header)
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = header_alignment
            
            # Add questions
            for row, question in enumerate(questions, 2):
                # Mark correct option with Y*
                options = [
                    question['option_1'],
                    question['option_2'],
                    question['option_3'],
                    question['option_4']
                ]
                
                # Add Y* to correct option
                correct_idx = question['correct_option'] - 1
                options[correct_idx] = f"Y*{options[correct_idx]}"
                
                # Write row data
                ws.cell(row=row, column=1, value=question['chapter'])
                ws.cell(row=row, column=2, value=question['topic'])
                ws.cell(row=row, column=3, value=question['question'])
                ws.cell(row=row, column=4, value=options[0])
                ws.cell(row=row, column=5, value=options[1])
                ws.cell(row=row, column=6, value=options[2])
                ws.cell(row=row, column=7, value=options[3])
                ws.cell(row=row, column=8, value=question['explanation'])
            
            # Auto-adjust column widths
            for column in ws.columns:
                max_length = 0
                column_letter = get_column_letter(column[0].column)
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                ws.column_dimensions[column_letter].width = adjusted_width
            
            # Save file
            wb.save(file_path)
            
            return {
                'success': True,
                'filename': filename,
                'file_path': file_path,
                'file_url': f"/api/v1/quiz/download/{filename}",
                'topic': topic,
                'chapter': chapter,
                'total_questions': len(questions),
                'generated_at': datetime.now()
            }
            
        except Exception as e:
            logger.error(f"Error generating Excel file: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'filename': filename or 'unknown'
            }
