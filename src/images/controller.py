import base64
import re
import uuid

from fastapi import APIRouter, HTTPException

from src.utils.file_upload import upload_file_to_r2
from src.utils.openai_image import generate_image, ImageGenerationRequest, \
    download_image_as_file, edit_images_openai
from .models import *

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
            url = await upload_file_to_r2(file_name=file_name, file_content=img_bytes, content_type="image/png")
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
        generation_response = await generate_image(generation_request)

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


@router.post("/edit", response_model=ImageEditResponse)
async def edit_images(request: ImageEditRequest):
    """
    Edit multiple images using OpenAI's image editing capability and the provided prompt.
    The images are downloaded from the provided URLs, wrapped as file-likes with names
    (so we get image/png, image/jpeg, etc.), edited according to the prompt, and
    the resulting image is optionally uploaded to R2 storage.
    """
    try:
        # Download all images from the provided URLs and wrap in io.BytesIO with .name
        image_files = []
        for url in request.image_urls:
            try:
                img_file = await download_image_as_file(url, str(uuid.uuid4()))
            except Exception as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Failed to download image from {url}: {e}"
                )
            image_files.append(img_file)

        # Process the edit request
        edit_response = await edit_images_openai(
            image_files=image_files,
            prompt=request.prompt)

        # If requested, store the edited image in R2
        final_url = None
        if request.store_image and edit_response.image:
            try:
                img_bytes = base64.b64decode(edit_response.image)
                file_name = f"ai_edited_{uuid.uuid4().hex}.png"
                final_url = await upload_file_to_r2(
                    file_name=file_name,
                    file_content=img_bytes,
                    content_type="image/png"
                )
            except Exception as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Failed to store edited image: {e}"
                )

        return ImageEditResponse(
            image=(None if request.store_image else edit_response.image),
            url=(final_url if request.store_image else edit_response.url)
        )

    except HTTPException:
        # re-raise HTTPExceptions so FastAPI handles them
        raise
    except Exception as e:
        # catch-all
        raise HTTPException(status_code=500, detail=f"Image editing failed: {e}")
