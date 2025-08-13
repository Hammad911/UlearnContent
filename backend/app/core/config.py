from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "OCR-to-LLM Pipeline"
    
    # CORS
    CORS_ORIGINS: str = "http://localhost:3000"
    
    # Database
    DATABASE_URL: str = "sqlite:///./app.db"
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    
    # OpenAI
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-3.5-turbo"
    
    # Mistral AI (for OCR)
    MISTRAL_API_KEY: str = ""
    MISTRAL_MODEL: str = "mistral-ocr-latest"
    
    # Google Gemini AI (for content generation)
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"
    
    # File upload
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB for PDFs
    ALLOWED_EXTENSIONS: List[str] = [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".pdf"]
    
    # OCR
    TESSERACT_CMD: str = "tesseract"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()

# Create upload directory if it doesn't exist
os.makedirs(settings.UPLOAD_DIR, exist_ok=True) 