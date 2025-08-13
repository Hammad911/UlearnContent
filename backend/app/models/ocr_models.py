from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class OCRRequest(BaseModel):
    """Request model for OCR processing"""
    file_id: str = Field(..., description="Unique identifier for the uploaded file")
    language: Optional[str] = Field(default="eng", description="Language code for OCR processing")
    confidence_threshold: Optional[float] = Field(default=0.5, description="Minimum confidence threshold for text extraction")

class OCRResponse(BaseModel):
    """Response model for OCR processing"""
    success: bool = Field(..., description="Whether the OCR processing was successful")
    text: str = Field(..., description="Extracted text from the image")
    file_id: str = Field(..., description="Unique identifier for the processed file")
    original_filename: str = Field(..., description="Original filename of the uploaded image")
    processed_at: datetime = Field(..., description="Timestamp when processing was completed")
    confidence: Optional[float] = Field(None, description="Overall confidence score of the OCR extraction")
    language: Optional[str] = Field(None, description="Detected language of the text")
    error: Optional[str] = Field(None, description="Error message if processing failed")
    word_count: Optional[int] = Field(None, description="Number of words extracted")
    character_count: Optional[int] = Field(None, description="Number of characters extracted")

class OCRBatchRequest(BaseModel):
    """Request model for batch OCR processing"""
    files: list[str] = Field(..., description="List of file IDs to process")
    language: Optional[str] = Field(default="eng", description="Language code for OCR processing")
    confidence_threshold: Optional[float] = Field(default=0.5, description="Minimum confidence threshold for text extraction")

class OCRBatchResponse(BaseModel):
    """Response model for batch OCR processing"""
    results: list[OCRResponse] = Field(..., description="List of OCR results for each file")
    total_processed: int = Field(..., description="Total number of files processed")
    successful: int = Field(..., description="Number of successfully processed files")
    failed: int = Field(..., description="Number of failed processing attempts")
    processing_time: float = Field(..., description="Total processing time in seconds") 