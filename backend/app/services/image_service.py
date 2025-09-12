import base64
import os
import requests
from typing import Optional
from app.core.config import settings


class ImageService:
    """Generate images with fal.ai FLUX using FAL_KEY."""

    def __init__(self):
        self.api_key = settings.FAL_KEY
        self.endpoint = "https://fal.run/fal-ai/fast-sdxl"

    def is_configured(self) -> bool:
        return bool(self.api_key)

    def generate_diagram_png(self, prompt: str, width: int = 1024, height: int = 1024) -> Optional[bytes]:
        if not self.api_key:
            return None
        
        # Enhance prompt for better educational diagrams
        enhanced_prompt = f"Simple black and white line drawing, technical diagram, scientific illustration, clean line art, white background, black lines only, educational textbook style, labeled parts, no colors, no artistic effects, no shadows, no gradients, simple and clear, minimalist: {prompt}"
        
        headers = {"Authorization": f"Key {self.api_key}", "Content-Type": "application/json"}
        payload = {
            "prompt": enhanced_prompt,
            "image_size": "square",
            "num_inference_steps": 4,
            "enable_safety_checker": True,
        }
        
        try:
            resp = requests.post(self.endpoint, json=payload, headers=headers, timeout=60)
            resp.raise_for_status()
            data = resp.json()
            
            # Handle the new response format with image URLs
            images = data.get("images", [])
            if not images:
                print(f"No images in response: {data}")
                return None
            
            # Get the first image URL
            image_url = images[0].get("url")
            if not image_url:
                print(f"No image URL in response: {data}")
                return None
            
            # Download the image from the URL
            img_resp = requests.get(image_url, timeout=30)
            img_resp.raise_for_status()
            return img_resp.content
            
        except Exception as e:
            print(f"Image generation error: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response content: {e.response.text}")
            return None


