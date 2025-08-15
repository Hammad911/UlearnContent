from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
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