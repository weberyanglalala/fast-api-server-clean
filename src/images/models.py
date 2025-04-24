from pydantic import BaseModel
from typing import List

class ImageUploadRequest(BaseModel):
    images: List[str]  # List of base64-encoded image strings

class ImageUploadResponse(BaseModel):
    urls: List[str]  # List of public URLs
