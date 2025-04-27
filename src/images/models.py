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

class ImageEditRequest(BaseModel):
    image_urls: List[str]  # List of URLs to images that will be edited
    prompt: str
    model: ImageModel = ImageModel.GPT_IMAGE
    store_image: bool = True  # Whether to store the image and return URL

class ImageEditResponse(BaseModel):
    image: Optional[str] = None  # Base64-encoded image (if not stored)
    url: Optional[str] = None  # URL to stored image

class ImagesRecognizeRequest(BaseModel):
    urls: List[str]  # List of public URLs

class ImageRecognizeObject(BaseModel):
    url: str
    description: str

class ImagesRecognizeResponse(BaseModel):
    images: List[ImageRecognizeObject]