from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import List
import os
import uuid
from datetime import datetime

from app.core.config import settings
from app.services.ocr_service import OCRService
from app.models.ocr_models import OCRResponse, OCRRequest

router = APIRouter()
ocr_service = OCRService()

@router.post("/extract", response_model=OCRResponse)
async def extract_text_from_image(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """
    Extract text from uploaded image using OCR
    """
    # Validate file type
    file_extension = os.path.splitext(file.filename)[1].lower()
    if file_extension not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type not allowed. Allowed types: {settings.ALLOWED_EXTENSIONS}"
        )
    
    # Validate file size
    if file.size and file.size > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: {settings.MAX_FILE_SIZE} bytes"
        )
    
    try:
        # Generate unique filename
        file_id = str(uuid.uuid4())
        file_extension = os.path.splitext(file.filename)[1]
        filename = f"{file_id}{file_extension}"
        file_path = os.path.join(settings.UPLOAD_DIR, filename)
        
        # Save uploaded file
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Extract text using OCR
        extracted_text = await ocr_service.extract_text(file_path)
        
        # Clean up file in background
        background_tasks.add_task(os.remove, file_path)
        
        return OCRResponse(
            success=True,
            text=extracted_text,
            file_id=file_id,
            original_filename=file.filename,
            processed_at=datetime.utcnow()
        )
        
    except Exception as e:
        # Clean up file if it exists
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"OCR processing failed: {str(e)}")

@router.post("/batch-extract", response_model=List[OCRResponse])
async def extract_text_from_multiple_images(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...)
):
    """
    Extract text from multiple uploaded images using OCR
    """
    if len(files) > 10:  # Limit batch size
        raise HTTPException(status_code=400, detail="Maximum 10 files allowed per batch")
    
    results = []
    
    for file in files:
        try:
            # Validate file type
            file_extension = os.path.splitext(file.filename)[1].lower()
            if file_extension not in settings.ALLOWED_EXTENSIONS:
                results.append(OCRResponse(
                    success=False,
                    text="",
                    file_id="",
                    original_filename=file.filename,
                    processed_at=datetime.utcnow(),
                    error=f"File type not allowed: {file_extension}"
                ))
                continue
            
            # Generate unique filename
            file_id = str(uuid.uuid4())
            file_extension = os.path.splitext(file.filename)[1]
            filename = f"{file_id}{file_extension}"
            file_path = os.path.join(settings.UPLOAD_DIR, filename)
            
            # Save uploaded file
            with open(file_path, "wb") as buffer:
                content = await file.read()
                buffer.write(content)
            
            # Extract text using OCR
            extracted_text = await ocr_service.extract_text(file_path)
            
            # Clean up file in background
            background_tasks.add_task(os.remove, file_path)
            
            results.append(OCRResponse(
                success=True,
                text=extracted_text,
                file_id=file_id,
                original_filename=file.filename,
                processed_at=datetime.utcnow()
            ))
            
        except Exception as e:
            # Clean up file if it exists
            if 'file_path' in locals() and os.path.exists(file_path):
                os.remove(file_path)
            results.append(OCRResponse(
                success=False,
                text="",
                file_id="",
                original_filename=file.filename,
                processed_at=datetime.utcnow(),
                error=str(e)
            ))
    
    return results 