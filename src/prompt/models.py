from enum import Enum
from typing import List, Optional, Any, Dict

from pydantic import BaseModel, Field


class PromptImageRequest(BaseModel):
    """Request model for image prompt generation."""
    prompt: str = Field(..., description="Natural language prompt for image generation")
    model: Optional[str] = Field("gpt-4.1-nano", description="Chat model to use for processing the prompt")
    temperature: float = Field(0.7, description="Temperature for the chat model")
    
    
class PromptImageResponse(BaseModel):
    """Response model for image prompt generation."""
    original_prompt: str
    generated_images: Optional[List[str]] = None
    image_urls: Optional[List[str]] = None
    edited_images: Optional[Dict[str, Any]] = None
    message: Optional[str] = None