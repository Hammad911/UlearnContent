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
    """Service for OCR text extraction from images"""
    
    def __init__(self):
        # Configure Tesseract path if needed
        if hasattr(settings, 'TESSERACT_CMD') and settings.TESSERACT_CMD:
            pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD
    
    async def extract_text(self, image_path: str, language: str = "eng") -> str:
        """
        Extract text from an image using OCR
        
        Args:
            image_path: Path to the image file
            language: Language code for OCR processing
            
        Returns:
            Extracted text from the image
        """
        try:
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"Image file not found: {image_path}")
            
            # Try multiple preprocessing approaches for better results
            text_results = []
            
            # Approach 1: Standard preprocessing
            try:
                image1 = self._preprocess_image(image_path)
                text1 = pytesseract.image_to_string(
                    image1, 
                    lang=language,
                    config='--psm 6'  # Assume uniform block of text
                )
                if text1.strip():
                    text_results.append(self._clean_text(text1))
            except Exception as e:
                logger.warning(f"Standard preprocessing failed: {str(e)}")
            
            # Approach 2: Different PSM mode
            try:
                image2 = self._preprocess_image(image_path)
                text2 = pytesseract.image_to_string(
                    image2, 
                    lang=language,
                    config='--psm 3'  # Fully automatic page segmentation
                )
                if text2.strip():
                    text_results.append(self._clean_text(text2))
            except Exception as e:
                logger.warning(f"PSM 3 preprocessing failed: {str(e)}")
            
            # Approach 3: Raw image without preprocessing
            try:
                raw_image = cv2.imread(image_path)
                if raw_image is not None:
                    text3 = pytesseract.image_to_string(
                        raw_image, 
                        lang=language,
                        config='--psm 6'
                    )
                    if text3.strip():
                        text_results.append(self._clean_text(text3))
            except Exception as e:
                logger.warning(f"Raw image processing failed: {str(e)}")
            
            # Return the best result (longest text)
            if text_results:
                best_text = max(text_results, key=len)
                logger.info(f"Successfully extracted text from {image_path} using {len(text_results)} approaches")
                return best_text
            else:
                logger.warning(f"No text extracted from {image_path}")
                return ""
            
        except Exception as e:
            logger.error(f"Error extracting text from {image_path}: {str(e)}")
            return ""
    
    def _preprocess_image(self, image_path: str) -> np.ndarray:
        """
        Preprocess image for better OCR results
        
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
        
        # Apply noise reduction
        denoised = cv2.medianBlur(gray, 3)
        
        # Apply thresholding to get binary image
        _, binary = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Apply morphological operations to remove noise
        kernel = np.ones((1, 1), np.uint8)
        processed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        
        return processed
    
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
        
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s\.\,\!\?\;\:\-\(\)\[\]\{\}]', '', text)
        
        # Normalize line breaks
        text = text.replace('\n', ' ').replace('\r', ' ')
        
        # Remove multiple spaces
        text = re.sub(r' +', ' ', text)
        
        # Strip leading/trailing whitespace
        text = text.strip()
        
        return text
    
    async def get_text_confidence(self, image_path: str, language: str = "eng") -> Dict[str, Any]:
        """
        Get OCR confidence scores for extracted text
        
        Args:
            image_path: Path to the image file
            language: Language code for OCR processing
            
        Returns:
            Dictionary containing text and confidence data
        """
        try:
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"Image file not found: {image_path}")
            
            # Load and preprocess image
            image = self._preprocess_image(image_path)
            
            # Get OCR data with confidence scores
            ocr_data = pytesseract.image_to_data(
                image, 
                lang=language,
                output_type=pytesseract.Output.DICT
            )
            
            # Extract text and confidence scores
            text_parts = []
            confidence_scores = []
            
            for i, conf in enumerate(ocr_data['conf']):
                if conf > 0:  # Filter out low confidence results
                    text_parts.append(ocr_data['text'][i])
                    confidence_scores.append(conf)
            
            full_text = ' '.join(text_parts)
            avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
            
            return {
                'text': self._clean_text(full_text),
                'confidence': avg_confidence,
                'word_count': len(text_parts),
                'character_count': len(full_text)
            }
            
        except Exception as e:
            logger.error(f"Error getting confidence for {image_path}: {str(e)}")
            raise
    
    async def detect_language(self, image_path: str) -> str:
        """
        Detect the language of text in the image
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Detected language code
        """
        try:
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"Image file not found: {image_path}")
            
            # Load and preprocess image
            image = self._preprocess_image(image_path)
            
            # Use Tesseract's language detection
            osd = pytesseract.image_to_osd(image)
            
            # Parse OSD output to get language
            # This is a simplified approach - in production you might want more sophisticated language detection
            if 'eng' in osd.lower():
                return 'eng'
            elif 'fra' in osd.lower():
                return 'fra'
            elif 'deu' in osd.lower():
                return 'deu'
            elif 'spa' in osd.lower():
                return 'spa'
            else:
                return 'eng'  # Default to English
                
        except Exception as e:
            logger.error(f"Error detecting language for {image_path}: {str(e)}")
            return 'eng'  # Default to English on error 