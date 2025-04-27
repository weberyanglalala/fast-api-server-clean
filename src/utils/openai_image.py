import io
import logging
import urllib.parse
from enum import Enum
from typing import Optional, List

import aiohttp
from openai import AsyncOpenAI
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ImageModel(str, Enum):
    GPT_IMAGE = "gpt-image-1"
    DALL_E_3 = "dall-e-3"
    DALL_E_2 = "dall-e-2"


class ImageSize(str, Enum):
    # Common sizes
    SIZE_1024 = "1024x1024"

    # GPT Image sizes
    GPT_IMAGE_LANDSCAPE = "1536x1024"
    GPT_IMAGE_PORTRAIT = "1024x1536"
    GPT_IMAGE_AUTO = "auto"

    # DALL-E-2 sizes
    DALL_E_2_SMALL = "256x256"
    DALL_E_2_MEDIUM = "512x512"

    # DALL-E-3 sizes
    DALL_E_3_LANDSCAPE = "1792x1024"
    DALL_E_3_PORTRAIT = "1024x1792"


class ImageGenerationRequest(BaseModel):
    prompt: str
    model: ImageModel = ImageModel.GPT_IMAGE
    count: int = Field(default=1, ge=1, le=10)
    size: Optional[str] = None

    def get_appropriate_size(self) -> str:
        """Determine the appropriate size based on the selected model."""
        if not self.size:
            if self.model == ImageModel.GPT_IMAGE:
                return ImageSize.GPT_IMAGE_AUTO
            elif self.model == ImageModel.DALL_E_2:
                return ImageSize.SIZE_1024
            else:  # DALL-E-3
                return ImageSize.SIZE_1024
        return self.size


class ImageGenerationResponse(BaseModel):
    images: List[str]  # List of base64-encoded image data
    urls: Optional[List[str]] = None  # URLs if provided by the API


async def generate_image(request: ImageGenerationRequest) -> ImageGenerationResponse:
    """
    Generate images using OpenAI's image generation models.
    
    Args:
        request: ImageGenerationRequest with model parameters
        
    Returns:
        ImageGenerationResponse containing generated images
    """
    client = AsyncOpenAI()

    # Get appropriate size for the selected model
    size = request.get_appropriate_size()

    # response_format
    # https://platform.openai.com/docs/api-reference/images/create#images-create-response_format

    # For gpt-image-1, the response_format parameter is ignored.

    # Set response format based on model
    # - For DALL-E-2 and DALL-E-3, we can request "b64_json" or "url"
    # - For GPT-Image-1, response_format is ignored and always returns base64 images
    response_format = "b64_json"  # Default format for all models

    # Generate images
    response = await client.images.generate(
        model=request.model,
        prompt=request.prompt,
        n=request.count,
        size=size,
        **({"response_format": response_format} if request.model != ImageModel.GPT_IMAGE else {})
    )

    # Extract base64-encoded images
    images = []
    for img_data in response.data:
        if hasattr(img_data, 'b64_json') and img_data.b64_json:
            images.append(img_data.b64_json)

    # Extract URLs if available
    urls = None
    if hasattr(response.data[0], 'url') and response.data[0].url:
        urls = [img_data.url for img_data in response.data if hasattr(img_data, 'url')]

    return ImageGenerationResponse(images=images, urls=urls)


class ImageEditResponse(BaseModel):
    """Response model with the edited image."""
    image: Optional[str] = None  # Base64-encoded image data
    url: Optional[str] = None  # URL if provided by the API


async def download_image_as_file(url: str, filename: str) -> io.BytesIO:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            resp.raise_for_status()
            data = await resp.read()

    # 使用 urlsplit 獲取 https://pub-fae13a4a449b449a9d2618873c3032a5.r2.dev/ai_edited_06ff09fbca69419c91430d93de1ff650.png
    path = urllib.parse.urlsplit(url).path
    # 取得 urlsplit ai_edited_06ff09fbca69419c91430d93de1ff650.png
    filename = path.split("/")[-1]
    bio = io.BytesIO(data)
    bio.name = filename
    return bio


async def edit_images_openai(image_files, prompt) -> ImageEditResponse:
    # download and wrap each image as a file-like object with .name
    client = AsyncOpenAI()
    resp = await client.images.edit(
        model="gpt-image-1",
        image=image_files,
        prompt=prompt,
    )

    # pull out the b64 or url
    img: Optional[str] = None
    url: Optional[str] = None
    if resp.data and hasattr(resp.data[0], "b64_json"):
        img = resp.data[0].b64_json
    if resp.data and hasattr(resp.data[0], "url"):
        url = resp.data[0].url

    # optionally upload to R2 … then return
    return ImageEditResponse(image=img, url=url)


async def recognize_image(image_url: str) -> str:
    client = AsyncOpenAI()
    response = await client.chat.completions.create(
        model="gpt-4.1-nano",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text",
                     "text": "You are an advanced image analysis AI capable of providing detailed descriptions in Traditional Chinese. Your task is to analyze the following image and provide a comprehensive description of its contents."},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": image_url
                        }
                    },
                ],
            }
        ],
        max_tokens=150,
    )

    return response.choices[0].message.content