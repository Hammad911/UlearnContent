from fastapi import APIRouter

from app.api.api_v1.endpoints import ocr, llm, files, pdf, quiz

api_router = APIRouter()

api_router.include_router(ocr.router, prefix="/ocr", tags=["ocr"])
api_router.include_router(llm.router, prefix="/llm", tags=["llm"])
api_router.include_router(files.router, prefix="/files", tags=["files"])
api_router.include_router(pdf.router, prefix="/pdf", tags=["pdf"])
api_router.include_router(quiz.router, prefix="/quiz", tags=["quiz"]) 