from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class PDFRequest(BaseModel):
    """Request model for PDF processing"""
    file_id: str = Field(..., description="Unique identifier for the uploaded PDF file")
    include_images: bool = Field(default=True, description="Whether to extract text from images")
    extract_structure: bool = Field(default=True, description="Whether to extract chapter/section structure")

class PDFResponse(BaseModel):
    """Response model for PDF processing"""
    success: bool = Field(..., description="Whether the PDF processing was successful")
    file_id: str = Field(..., description="Unique identifier for the processed file")
    original_filename: str = Field(..., description="Original filename of the uploaded PDF")
    text: str = Field(..., description="Extracted text from the PDF")
    structure: Dict[str, Any] = Field(..., description="Extracted chapter and section structure")
    pages: List[Dict[str, Any]] = Field(..., description="Information about each page")
    image_count: int = Field(..., description="Number of images found in the PDF")
    total_pages: int = Field(..., description="Total number of pages in the PDF")
    processed_at: datetime = Field(..., description="Timestamp when processing was completed")
    error: Optional[str] = Field(None, description="Error message if processing failed")

class ExcelRequest(BaseModel):
    """Request model for Excel generation"""
    pdf_text: str = Field(..., description="Extracted text from PDF")
    structure: Dict[str, Any] = Field(..., description="PDF structure information")
    include_metadata: bool = Field(default=True, description="Whether to include metadata sheet")
    format_type: str = Field(default="advanced", description="Excel format type (basic/advanced)")

class ExcelResponse(BaseModel):
    """Response model for Excel generation"""
    success: bool = Field(..., description="Whether the Excel generation was successful")
    file_id: str = Field(..., description="Unique identifier for the generated Excel file")
    filename: str = Field(..., description="Generated Excel filename")
    total_items: int = Field(..., description="Total number of content items in Excel")
    processed_at: datetime = Field(..., description="Timestamp when processing was completed")
    error: Optional[str] = Field(None, description="Error message if generation failed")

class ContentItem(BaseModel):
    """Model for individual content items in Excel"""
    topic: str = Field(..., description="Main topic or chapter name")
    subtopic: str = Field(..., description="Subtopic or section name")
    content: str = Field(..., description="Content description or summary")
    video_link: Optional[str] = Field(None, description="Optional video link")

class PDFAnalysisRequest(BaseModel):
    """Request model for PDF content analysis"""
    file_id: str = Field(..., description="Unique identifier for the uploaded PDF file")
    analysis_type: str = Field(default="educational", description="Type of analysis to perform")
    include_summary: bool = Field(default=True, description="Whether to include content summary")

class PDFAnalysisResponse(BaseModel):
    """Response model for PDF content analysis"""
    success: bool = Field(..., description="Whether the analysis was successful")
    file_id: str = Field(..., description="Unique identifier for the analyzed file")
    original_filename: str = Field(..., description="Original filename of the PDF")
    analysis: str = Field(..., description="Analysis results from LLM")
    structure: Dict[str, Any] = Field(..., description="Extracted structure information")
    stats: Dict[str, Any] = Field(..., description="Statistics about the PDF")
    processed_at: datetime = Field(..., description="Timestamp when analysis was completed")
    error: Optional[str] = Field(None, description="Error message if analysis failed")

class ChapterInfo(BaseModel):
    """Model for chapter information"""
    number: str = Field(..., description="Chapter number")
    title: str = Field(..., description="Chapter title")
    line: int = Field(..., description="Line number in the text")

class SectionInfo(BaseModel):
    """Model for section information"""
    number: str = Field(..., description="Section number")
    title: str = Field(..., description="Section title")
    line: int = Field(..., description="Line number in the text")

class PageInfo(BaseModel):
    """Model for page information"""
    page: int = Field(..., description="Page number")
    text_length: int = Field(..., description="Length of text on the page")
    has_images: bool = Field(..., description="Whether the page contains images")
    error: Optional[str] = Field(None, description="Error message if page processing failed")

class PDFStructure(BaseModel):
    """Model for PDF structure information"""
    chapters: List[ChapterInfo] = Field(default_factory=list, description="List of chapters")
    sections: List[SectionInfo] = Field(default_factory=list, description="List of sections")

class PDFStats(BaseModel):
    """Model for PDF statistics"""
    total_pages: int = Field(..., description="Total number of pages")
    image_count: int = Field(..., description="Number of images")
    text_length: int = Field(..., description="Total text length")
    chapters: int = Field(..., description="Number of chapters")
    sections: int = Field(..., description="Number of sections") 