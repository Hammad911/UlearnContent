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
    
    # Google Gemini AI (for image generation)
    GEMINI_IMAGE_MODEL: str = "gemini-2.5-flash-image-preview"
    
    # MathPix (for formula conversion)
    MATHPIX_API_KEY: str = ""
    MATHPIX_APP_ID: str = ""
    
    # File upload
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB for PDFs
    ALLOWED_EXTENSIONS: List[str] = [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".pdf"]
    
    # OCR
    TESSERACT_CMD: str = "tesseract"

    # fal.ai image generation (deprecated - now using Vertex AI)
    FAL_KEY: str = ""
    
    # Vertex AI (for image generation)
    GOOGLE_CLOUD_PROJECT: str = ""
    VERTEX_LOCATION: str = "us-central1"
    GOOGLE_APPLICATION_CREDENTIALS: str = ""

    # AWS S3
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_DEFAULT_REGION: str = "us-east-1"
    S3_BUCKET_NAME: str = ""
    S3_PUBLIC_BASE: str = ""
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()

# Create upload directory if it doesn't exist
os.makedirs(settings.UPLOAD_DIR, exist_ok=True) 