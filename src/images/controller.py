from fastapi import APIRouter, HTTPException
from .models import ImageUploadRequest, ImageUploadResponse, ImageGenerateRequest, ImageGenerateResponse
from src.utils.file_upload import upload_file_to_r2
from src.utils.openai_image import generate_image, ImageGenerationRequest
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

@router.post("/generate", response_model=ImageGenerateResponse)
async def generate_images(request: ImageGenerateRequest):
    """
    Generate images using OpenAI's image generation models.
    """
    try:
        # Convert our API request to the utility request model
        generation_request = ImageGenerationRequest(
            prompt=request.prompt,
            model=request.model,
            count=request.count,
            size=request.size
        )
        
        # Generate the images
        generation_response = generate_image(generation_request)
        
        # Store images if needed
        urls = []
        if request.store_images and generation_response.images:
            for img_str in generation_response.images:
                try:
                    img_bytes = base64.b64decode(img_str)
                    file_name = f"ai_generated_{uuid.uuid4().hex}.png"
                    url = upload_file_to_r2(file_name=file_name, file_content=img_bytes, content_type="image/png")
                    urls.append(url)
                except Exception as e:
                    raise HTTPException(status_code=400, detail=f"Failed to store generated image: {str(e)}")
        
        return ImageGenerateResponse(
            images=generation_response.images if not request.store_images else None,
            urls=urls if request.store_images else generation_response.urls
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image generation failed: {str(e)}")
