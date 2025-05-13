import os
import logging
import base64
from functools import lru_cache
from typing import Dict, Any, Optional, Callable

import aiohttp
from fastapi import Depends, HTTPException, status
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# ComfyUI environment variables
COMFYUI_BASE_URL = os.getenv("COMFYUI_BASE_URL", "https://comfyui.buildschool.dev")
COMFYUI_USERNAME = os.getenv("COMFYUI_USERNAME")
COMFYUI_PASSWORD = os.getenv("COMFYUI_PASSWORD")

# Create a factory function that returns an aiohttp ClientSession with basic auth
@lru_cache()
def get_comfyui_client() -> aiohttp.ClientSession:
    """
    Create and return an instance of aiohttp ClientSession with basic auth for ComfyUI.
    Uses lru_cache to ensure only one instance is created.
    
    Returns:
        aiohttp.ClientSession: A session configured with basic auth for ComfyUI
    """
    if not COMFYUI_USERNAME or not COMFYUI_PASSWORD:
        logger.warning("ComfyUI credentials not found in environment variables")
    
    # Create basic auth header
    auth = None
    if COMFYUI_USERNAME and COMFYUI_PASSWORD:
        auth = aiohttp.BasicAuth(COMFYUI_USERNAME, COMFYUI_PASSWORD)
    
    # Create session with basic auth
    return aiohttp.ClientSession(auth=auth)

# Define a dependency that can be used in FastAPI routes
ComfyUIClient = Callable[[], aiohttp.ClientSession]
get_async_comfyui_client = Depends(get_comfyui_client)

async def comfyui_request(
    endpoint: str,
    method: str = "GET",
    data: Optional[Dict[str, Any]] = None,
    client: aiohttp.ClientSession = None,
) -> Dict[str, Any]:
    """
    Make a request to the ComfyUI API.
    
    Args:
        endpoint: API endpoint (without base URL)
        method: HTTP method (GET, POST, etc.)
        data: Request data for POST/PUT requests
        client: aiohttp ClientSession (injected via dependency)
        
    Returns:
        Dict[str, Any]: Response data from ComfyUI API
    """
    url = f"{COMFYUI_BASE_URL}/{endpoint.lstrip('/')}"
    
    # Create a new client if one wasn't provided
    close_client = False
    if client is None:
        client = get_comfyui_client()
        close_client = True
    
    try:
        # Make the request
        if method.upper() == "GET":
            async with client.get(url) as response:
                await _handle_response(response)
                return await response.json()
        elif method.upper() == "POST":
            async with client.post(url, json=data) as response:
                await _handle_response(response)
                return await response.json()
        elif method.upper() == "PUT":
            async with client.put(url, json=data) as response:
                await _handle_response(response)
                return await response.json()
        elif method.upper() == "DELETE":
            async with client.delete(url) as response:
                await _handle_response(response)
                return await response.json()
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
    except aiohttp.ClientError as e:
        logger.error(f"ComfyUI API request failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"ComfyUI service unavailable: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error in ComfyUI API request: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error in ComfyUI API request: {str(e)}"
        )
    finally:
        # Close the client if we created it
        if close_client:
            await client.close()

async def _handle_response(response: aiohttp.ClientResponse) -> None:
    """
    Handle the API response, raising appropriate exceptions for error status codes.
    
    Args:
        response: aiohttp ClientResponse object
        
    Raises:
        HTTPException: If the response status code indicates an error
    """
    if response.status >= 400:
        error_detail = await response.text()
        logger.error(f"ComfyUI API error ({response.status}): {error_detail}")
        
        if response.status == 401:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication failed for ComfyUI API"
            )
        elif response.status == 403:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden access to ComfyUI API"
            )
        elif response.status == 404:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="ComfyUI API endpoint not found"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"ComfyUI API error: {error_detail}"
            )