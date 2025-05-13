import base64
import re
import uuid
import logging

from fastapi import APIRouter, HTTPException, Depends, status
from openai import AsyncOpenAI

from src.utils.file_upload import upload_file_to_r2
from src.utils.openai_image import (generate_image, ImageGenerationRequest, EditImageRequest,
                                    download_image_as_file, edit_images_openai, recognize_image,
                                    get_async_openai_client, get_image_dimensions)
from .models import *

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/images",
    tags=["Images"]
)


@router.post("/recognize", response_model=ImagesRecognizeResponse)
async def upload_images(request: ImagesRecognizeRequest, client: AsyncOpenAI = get_async_openai_client):
    images: List[ImageRecognizeObject] = []
    for img_url in request.urls:
        try:
            description = await recognize_image(img_url, client)
            images.append(ImageRecognizeObject(url=img_url, description=description))
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to process image: {str(e)}")
    return ImagesRecognizeResponse(images=images)


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
async def generate_images(request: ImageGenerateRequest, client: AsyncOpenAI = get_async_openai_client):
    """
    Generate images using OpenAI's image generation models.
    """
    try:
        # Convert our API request to the utility request model
        generation_request = ImageGenerationRequest(
            prompt=request.prompt,
            model=request.model,
            count=request.count,
            size=request.size,
            quality=request.quality,
        )

        # Generate the images
        generation_response = await generate_image(generation_request, client)

        # Store images if needed
        urls = []
        if request.store_images and generation_response.images:
            for img_str in generation_response.images:
                try:
                    img_bytes = base64.b64decode(img_str)
                    file_name = f"ai_generated_{uuid.uuid4().hex}.png"
                    url = await upload_file_to_r2(file_name=file_name, file_content=img_bytes, content_type="image/png")
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
async def edit_images(request: ImageEditRequest, client: AsyncOpenAI = get_async_openai_client):
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

        # Create the edit request
        edit_request = EditImageRequest(
            image_files=image_files,
            prompt=request.prompt
        )

        # Process the edit request
        edit_response = await edit_images_openai(
            request=edit_request,
            client=client)

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


@router.get("/image-dimensions", response_model=ImageDimensionsResponse)
async def image_dimensions(url: str):
    """
    FastAPI endpoint to fetch and return the dimensions of an image from a provided URL.
    Args:
        url: The URL of the image.
    Returns:
        JSON response with width and height of the image.
    """
    try:
        width, height = await get_image_dimensions(url)
        logger.info(f"Processed image dimensions for URL: {url}")
        return {"width": width, "height": height}
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Unexpected error for URL {url}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred."
        )
