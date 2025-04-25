from enum import Enum
from typing import Optional, List

from openai import AsyncOpenAI
from pydantic import BaseModel, Field


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
