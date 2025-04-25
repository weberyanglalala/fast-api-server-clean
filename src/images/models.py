from pydantic import BaseModel, Field
from typing import List, Optional
from src.utils.openai_image import ImageModel

class ImageUploadRequest(BaseModel):
    images: List[str]  # List of base64-encoded image strings

class ImageUploadResponse(BaseModel):
    urls: List[str]  # List of public URLs

class ImageGenerateRequest(BaseModel):
    prompt: str
    model: ImageModel = ImageModel.GPT_IMAGE
    count: int = Field(default=1, ge=1, le=3)
    size: Optional[str] = None
    store_images: bool = True  # Whether to store the images and return URLs

class ImageGenerateResponse(BaseModel):
    images: Optional[List[str]] = None  # Base64-encoded images (if not stored)
    urls: Optional[List[str]] = None  # URLs to stored images or from OpenAI
