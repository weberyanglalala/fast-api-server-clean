from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class ComfyUIExpandImageRequest(BaseModel):
    """Request model for ComfyUI expand image with image URL replacement."""
    image_url: str = Field(..., description="URL of the image to use in the prompt")
    client_id: Optional[str] = Field("api-server", description="Client ID for the ComfyUI request")

    # Node 15 (ImagePadForOutpaint) properties
    left: Optional[int] = Field(None, description="Left padding for outpainting (node 15)")
    top: Optional[int] = Field(None, description="Top padding for outpainting (node 15)")
    right: Optional[int] = Field(None, description="Right padding for outpainting (node 15)")
    bottom: Optional[int] = Field(None, description="Bottom padding for outpainting (node 15)")

    # Node 21 (ImageResize+) properties
    width: Optional[int] = Field(None, description="Width for image resize (node 21)")
    height: Optional[int] = Field(None, description="Height for image resize (node 21)")


class ComfyUIExpandImageResponse(BaseModel):
    """Response model for ComfyUI expand image with image URL replacement."""
    status: str = Field("success", description="Status of the operation")
    result: Dict[str, Any] = Field(..., description="Modified ComfyUI prompt JSON")
    message: Optional[str] = Field(None, description="Additional information about the operation")
    prompt_id: Optional[str] = Field("error", description="Prompt ID for the ComfyUI request")
    
class PromptRequestDTO(BaseModel):
    """
    A minimalist request body required for submitting ComfyUI tasks,
    where prompt supports any JSON object structure, and client_id identifies the caller.
    """
    prompt: Dict[str, Any] = Field(..., description="ComfyUI 节点结构的 JSON 对象")
    client_id: str = Field(..., description="调用方客户端 ID")

    

