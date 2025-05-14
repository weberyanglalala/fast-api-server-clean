import logging

import aiohttp
from fastapi import APIRouter, HTTPException, status

from src.utils.comfyui_client import get_async_comfyui_client, comfyui_request
from .models import (ComfyUIExpandImageRequest, ComfyUIExpandImageResponse, PromptRequestDTO, ExpandImageResultResponse,
                     ExpandImageResultRequest)
from .service import (replace_comfyui_expand_image_in_prompt, fetch_comfyui_expand_image_workflow_json,
                      get_comfyui_expand_image_result_file_path, upload_comfyui_server_image_to_r2)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/comfyui",
    tags=["ComfyUI"]
)


@router.post("/expandImage", response_model=ComfyUIExpandImageResponse)
async def process_comfyui_expand_image(
        request: ComfyUIExpandImageRequest,
        client: aiohttp.ClientSession = get_async_comfyui_client
):
    """
    Process a ComfyUI expand image request by replacing the image URL and updating node properties.

    The endpoint fetches the ComfyUI expand image workflow JSON from the URL specified in the environment variable
    and performs the following modifications:

    1. Replaces the image URL in node "22" with the provided image URL
    2. Updates the padding properties (left, top, right, bottom) in node "15" (ImagePadForOutpaint) if provided
    3. Updates the resize properties (width, height) in node "21" (ImageResize+) if provided
    4. Updates the client_id if provided

    Returns the modified ComfyUI expand image workflow JSON.
    """
    try:
        # Fetch the workflow JSON from the URL
        workflow_json = await fetch_comfyui_expand_image_workflow_json(aiohttp.ClientSession())

        # Replace the image URL and update node properties in the prompt
        modified_prompt = await replace_comfyui_expand_image_in_prompt(
            prompt=workflow_json,
            image_url=request.image_url,
            left=request.left,
            top=request.top,
            right=request.right,
            bottom=request.bottom,
            width=request.width,
            height=request.height
        )

        # Optionally, you can send the modified prompt to ComfyUI
        # Uncomment the following code if you want to send the prompt to ComfyUI
        prompt_dto = PromptRequestDTO(prompt=modified_prompt, client_id=request.client_id)
        result = await comfyui_request(
            endpoint="/prompt",
            method="POST",
            data=prompt_dto.dict(),
            client=client
        )

        if "prompt_id" not in result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="ComfyUI did not return a prompt_id"
            )

        return ComfyUIExpandImageResponse(
            status="success",
            result=result,
            prompt_id=result.get("prompt_id"),
            message="Image URL successfully replaced in expand image workflow"
        )

    except ValueError as e:
        logger.error(f"Value error in ComfyUI expand image processing: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error processing ComfyUI expand image: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process ComfyUI expand image: {str(e)}"
        )


@router.post("/expandImageResult", response_model=ExpandImageResultResponse)
async def process_comfyui_expand_image_result(
        request: ExpandImageResultRequest,
        client: aiohttp.ClientSession = get_async_comfyui_client
):
    try:
        # Get prompt history from ComfyUI server
        prompt_history = await comfyui_request(
            endpoint=f"/history/{request.prompt_id}",
            method="GET",
            client=client
        )

        # Get image file path from prompt history
        prompt_id_image_url = get_comfyui_expand_image_result_file_path(prompt_history, request.prompt_id)

        # Upload image from ComfyUI server to R2 storage and get public URL
        public_url = await upload_comfyui_server_image_to_r2(prompt_id_image_url, client)

        return ExpandImageResultResponse(public_url=public_url, status="success")

    except ValueError as e:
        logger.error(f"Value error in ComfyUI expand image result processing: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error processing ComfyUI expand image result: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process ComfyUI expand image result: {str(e)}"
        )
