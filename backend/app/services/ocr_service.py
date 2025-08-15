import pytesseract
from PIL import Image
import cv2
import numpy as np
import os
import re
from typing import Optional, Dict, Any
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

class OCRService:
    """Simplified service for OCR text extraction from images"""
    
    def __init__(self):
        # Configure Tesseract path if needed
        if hasattr(settings, 'TESSERACT_CMD') and settings.TESSERACT_CMD:
            pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD
    
    async def extract_text(self, image_path: str, language: str = "eng") -> str:
        """
        Extract text from an image using OCR - simplified version
        
        Args:
            image_path: Path to the image file
            language: Language code for OCR processing
            
        Returns:
            Extracted text from the image
        """
        try:
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"Image file not found: {image_path}")
            
            # Use single, most effective approach
            image = self._preprocess_image(image_path)
            text = pytesseract.image_to_string(
                image, 
                lang=language,
                config='--psm 6'  # Assume uniform block of text
            )
            
            cleaned_text = self._clean_text(text)
            
            if cleaned_text.strip():
                logger.info(f"Successfully extracted text from {image_path}")
                return cleaned_text
            else:
                logger.warning(f"No text extracted from {image_path}")
                return ""
            
        except Exception as e:
            logger.error(f"Error extracting text from {image_path}: {str(e)}")
            return ""
    
    def _preprocess_image(self, image_path: str) -> np.ndarray:
        """
        Preprocess image for better OCR results - simplified version
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Preprocessed image as numpy array
        """
        # Read image
        image = cv2.imread(image_path)
        
        if image is None:
            raise ValueError(f"Could not read image: {image_path}")
        
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply simple thresholding for better text recognition
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        return binary
    
    def _clean_text(self, text: str) -> str:
        """
        Clean and normalize extracted text
        
        Args:
            text: Raw extracted text
            
        Returns:
            Cleaned and normalized text
        """
        if not text:
            return ""
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep basic punctuation and math symbols
        text = re.sub(r'[^\w\s\.\,\!\?\;\:\-\(\)\[\]\{\}\+\-\*\/\=\^\_]', '', text)
        
        # Normalize line breaks
        text = text.replace('\n', ' ').replace('\r', ' ')
        
        # Remove multiple spaces
        text = re.sub(r' +', ' ', text)
        
        # Strip leading/trailing whitespace
        text = text.strip()
        
        return text 