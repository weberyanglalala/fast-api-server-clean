import json
import logging
from typing import List

from fastapi import APIRouter, HTTPException, Depends
from openai import AsyncOpenAI

from src.utils.openai_chat import (
    ChatCompletionRequest, Message, MessageRole,
    ImageGenerationTool, ImageEditTool, chat_completion_with_tools,
    ChatModel
)
from src.utils.openai_image import get_async_openai_client
from .models import PromptImageRequest, PromptImageResponse

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/prompt",
    tags=["Prompts"]
)


@router.post("/image", response_model=PromptImageResponse)
async def process_image_prompt(
    request: PromptImageRequest,
    client: AsyncOpenAI = get_async_openai_client
):
    """
    Process a natural language prompt for image generation using AI tools.
    
    The endpoint analyzes a natural language prompt and determines whether to:
    1. Generate new images based on the description
    2. Edit existing images based on the description (if image URLs are detected)
    3. A combination of both
    
    Returns generated/edited images with appropriate URLs and descriptions.
    """
    try:
        # Create initial system message
        system_message = Message(
            role=MessageRole.SYSTEM,
            content="""You are an AI assistant specialized in processing image-related requests.
            You can:
            1. Generate new images from text descriptions
            2. Edit existing images based on instructions
            
            You can use the following tools to accomplish these tasks:
            - generate_image: Creates new images based on a prompt
            - edit_image: Modifies existing images based on instructions
            
            Analyze the user's request and determine the appropriate action.
            For image generation, extract or refine the description to create high-quality prompts.
            For image editing, identify the URLs to edit and create clear edit instructions.
            """
        )
        
        # Create user message
        user_message = Message(
            role=MessageRole.USER,
            content=request.prompt
        )
        
        # Create chat completion request with tools
        chat_request = ChatCompletionRequest(
            model=ChatModel(request.model),
            messages=[system_message, user_message],
            temperature=request.temperature,
            tools=[ImageGenerationTool(), ImageEditTool()],
            tool_choice="auto"
        )
        
        # Send the request with tools
        chat_response = await chat_completion_with_tools(chat_request, client)
        
        # Analyze the response to check for generated or edited images
        generated_images = None
        image_urls = None
        edited_images = None
        
        # Check for content
        message = chat_response.content if chat_response.content else "Processing complete"
        
        # Collect the results from the tool calls in the conversation history
        for msg in chat_request.messages:
            if msg.role == MessageRole.TOOL:
                try:
                    tool_result = json.loads(msg.content)
                    
                    if msg.name == "generate_image":
                        generated_images = tool_result.get("images")
                        image_urls = tool_result.get("urls")
                    
                    elif msg.name == "edit_image":
                        if not edited_images:
                            edited_images = {}
                        edited_images[msg.name] = tool_result
                except Exception as e:
                    logger.error(f"Error parsing tool result: {e}")
        
        return PromptImageResponse(
            original_prompt=request.prompt,
            generated_images=generated_images,
            image_urls=image_urls,
            edited_images=edited_images,
            message=message
        )
        
    except Exception as e:
        logger.error(f"Error processing image prompt: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process image prompt: {str(e)}")