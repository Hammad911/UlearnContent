from fastapi import APIRouter, HTTPException
from typing import List, Optional
from datetime import datetime

from app.services.llm_service import LLMService
from app.models.llm_models import (
    LLMRequest, LLMResponse, AnalysisRequest, AnalysisResponse,
    ContentGenerationRequest, ContentGenerationResponse
)

router = APIRouter()
llm_service = LLMService()

@router.post("/process", response_model=LLMResponse)
async def process_text_with_llm(request: LLMRequest):
    """
    Process extracted text through LLM for analysis and insights
    """
    try:
        if not request.text or request.text.strip() == "":
            raise HTTPException(status_code=400, detail="Text cannot be empty")
        
        # Process text through LLM
        processed_result = await llm_service.process_text(
            text=request.text,
            task_type=request.task_type,
            additional_context=request.additional_context
        )
        
        return LLMResponse(
            success=True,
            original_text=request.text,
            processed_result=processed_result,
            task_type=request.task_type,
            processed_at=datetime.utcnow()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM processing failed: {str(e)}")

@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_text(request: AnalysisRequest):
    """
    Perform comprehensive analysis of extracted text
    """
    try:
        if not request.text or request.text.strip() == "":
            raise HTTPException(status_code=400, detail="Text cannot be empty")
        
        # Perform analysis
        analysis_result = await llm_service.analyze_text(
            text=request.text,
            analysis_type=request.analysis_type,
            language=request.language
        )
        
        return AnalysisResponse(
            success=True,
            original_text=request.text,
            analysis_result=analysis_result,
            analysis_type=request.analysis_type,
            language=request.language,
            processed_at=datetime.utcnow()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Text analysis failed: {str(e)}")

@router.post("/summarize")
async def summarize_text(request: LLMRequest):
    """
    Generate a summary of the extracted text
    """
    try:
        if not request.text or request.text.strip() == "":
            raise HTTPException(status_code=400, detail="Text cannot be empty")
        
        # Generate summary
        summary = await llm_service.summarize_text(
            text=request.text,
            max_length=request.additional_context.get("max_length", 200) if request.additional_context else 200
        )
        
        return {
            "success": True,
            "original_text": request.text,
            "summary": summary,
            "processed_at": datetime.utcnow()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Text summarization failed: {str(e)}")

@router.post("/translate")
async def translate_text(request: LLMRequest):
    """
    Translate extracted text to specified language
    """
    try:
        if not request.text or request.text.strip() == "":
            raise HTTPException(status_code=400, detail="Text cannot be empty")
        
        target_language = request.additional_context.get("target_language", "English") if request.additional_context else "English"
        
        # Translate text
        translated_text = await llm_service.translate_text(
            text=request.text,
            target_language=target_language
        )
        
        return {
            "success": True,
            "original_text": request.text,
            "translated_text": translated_text,
            "target_language": target_language,
            "processed_at": datetime.utcnow()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Text translation failed: {str(e)}")

@router.post("/extract-entities")
async def extract_entities(request: LLMRequest):
    """
    Extract named entities from the text
    """
    try:
        if not request.text or request.text.strip() == "":
            raise HTTPException(status_code=400, detail="Text cannot be empty")
        
        # Extract entities
        entities = await llm_service.extract_entities(request.text)
        
        return {
            "success": True,
            "original_text": request.text,
            "entities": entities,
            "processed_at": datetime.utcnow()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Entity extraction failed: {str(e)}")

@router.post("/generate-content")
async def generate_educational_content(request: ContentGenerationRequest):
    """
    Generate educational content from OCR extracted text
    """
    try:
        if not request.text or request.text.strip() == "":
            raise HTTPException(status_code=400, detail="Text cannot be empty")
        
        # Generate educational content
        content_result = await llm_service.generate_educational_content(
            text=request.text,
            content_type=request.content_type,
            topic=request.topic,
            difficulty_level=request.difficulty_level,
            target_audience=request.target_audience
        )
        
        return ContentGenerationResponse(
            success=content_result['success'],
            original_text=content_result['original_text'],
            generated_content=content_result.get('generated_content', ''),
            content_type=content_result['content_type'],
            topic=content_result.get('topic'),
            difficulty_level=content_result.get('difficulty_level', 'intermediate'),
            target_audience=content_result.get('target_audience', 'students'),
            processed_at=content_result.get('processed_at', datetime.utcnow()),
            word_count=content_result.get('word_count', 0),
            key_concepts=content_result.get('key_concepts', [])
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Content generation failed: {str(e)}") 