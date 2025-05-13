import copy
import json
import logging
import os
from typing import Dict, Any, Optional

import aiohttp
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ComfyUI workflow JSON URL
COMFYUI_WORKFLOW_JSON_URL = os.getenv("COMFYUI_WORKFLOW_JSON_URL", "https://raw.githubusercontent.com/dannwu966/style/refs/heads/main/imgurl_outpainting.json")

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
