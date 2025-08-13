from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from typing import List
import os
import uuid
import logging
from datetime import datetime
import io

logger = logging.getLogger(__name__)

from app.core.config import settings
from app.services.pdf_service import PDFService
from app.services.excel_service import ExcelService
from app.services.llm_service import LLMService
from app.models.pdf_models import PDFResponse, ExcelRequest

router = APIRouter()
pdf_service = PDFService()
excel_service = ExcelService()
llm_service = LLMService()

@router.post("/extract", response_model=PDFResponse)
async def extract_text_from_pdf(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """
    Extract text from uploaded PDF file, including images
    """
    # Validate file type
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=400,
            detail="File must be a PDF"
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
        filename = f"{file_id}.pdf"
        file_path = os.path.join(settings.UPLOAD_DIR, filename)
        
        # Save uploaded file
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Extract text from PDF
        result = await pdf_service.extract_text_from_pdf(file_path)
        
        # Clean up file in background
        background_tasks.add_task(os.remove, file_path)
        
        return PDFResponse(
            success=True,
            file_id=file_id,
            original_filename=file.filename,
            text=result['text'],
            structure=result['structure'],
            pages=result['pages'],
            image_count=result['image_count'],
            total_pages=result['total_pages'],
            processed_at=datetime.utcnow()
        )
        
    except Exception as e:
        # Clean up file if it exists
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"PDF processing failed: {str(e)}")

@router.post("/generate-excel")
async def generate_excel_from_pdf(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    include_metadata: bool = True
):
    """
    Extract text from PDF and generate Excel file with structured content
    """
    # Validate file type
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=400,
            detail="File must be a PDF"
        )
    
    try:
        # Generate unique filename
        file_id = str(uuid.uuid4())
        filename = f"{file_id}.pdf"
        file_path = os.path.join(settings.UPLOAD_DIR, filename)
        
        # Save uploaded file
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Extract text from PDF
        pdf_result = await pdf_service.extract_text_from_pdf(file_path)
        
        # Log the extracted text for debugging
        logger.info(f"Extracted text length: {len(pdf_result.get('text', ''))}")
        logger.info(f"Structure: {pdf_result.get('structure', {})}")
        
        # Generate Excel content using LLM
        excel_data = await pdf_service.create_excel_content(
            pdf_result['text'], 
            pdf_result['structure']
        )
        
        # Log the Excel data for debugging
        logger.info(f"Excel data items: {len(excel_data.get('data', []))}")
        logger.info(f"Excel data sample: {excel_data.get('data', [])[:2]}")
        
        # Create Excel file
        if include_metadata:
            metadata = {
                'original_filename': file.filename,
                'total_pages': pdf_result['total_pages'],
                'image_count': pdf_result['image_count'],
                'content_breakdown': pdf_result.get('content_breakdown', {}),
                'processed_at': datetime.utcnow().isoformat(),
                'file_id': file_id
            }
            excel_bytes = excel_service.create_advanced_excel(
                excel_data['data'], 
                metadata,
                pdf_result.get('detailed_content', {})
            )
        else:
            excel_bytes = excel_service.create_excel_file(
                excel_data['data'],
                detailed_content=pdf_result.get('detailed_content', {})
            )
        
        # Clean up file in background
        background_tasks.add_task(os.remove, file_path)
        
        # Generate Excel filename
        excel_filename = f"{os.path.splitext(file.filename)[0]}_content.xlsx"
        
        return StreamingResponse(
            io.BytesIO(excel_bytes),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={excel_filename}"}
        )
        
    except Exception as e:
        # Clean up file if it exists
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Excel generation failed: {str(e)}")

@router.post("/get-excel-content")
async def get_excel_content(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """
    Get Excel content without downloading the file
    """
    # Validate file type
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=400,
            detail="File must be a PDF"
        )
    
    try:
        # Generate unique filename
        file_id = str(uuid.uuid4())
        filename = f"{file_id}.pdf"
        file_path = os.path.join(settings.UPLOAD_DIR, filename)
        
        # Save uploaded file
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Extract text from PDF
        pdf_result = await pdf_service.extract_text_from_pdf(file_path)
        
        # Log the extracted text for debugging
        logger.info(f"Extracted text length: {len(pdf_result.get('text', ''))}")
        logger.info(f"Structure: {pdf_result.get('structure', {})}")
        
        # Generate Excel content using LLM
        excel_data = await pdf_service.create_excel_content(
            pdf_result['text'], 
            pdf_result['structure']
        )
        
        # Log the Excel data for debugging
        logger.info(f"Excel data items: {len(excel_data.get('data', []))}")
        logger.info(f"Excel data sample: {excel_data.get('data', [])[:2]}")
        
        # Clean up file in background
        background_tasks.add_task(os.remove, file_path)
        
        return {
            "success": True,
            "data": excel_data.get('data', []),
            "total_items": len(excel_data.get('data', [])),
            "original_filename": file.filename
        }
        
    except Exception as e:
        # Clean up file if it exists
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Content generation failed: {str(e)}")

@router.post("/analyze-content")
async def analyze_pdf_content(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """
    Analyze PDF content and provide detailed insights
    """
    # Validate file type
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=400,
            detail="File must be a PDF"
        )
    
    try:
        # Generate unique filename
        file_id = str(uuid.uuid4())
        filename = f"{file_id}.pdf"
        file_path = os.path.join(settings.UPLOAD_DIR, filename)
        
        # Save uploaded file
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Extract text from PDF
        pdf_result = await pdf_service.extract_text_from_pdf(file_path)
        
        # Analyze content with LLM
        analysis_prompt = f"""
        Analyze the following PDF content and provide:
        1. Main topics and themes
        2. Key concepts and definitions
        3. Important examples or case studies
        4. Summary of each chapter/section
        5. Educational value and learning objectives
        
        Content:
        {pdf_result['text'][:5000]}  # Limit to first 5000 chars for analysis
        """
        
        analysis_result = await llm_service.process_text(
            text=analysis_prompt,
            task_type="analyze",
            additional_context={"analysis_type": "educational_content"}
        )
        
        # Clean up file in background
        background_tasks.add_task(os.remove, file_path)
        
        return {
            "success": True,
            "file_id": file_id,
            "original_filename": file.filename,
            "analysis": analysis_result,
            "structure": pdf_result['structure'],
            "stats": {
                "total_pages": pdf_result['total_pages'],
                "image_count": pdf_result['image_count'],
                "text_length": len(pdf_result['text']),
                "chapters": len(pdf_result['structure']['chapters']),
                "sections": len(pdf_result['structure']['sections'])
            },
            "processed_at": datetime.utcnow()
        }
        
    except Exception as e:
        # Clean up file if it exists
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Content analysis failed: {str(e)}") 