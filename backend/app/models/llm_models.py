from pydantic import BaseModel, Field
from typing import Optional, Dict, List
from datetime import datetime

class ContentGenerationRequest(BaseModel):
    """Request model for educational content generation"""
    text: str = Field(..., description="OCR extracted text to generate content from")
    topic: Optional[str] = Field(default=None, description="Topic or subject area")

class ContentGenerationResponse(BaseModel):
    """Response model for educational content generation"""
    success: bool = Field(..., description="Whether the content generation was successful")
    original_text: str = Field(..., description="Original OCR extracted text")
    content_items: List[Dict[str, str]] = Field(..., description="Generated content items with topics and subtopics")
    topic: Optional[str] = Field(default=None, description="Topic or subject area")
    processed_at: datetime = Field(..., description="Timestamp when content generation was completed")
    processing_time: float = Field(..., description="Time taken for processing in seconds")
    total_items: int = Field(..., description="Total number of content items generated")
    error: Optional[str] = Field(None, description="Error message if generation failed")

class ContentExcelGenerationRequest(BaseModel):
    """Request model for generating Excel file from educational content"""
    text: str = Field(..., description="OCR extracted text to generate content from")
    topic: Optional[str] = Field(default=None, description="Topic or subject area")

class ContentExcelGenerationResponse(BaseModel):
    """Response model for Excel file generation from educational content"""
    success: bool = Field(..., description="Whether the Excel generation was successful")
    filename: str = Field(..., description="Generated Excel filename")
    file_url: str = Field(..., description="URL to download the Excel file")
    topic: Optional[str] = Field(default=None, description="Topic or subject area")
    total_items: int = Field(..., description="Total number of content items in Excel")
    generated_at: datetime = Field(..., description="Timestamp when Excel generation was completed")
    error: Optional[str] = Field(None, description="Error message if generation failed")

class QnAExcelGenerationRequest(BaseModel):
    """Request model for generating Q&A Excel file from educational content"""
    text: str = Field(..., description="OCR extracted text to generate Q&A from")
    topic: Optional[str] = Field(default=None, description="Topic or subject area")

class QnAExcelGenerationResponse(BaseModel):
    """Response model for Q&A Excel file generation"""
    success: bool = Field(..., description="Whether the Q&A Excel generation was successful")
    filename: str = Field(..., description="Generated Excel filename")
    file_url: str = Field(..., description="URL to download the Excel file")
    topic: Optional[str] = Field(default=None, description="Topic or subject area")
    total_questions: int = Field(..., description="Total number of Q&A pairs in Excel")
    generated_at: datetime = Field(..., description="Timestamp when Excel generation was completed")
    error: Optional[str] = Field(None, description="Error message if generation failed") 