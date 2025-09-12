from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class QuizQuestionRequest(BaseModel):
    """Request model for quiz question generation"""
    topic: str = Field(..., description="Topic name (will remain constant in Excel)")
    chapter: str = Field(..., description="Chapter name")
    content: str = Field(..., description="Educational content to generate questions from")
    num_questions: int = Field(default=10, description="Number of questions to generate")
    language: str = Field(default="urdu", description="Language for questions (urdu/english)")

class QuizQuestion(BaseModel):
    """Model for a single quiz question"""
    chapter: str = Field(..., description="Chapter name")
    topic: str = Field(..., description="Topic name (constant)")
    question: str = Field(..., description="Question text")
    option_1: str = Field(..., description="Option 1")
    option_2: str = Field(..., description="Option 2")
    option_3: str = Field(..., description="Option 3")
    option_4: str = Field(..., description="Option 4")
    explanation: str = Field(..., description="Explanation for correct answer")
    correct_option: int = Field(..., description="Correct option number (1-4)")

class QuizGenerationResponse(BaseModel):
    """Response model for quiz generation"""
    success: bool = Field(..., description="Whether quiz generation was successful")
    topic: str = Field(..., description="Topic name")
    chapter: str = Field(..., description="Chapter name")
    questions: List[QuizQuestion] = Field(..., description="Generated questions")
    total_questions: int = Field(..., description="Total number of questions generated")
    generated_at: datetime = Field(..., description="Timestamp when quiz was generated")
    processing_time: float = Field(..., description="Time taken for processing in seconds")
    error: Optional[str] = Field(None, description="Error message if generation failed")

class ExcelQuizRequest(BaseModel):
    """Request model for generating Excel file with quiz content"""
    topic: str = Field(..., description="Topic name (constant throughout Excel)")
    chapter: str = Field(..., description="Chapter name")
    content: str = Field(..., description="Educational content")
    num_questions: int = Field(default=10, description="Number of questions")
    filename: Optional[str] = Field(None, description="Custom filename for Excel")
    language: str = Field(default="urdu", description="Language for questions")

class ExcelQuizResponse(BaseModel):
    """Response model for Excel quiz generation"""
    success: bool = Field(..., description="Whether Excel generation was successful")
    filename: str = Field(..., description="Generated Excel filename")
    file_url: str = Field(..., description="Download URL for Excel file")
    topic: str = Field(..., description="Topic name")
    chapter: str = Field(..., description="Chapter name")
    total_questions: int = Field(..., description="Total questions in Excel")
    generated_at: datetime = Field(..., description="Timestamp when Excel was generated")
    error: Optional[str] = Field(None, description="Error message if generation failed")
