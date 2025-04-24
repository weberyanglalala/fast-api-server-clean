from fastapi import APIRouter, HTTPException
from .models import ImageUploadRequest, ImageUploadResponse
from src.utils.file_upload import upload_file_to_r2
import base64
import uuid
import re
from typing import List

router = APIRouter(
    prefix="/images",
    tags=["Images"]
)

@router.post("/upload", response_model=ImageUploadResponse)
async def upload_images(request: ImageUploadRequest):
    urls: List[str] = []
    for img_str in request.images:
        try:
            # Remove data URI prefix if present (e.g., "data:image/svg+xml;base64,")
            if img_str.startswith("data:"):
                # Extract the base64 part after the comma
                img_str = re.sub(r"^data:[^,]+,", "", img_str)
            img_bytes = base64.b64decode(img_str)
            file_name = f"image_{uuid.uuid4().hex}.png"
            url = upload_file_to_r2(file_name=file_name, file_content=img_bytes, content_type="image/png")
            urls.append(url)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to process image: {str(e)}")
    return ImageUploadResponse(urls=urls)
