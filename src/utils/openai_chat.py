import json
import logging
import uuid  # for generating unique tool call IDs
from enum import Enum
from typing import List, Dict, Any, Optional, Callable, TypeVar, Union

from openai import AsyncOpenAI
from pydantic import BaseModel, Field

from src.utils.openai_image import generate_image, edit_images_openai, ImageGenerationRequest

logger = logging.getLogger(__name__)


class ChatModel(str, Enum):
    GPT_41_NANO = "gpt-4.1-nano"


class MessageRole(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    FUNCTION = "function"
    TOOL = "tool"


class Message(BaseModel):
    role: MessageRole
    content: str = ""
    name: Optional[str] = None
    tool_call_id: Optional[str] = None
    tool_calls: Optional[List["ToolCall"]] = None  # add support for embedding function call metadata


class ChatTool(BaseModel):
    type: str = "function"
    function: Dict[str, Any]


class ImageGenerationTool(ChatTool):
    """Tool for generating images using OpenAI image generation models."""
    
    def __init__(self):
        super().__init__(
            type="function",
            function={
                "name": "generate_image",
                "description": "Generate an image based on a text prompt",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "prompt": {
                            "type": "string",
                            "description": "A detailed description of the image to generate"
                        },
                        "model": {
                            "type": "string",
                            "enum": ["gpt-image-1", "dall-e-3", "dall-e-2"],
                            "description": "The image model to use",
                            "default": "gpt-image-1"
                        },
                        "count": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 10,
                            "description": "Number of images to generate",
                            "default": 1
                        },
                        "size": {
                            "type": "string",
                            "description": "Size of the image. If not provided, an appropriate default will be used based on the model."
                        }
                    },
                    "required": ["prompt"]
                }
            }
        )


class ImageEditTool(ChatTool):
    """Tool for editing images using OpenAI image editing capabilities."""
    
    def __init__(self):
        super().__init__(
            type="function",
            function={
                "name": "edit_image",
                "description": "Edit an image based on a text prompt",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "image_urls": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            },
                            "description": "URLs of the images to edit"
                        },
                        "prompt": {
                            "type": "string",
                            "description": "Description of the edits to apply to the image"
                        }
                    },
                    "required": ["image_urls", "prompt"]
                }
            }
        )


class ChatCompletionRequest(BaseModel):
    model: ChatModel = ChatModel.GPT_41_NANO
    messages: List[Message]
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    tools: Optional[List[ChatTool]] = None
    tool_choice: Optional[str] = "auto"
    

class ToolCall(BaseModel):
    id: str
    type: str = "function"
    function: Dict[str, Any]


class ChatCompletionResponse(BaseModel):
    content: Optional[str] = None
    tool_calls: Optional[List[ToolCall]] = None
    finish_reason: str
    

async def chat_completion(
    request: ChatCompletionRequest,
    client: AsyncOpenAI
) -> ChatCompletionResponse:
    """
    Send a chat completion request to OpenAI's API.
    
    Args:
        request: Parameters for the chat completion request
        client: AsyncOpenAI client
        
    Returns:
        ChatCompletionResponse containing the model's response
    """
    # Convert messages to the format expected by OpenAI
    messages = []
    for msg in request.messages:
        message_dict = {"role": msg.role, "content": msg.content}
        if msg.name:
            message_dict["name"] = msg.name
        if msg.tool_call_id:
            message_dict["tool_call_id"] = msg.tool_call_id
        if getattr(msg, 'tool_calls', None):
            # include tool_calls metadata for assistant messages when present
            message_dict['tool_calls'] = [tc.dict() for tc in msg.tool_calls]
        messages.append(message_dict)
    
    # Prepare optional parameters
    params = {
        "model": request.model,
        "messages": messages,
        "temperature": request.temperature,
    }
    
    if request.max_tokens:
        params["max_tokens"] = request.max_tokens
        
    if request.tools:
        params["tools"] = [tool.dict() for tool in request.tools]
        params["tool_choice"] = request.tool_choice
    
    # Send the request to OpenAI
    response = await client.chat.completions.create(**params)
    
    # Extract content and tool calls from the response
    choice = response.choices[0]
    message = choice.message
    
    content = message.content
    
    # Extract tool calls from the message if present
    tool_calls = None
    if hasattr(message, 'tool_calls') and message.tool_calls:
        tool_calls = [
            ToolCall(
                id=tc.id,
                type=tc.type,
                function={
                    "name": tc.function.name,
                    "arguments": tc.function.arguments
                }
            ) 
            for tc in message.tool_calls
        ]
    
    return ChatCompletionResponse(
        content=content,
        tool_calls=tool_calls,
        finish_reason=choice.finish_reason
    )


async def process_tool_calls(
    tool_calls: List[ToolCall],
    client: AsyncOpenAI
) -> List[Message]:
    """
    Process tool calls by executing the appropriate functions.
    
    Args:
        tool_calls: List of tool calls to process
        client: AsyncOpenAI client
        
    Returns:
        List of messages with tool outputs
    """
    tool_messages = []
    
    for tc in tool_calls:
        if tc.type == "function":
            function_name = tc.function["name"]
            arguments = json.loads(tc.function["arguments"])
            
            result = None
            if function_name == "generate_image":
                # Process image generation request
                gen_request = ImageGenerationRequest(
                    prompt=arguments["prompt"],
                    model=arguments.get("model", "gpt-image-1"),
                    count=arguments.get("count", 1),
                    size=arguments.get("size")
                )
                response = await generate_image(gen_request, client)
                result = {
                    "images": response.images,
                    "urls": response.urls
                }
                
            elif function_name == "edit_image":
                # Process image editing request
                response = await edit_images_openai(
                    image_files=arguments["image_urls"],
                    prompt=arguments["prompt"],
                    client=client
                )
                result = {
                    "image": response.image,
                    "url": response.url
                }
            
            # Create a tool message with the result
            if result:
                tool_messages.append(
                    Message(
                        role=MessageRole.TOOL,
                        content=json.dumps(result),
                        name=tc.function["name"],
                        # Include the tool_call_id to link this message to the corresponding tool call
                        tool_call_id=tc.id
                    )
                )
    
    return tool_messages


async def chat_completion_with_tools(
    request: ChatCompletionRequest,
    client: AsyncOpenAI
) -> ChatCompletionResponse:
    """
    Send a chat completion request with tools and handle tool calls.
    
    Args:
        request: Parameters for the chat completion request
        client: AsyncOpenAI client
        
    Returns:
        ChatCompletionResponse containing the final model's response
    """
    # Send initial request
    response = await chat_completion(request, client)
    
    # If no tool calls, return the response
    if not response.tool_calls:
        return response
    
    # Process tool calls
    tool_messages = await process_tool_calls(response.tool_calls, client)

    # Add assistant message with tool call metadata to the conversation
    assistant_message = Message(
        role=MessageRole.ASSISTANT,
        content=response.content or "",
        tool_calls=response.tool_calls
    )
    request.messages.append(assistant_message)

    # Add each tool message, linked to the assistant's tool calls
    for tool_msg in tool_messages:
        request.messages.append(tool_msg)
    
    # Send follow-up request to get final response
    final_response = await chat_completion(request, client)
    
    return final_response