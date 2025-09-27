import base64
import os
from typing import Optional
from io import BytesIO
from PIL import Image
from app.core.config import settings

try:
    from google import genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False


class ImageService:
    """Generate images using Gemini 2.5 Flash Image Preview API."""

    def __init__(self):
        # Use API key from settings (you can set this in .env file)
        self.api_key = settings.GEMINI_API_KEY   # Fallback to your key
        self.model_name = settings.GEMINI_IMAGE_MODEL or "gemini-2.5-flash-image-preview"
        
        if GENAI_AVAILABLE and self.api_key:
            try:
                # Set the API key as environment variable for the client
                os.environ["GEMINI_API_KEY"] = self.api_key
                self.client = genai.Client()
                self.configured = True
            except Exception as e:
                print(f"Failed to initialize Gemini client: {e}")
                self.configured = False
        else:
            self.configured = False

    def is_configured(self) -> bool:
        return self.configured

    def generate_diagram_png(self, prompt: str, width: int = 1024, height: int = 1024) -> Optional[bytes]:
        if not self.is_configured():
            print("Gemini API not configured")
            return None

        # Use a simple, direct prompt that works with the model
        enhanced_prompt = f"Create a simple educational diagram: {prompt}"

        try:
            # Use the new Google Generative AI client following the reference pattern
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[enhanced_prompt]
            )
            
            # Process response following the reference pattern
            if response.candidates and len(response.candidates) > 0:
                candidate = response.candidates[0]
                if candidate.content and candidate.content.parts:
                    for part in candidate.content.parts:
                        # Check for image data first (this is what we want)
                        if part.inline_data is not None and part.inline_data.data:
                            # Convert the image data to bytes
                            image_bytes = part.inline_data.data
                            print(f"✅ Found image data: {len(image_bytes):,} bytes")
                            return image_bytes
                        
                        # Log text response but continue looking for image
                        elif part.text is not None:
                            print(f"Text response: {part.text}")
            
            print(f"No image data found in response")
            return None

        except Exception as e:
            print(f"Image generation error: {e}")
            return None