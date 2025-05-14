import copy
import json
import logging
import os
import uuid
from typing import Dict, Any, Optional
import aiohttp
from urllib.parse import urlparse, parse_qs
from dotenv import load_dotenv
from src.utils.comfyui_client import comfyui_request_bytes
from src.utils.file_upload import upload_file_to_r2

# Load environment variables
load_dotenv()

# ComfyUI workflow JSON URL
COMFYUI_WORKFLOW_JSON_URL = os.getenv("COMFYUI_WORKFLOW_JSON_URL",
                                      "https://raw.githubusercontent.com/dannwu966/style/refs/heads/main/imgurl_outpainting.json")
COMFYUI_BASE_URL = os.getenv("COMFYUI_BASE_URL", "https://comfyui.buildschool.dev")
logger = logging.getLogger(__name__)


async def fetch_comfyui_expand_image_workflow_json(client: aiohttp.ClientSession) -> Dict[str, Any]:
    """
    Fetch the ComfyUI expand image workflow JSON from the URL specified in the environment variable.

    Args:
        client: aiohttp ClientSession

    Returns:
        The ComfyUI workflow JSON
    """
    if client is None:
        raise ValueError("Client session must be provided")

    try:
        # Fetch the workflow JSON
        async with client.get(COMFYUI_WORKFLOW_JSON_URL) as response:
            if response.status != 200:
                raise ValueError(f"Failed to fetch workflow JSON: HTTP {response.status}")

            text = await response.text()
            try:
                workflow_json = json.loads(text)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON format: {str(e)}")

            logger.info(f"Successfully fetched workflow JSON from {COMFYUI_WORKFLOW_JSON_URL}")
            return workflow_json
    except Exception as e:
        logger.error(f"Error fetching workflow JSON: {str(e)}")
        raise ValueError(f"Failed to fetch workflow JSON: {str(e)}")


async def replace_comfyui_expand_image_in_prompt(
        prompt: Dict[str, Any],
        image_url: str,
        left: Optional[int] = None,
        top: Optional[int] = None,
        right: Optional[int] = None,
        bottom: Optional[int] = None,
        width: Optional[int] = None,
        height: Optional[int] = None
) -> Dict[str, Any]:
    """
    Replace the image URL in the ComfyUI expand image workflow JSON and update other node properties.

    Args:
        prompt: The ComfyUI prompt JSON
        image_url: The URL of the image to use in the prompt
        client_id: Optional client ID for the ComfyUI request
        left: Left padding for outpainting (node 15)
        top: Top padding for outpainting (node 15)
        right: Right padding for outpainting (node 15)
        bottom: Bottom padding for outpainting (node 15)
        width: Width for image resize (node 21)
        height: Height for image resize (node 21)

    Returns:
        The modified ComfyUI prompt JSON
    """
    try:
        # Create a deep copy of the prompt to avoid modifying the original
        modified_prompt = copy.deepcopy(prompt)

        # image_url node_id
        image_url_node_id = "22"

        # Check if the node_id exists in the prompt
        if image_url_node_id not in modified_prompt:
            logger.warning(f"Node ID {image_url_node_id} not found in prompt")
            return modified_prompt

        # Replace the image URL in the specified node using update_node_properties
        modified_prompt[image_url_node_id]["inputs"]["image"] = image_url

        # Update node 15 (ImagePadForOutpaint) properties if provided
        if left is not None:
            modified_prompt["15"]["inputs"]["left"] = left
        if top is not None:
            modified_prompt["15"]["inputs"]["top"] = top
        if right is not None:
            modified_prompt["15"]["inputs"]["right"] = right
        if bottom is not None:
            modified_prompt["15"]["inputs"]["bottom"] = bottom

        # Update node 21 (ImageResize+) properties if provided
        if width is not None:
            modified_prompt["21"]["inputs"]["width"] = width
        if height is not None:
            modified_prompt["21"]["inputs"]["height"] = height

        return modified_prompt
    except Exception as e:
        logger.error(f"Error replacing image URL in prompt: {str(e)}")
        raise ValueError(f"Failed to replace image URL in prompt: {str(e)}")


def get_comfyui_expand_image_result_file_path(prompt_json: Dict[str, Any], prompt_id: str) -> str:
    if prompt_id not in prompt_json:
        raise ValueError(f"Prompt JSON {prompt_id} not found in prompt")

    # workflow history sample from prompt_id 71f5fa0f-1943-4e86-9379-dd802d3b53a8
    if "outputs" not in prompt_json[prompt_id]:
        raise ValueError("Outputs not found in prompt response")
    outputs = prompt_json[prompt_id]["outputs"]

    if "16" not in outputs or "images" not in outputs["16"] or not outputs["16"]["images"]:
        raise ValueError("Image output data not found in prompt response")
    image_result = outputs["16"]["images"][0]

    for prop in ["filename", "subfolder", "type"]:
        if prop not in image_result:
            raise ValueError(f"Required property '{prop}' missing in image result")

    filename = image_result["filename"]
    subfolder = image_result["subfolder"]
    file_type = image_result["type"]

    # https://comfyui.buildschool.dev/view?type=output&filename=ComfyUI_01715_.png&subfolder=
    return f"{COMFYUI_BASE_URL}/view?type={file_type}&filename={filename}&subfolder={subfolder}"


async def upload_comfyui_server_image_to_r2(
        file_url: str,
        client: aiohttp.ClientSession
) -> str:
    """
    Uploads an image from a ComfyUI server to an R2 storage.

    This function retrieves an image from a ComfyUI server via the provided URL,
    downloads it as bytes, assigns a unique filename using UUID, and uploads it
    to an R2 storage. The function returns the final URL of the uploaded image.

    Parameters:
        file_url: str
            The URL of the image on the ComfyUI server.
        client: aiohttp.ClientSession
            An active instance of aiohttp.ClientSession used to make HTTP requests.

    Returns:
        str
            The URL of the uploaded image in R2 storage.
    """
    filename, file_type, file_path = parse_comfyui_url(file_url)

    filename = f"{filename}-{uuid.uuid4()}.{file_type}"

    # Use file_path directly instead of 'endpoint' since this path already
    # includes the full URL with query params, and we don't need to combine
    # it with a base URL from the client
    image_bytes = await comfyui_request_bytes(
        endpoint=file_path,
        client=client
    )

    return await upload_file_to_r2(filename, image_bytes, file_type)


def parse_comfyui_url(url: str) -> tuple[str, str, str]:
    """Parse ComfyUI URL to get filename and file type."""
    # Example: "https://comfyui.buildschool.dev/view?type=output&filename=ComfyUI_01715_.png&subfolder="

    parsed = urlparse(url)
    query_params = parse_qs(parsed.query)

    filename = query_params["filename"][0].rsplit(".", 1)[0]  # ComfyUI_01715_
    file_type = query_params["filename"][0].split(".")[-1]  # png
    file_path = parsed.path + "?" + parsed.query
    return filename, file_type, file_path
