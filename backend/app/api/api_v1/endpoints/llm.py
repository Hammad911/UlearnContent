from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from datetime import datetime
import os

from app.services.llm_service import LLMService
from app.models.llm_models import (
    ContentGenerationRequest, ContentGenerationResponse,
    ContentExcelGenerationRequest, ContentExcelGenerationResponse,
    QnAExcelGenerationRequest, QnAExcelGenerationResponse
)
from app.core.config import settings

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

@router.post("/generate-content-excel", response_model=ContentExcelGenerationResponse)
async def generate_educational_content_excel(request: ContentExcelGenerationRequest):
    """
    Generate educational content and create Excel file from OCR extracted text
    """
    try:
        if not request.text or request.text.strip() == "":
            raise HTTPException(status_code=400, detail="Text cannot be empty")
        
        # Generate educational content and Excel file
        result = await llm_service.generate_educational_content_excel(
            text=request.text,
            topic=request.topic
        )
        
        if not result['success']:
            raise HTTPException(status_code=500, detail=f"Excel generation failed: {result.get('error', 'Unknown error')}")
        
        return ContentExcelGenerationResponse(
            success=True,
            filename=result['filename'],
            file_url=result['file_url'],
            topic=result['topic'],
            total_items=result['total_items'],
            generated_at=result['generated_at']
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Excel generation failed: {str(e)}")

@router.get("/download-excel/{filename}")
async def download_excel_file(filename: str):
    """
    Download generated Excel file
    """
    try:
        file_path = os.path.join(settings.UPLOAD_DIR, filename)
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")
        
        return FileResponse(
            path=file_path,
            filename=filename,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File download failed: {str(e)}")

@router.post("/generate-qna-excel", response_model=QnAExcelGenerationResponse)
async def generate_qna_excel(request: QnAExcelGenerationRequest):
    """
    Generate Q&A pairs and create Excel file from OCR extracted text
    """
    try:
        if not request.text or request.text.strip() == "":
            raise HTTPException(status_code=400, detail="Text cannot be empty")
        
        # Generate Q&A pairs and Excel file
        result = await llm_service.generate_qna_excel(
            text=request.text,
            topic=request.topic
        )
        
        if not result['success']:
            raise HTTPException(status_code=500, detail=f"Q&A Excel generation failed: {result.get('error', 'Unknown error')}")
        
        return QnAExcelGenerationResponse(
            success=True,
            filename=result['filename'],
            file_url=result['file_url'],
            topic=result['topic'],
            total_questions=result['total_questions'],
            generated_at=result['generated_at']
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Q&A Excel generation failed: {str(e)}")

@router.get("/download-qna-excel/{filename}")
async def download_qna_excel_file(filename: str):
    """
    Download generated Q&A Excel file
    """
    try:
        file_path = os.path.join(settings.UPLOAD_DIR, filename)
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")
        
        return FileResponse(
            path=file_path,
            filename=filename,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File download failed: {str(e)}") 