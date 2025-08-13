from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime

class LLMRequest(BaseModel):
    """Request model for LLM processing"""
    text: str = Field(..., description="Text to be processed by the LLM")
    task_type: str = Field(..., description="Type of task to perform (e.g., 'summarize', 'analyze', 'translate')")
    additional_context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context or parameters for the task")

class LLMResponse(BaseModel):
    """Response model for LLM processing"""
    success: bool = Field(..., description="Whether the LLM processing was successful")
    original_text: str = Field(..., description="Original text that was processed")
    processed_result: str = Field(..., description="Result from LLM processing")
    task_type: str = Field(..., description="Type of task that was performed")
    processed_at: datetime = Field(..., description="Timestamp when processing was completed")
    model_used: Optional[str] = Field(None, description="LLM model that was used for processing")
    processing_time: Optional[float] = Field(None, description="Time taken for processing in seconds")
    error: Optional[str] = Field(None, description="Error message if processing failed")

class AnalysisRequest(BaseModel):
    """Request model for text analysis"""
    text: str = Field(..., description="Text to be analyzed")
    analysis_type: str = Field(..., description="Type of analysis to perform (e.g., 'sentiment', 'entities', 'topics')")
    language: Optional[str] = Field(default="en", description="Language of the text")

class AnalysisResponse(BaseModel):
    """Response model for text analysis"""
    success: bool = Field(..., description="Whether the analysis was successful")
    original_text: str = Field(..., description="Original text that was analyzed")
    analysis_result: Dict[str, Any] = Field(..., description="Results of the analysis")
    analysis_type: str = Field(..., description="Type of analysis that was performed")
    language: str = Field(..., description="Language of the analyzed text")
    processed_at: datetime = Field(..., description="Timestamp when analysis was completed")
    confidence_scores: Optional[Dict[str, float]] = Field(None, description="Confidence scores for different aspects of the analysis")

class TranslationRequest(BaseModel):
    """Request model for text translation"""
    text: str = Field(..., description="Text to be translated")
    source_language: Optional[str] = Field(default="auto", description="Source language (auto-detect if not specified)")
    target_language: str = Field(..., description="Target language for translation")

class TranslationResponse(BaseModel):
    """Response model for text translation"""
    success: bool = Field(..., description="Whether the translation was successful")
    original_text: str = Field(..., description="Original text that was translated")
    translated_text: str = Field(..., description="Translated text")
    source_language: str = Field(..., description="Detected source language")
    target_language: str = Field(..., description="Target language")
    processed_at: datetime = Field(..., description="Timestamp when translation was completed")
    confidence: Optional[float] = Field(None, description="Confidence score of the translation")

class EntityExtractionRequest(BaseModel):
    """Request model for entity extraction"""
    text: str = Field(..., description="Text to extract entities from")
    entity_types: Optional[List[str]] = Field(default=None, description="Types of entities to extract (e.g., ['PERSON', 'ORG', 'LOC'])")

class EntityExtractionResponse(BaseModel):
    """Response model for entity extraction"""
    success: bool = Field(..., description="Whether the entity extraction was successful")
    original_text: str = Field(..., description="Original text that was processed")
    entities: List[Dict[str, Any]] = Field(..., description="Extracted entities with their details")
    processed_at: datetime = Field(..., description="Timestamp when extraction was completed")
    total_entities: int = Field(..., description="Total number of entities extracted")

class SummarizationRequest(BaseModel):
    """Request model for text summarization"""
    text: str = Field(..., description="Text to be summarized")
    max_length: Optional[int] = Field(default=200, description="Maximum length of the summary")
    summary_type: Optional[str] = Field(default="extractive", description="Type of summarization (extractive or abstractive)")

class SummarizationResponse(BaseModel):
    """Response model for text summarization"""
    success: bool = Field(..., description="Whether the summarization was successful")
    original_text: str = Field(..., description="Original text that was summarized")
    summary: str = Field(..., description="Generated summary")
    summary_length: int = Field(..., description="Length of the generated summary")
    compression_ratio: float = Field(..., description="Ratio of summary length to original text length")
    processed_at: datetime = Field(..., description="Timestamp when summarization was completed")

class ContentGenerationRequest(BaseModel):
    """Request model for educational content generation"""
    text: str = Field(..., description="OCR extracted text to generate content from")
    content_type: str = Field(default="educational", description="Type of content to generate (educational, summary, explanation, quiz)")
    topic: Optional[str] = Field(default=None, description="Topic or subject area")
    difficulty_level: Optional[str] = Field(default="intermediate", description="Difficulty level (beginner, intermediate, advanced)")
    target_audience: Optional[str] = Field(default="students", description="Target audience (students, teachers, professionals)")

class ContentGenerationResponse(BaseModel):
    """Response model for educational content generation"""
    success: bool = Field(..., description="Whether the content generation was successful")
    original_text: str = Field(..., description="Original OCR extracted text")
    generated_content: str = Field(..., description="Generated educational content")
    content_type: str = Field(..., description="Type of content that was generated")
    topic: Optional[str] = Field(default=None, description="Topic or subject area")
    difficulty_level: str = Field(..., description="Difficulty level of the generated content")
    target_audience: str = Field(..., description="Target audience for the content")
    processed_at: datetime = Field(..., description="Timestamp when content generation was completed")
    word_count: int = Field(..., description="Number of words in the generated content")
    key_concepts: Optional[List[str]] = Field(default=None, description="Key concepts identified in the content") 