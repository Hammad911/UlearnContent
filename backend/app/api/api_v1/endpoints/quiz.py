from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from typing import Optional
import os

from app.services.quiz_service import QuizService
from app.models.quiz_models import (
    QuizQuestionRequest, QuizGenerationResponse,
    ExcelQuizRequest, ExcelQuizResponse
)
from app.core.config import settings

router = APIRouter()
quiz_service = QuizService()

@router.post("/generate-quiz", response_model=QuizGenerationResponse)
async def generate_quiz_from_text(request: QuizQuestionRequest):
    """
    Generate quiz questions from OCR extracted text
    """
    try:
        if not request.content or request.content.strip() == "":
            raise HTTPException(status_code=400, detail="Content cannot be empty")
        
        if not request.topic or request.topic.strip() == "":
            raise HTTPException(status_code=400, detail="Topic cannot be empty")
        
        if not request.chapter or request.chapter.strip() == "":
            raise HTTPException(status_code=400, detail="Chapter cannot be empty")
        
        # Generate quiz questions
        result = await quiz_service.generate_quiz_from_text(
            text=request.content,
            chapter=request.chapter,  # Chapter name (topic in Excel)
            topic=request.topic,      # Subtopic (will be deduced if empty)
            num_questions=request.num_questions,
            language=request.language
        )
        
        if not result['success']:
            raise HTTPException(status_code=500, detail=f"Quiz generation failed: {result.get('error', 'Unknown error')}")
        
        return QuizGenerationResponse(
            success=True,
            topic=result['topic'],
            chapter=result['chapter'],
            questions=result['questions'],
            total_questions=result['total_questions'],
            generated_at=result['generated_at'],
            processing_time=result['processing_time']
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Quiz generation failed: {str(e)}")

@router.post("/generate-excel", response_model=ExcelQuizResponse)
async def generate_excel_quiz(request: ExcelQuizRequest):
    """
    Generate Excel file with quiz questions from OCR extracted text
    """
    try:
        if not request.content or request.content.strip() == "":
            raise HTTPException(status_code=400, detail="Content cannot be empty")
        
        if not request.topic or request.topic.strip() == "":
            raise HTTPException(status_code=400, detail="Topic cannot be empty")
        
        if not request.chapter or request.chapter.strip() == "":
            raise HTTPException(status_code=400, detail="Chapter cannot be empty")
        
        # Generate quiz questions first
        quiz_result = await quiz_service.generate_quiz_from_text(
            text=request.content,
            chapter=request.chapter,  # Chapter name (topic in Excel)
            topic=request.topic,      # Subtopic (will be deduced if empty)
            num_questions=request.num_questions,
            language=request.language
        )
        
        if not quiz_result['success']:
            raise HTTPException(status_code=500, detail=f"Quiz generation failed: {quiz_result.get('error', 'Unknown error')}")
        
        # Generate Excel file
        excel_result = await quiz_service.generate_excel_file(
            questions=quiz_result['questions'],
            topic=request.topic,
            chapter=request.chapter,
            filename=request.filename
        )
        
        if not excel_result['success']:
            raise HTTPException(status_code=500, detail=f"Excel generation failed: {excel_result.get('error', 'Unknown error')}")
        
        return ExcelQuizResponse(
            success=True,
            filename=excel_result['filename'],
            file_url=excel_result['file_url'],
            topic=request.topic,
            chapter=request.chapter,
            total_questions=excel_result['total_questions'],
            generated_at=excel_result['generated_at']
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Excel generation failed: {str(e)}")

@router.get("/download/{filename}")
async def download_quiz_file(filename: str):
    """
    Download generated quiz Excel file
    """
    try:
        file_path = os.path.join(settings.UPLOAD_DIR, filename)
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")
        
        return FileResponse(
            path=file_path,
            filename=filename,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File download failed: {str(e)}")

@router.post("/generate-quiz-from-ocr")
async def generate_quiz_from_ocr_file(
    file: UploadFile = File(...),
    topic: str = Form(...),
    chapter: str = Form(...),
    num_questions: int = Form(default=10),
    language: str = Form(default="urdu")
):
    """
    Generate quiz from uploaded OCR file (image/PDF)
    """
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file uploaded")
        
        # Save uploaded file temporarily
        temp_file_path = os.path.join(settings.UPLOAD_DIR, f"temp_{file.filename}")
        with open(temp_file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        try:
            # Extract text using OCR (you can integrate with your existing OCR service)
            # For now, we'll use a placeholder
            extracted_text = f"Extracted text from {file.filename}. This is a placeholder for OCR text."
            
            # Generate quiz
            result = await quiz_service.generate_quiz_from_text(
                text=extracted_text,
                topic=topic,
                chapter=chapter,
                num_questions=num_questions,
                language=language
            )
            
            if not result['success']:
                raise HTTPException(status_code=500, detail=f"Quiz generation failed: {result.get('error', 'Unknown error')}")
            
            # Generate Excel file
            excel_result = await quiz_service.generate_excel_file(
                questions=result['questions'],
                topic=topic,
                chapter=chapter
            )
            
            if not excel_result['success']:
                raise HTTPException(status_code=500, detail=f"Excel generation failed: {excel_result.get('error', 'Unknown error')}")
            
            return {
                'success': True,
                'filename': excel_result['filename'],
                'file_url': excel_result['file_url'],
                'topic': topic,
                'chapter': chapter,
                'total_questions': excel_result['total_questions'],
                'generated_at': excel_result['generated_at']
            }
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Quiz generation from OCR failed: {str(e)}")
