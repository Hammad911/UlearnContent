from fastapi import APIRouter, HTTPException
from typing import List, Optional
from datetime import datetime

from app.services.llm_service import LLMService
from app.models.llm_models import (
    ContentGenerationRequest, ContentGenerationResponse
)

router = APIRouter()
llm_service = LLMService()

@router.post("/generate-content", response_model=ContentGenerationResponse)
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
            topic=request.topic
        )
        
        return ContentGenerationResponse(
            success=content_result['success'],
            original_text=content_result['original_text'],
            content_items=content_result.get('content_items', []),
            topic=content_result.get('topic'),
            processed_at=content_result.get('processed_at', datetime.utcnow()),
            processing_time=content_result.get('processing_time', 0.0),
            total_items=content_result.get('total_items', 0),
            error=content_result.get('error')
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Content generation failed: {str(e)}") 