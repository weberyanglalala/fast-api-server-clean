# ComfyUI Client Integration Guide

This document provides guidance on how to use the ComfyUI HTTP client in your FastAPI Clean Architecture project.

## Overview

The ComfyUI client is a named HTTP client specifically designed to interact with the ComfyUI API at `https://comfyui.buildschool.dev`. It handles authentication and provides a clean interface for making API requests.

## Configuration

### Environment Variables

The ComfyUI client requires the following environment variables:

```bash
# ComfyUI API settings
COMFYUI_BASE_URL=https://comfyui.buildschool.dev
COMFYUI_USERNAME=your_comfyui_username
COMFYUI_PASSWORD=your_comfyui_password
```

Add these to your `.env` file. The `.env.example` file has been updated to include these variables.

## Client Implementation

The ComfyUI client is implemented in `src/utils/comfyui_client.py` and provides:

1. A factory function that returns an authenticated aiohttp ClientSession
2. A FastAPI dependency for injecting the client into routes
3. Helper functions for making API requests with proper error handling

### Key Components

#### Client Factory

```python
@lru_cache()
def get_comfyui_client() -> aiohttp.ClientSession:
    """
    Create and return an instance of aiohttp ClientSession with basic auth for ComfyUI.
    Uses lru_cache to ensure only one instance is created.
    """
    if not COMFYUI_USERNAME or not COMFYUI_PASSWORD:
        logger.warning("ComfyUI credentials not found in environment variables")
    
    # Create basic auth header
    auth = None
    if COMFYUI_USERNAME and COMFYUI_PASSWORD:
        auth = aiohttp.BasicAuth(COMFYUI_USERNAME, COMFYUI_PASSWORD)
    
    # Create session with basic auth
    return aiohttp.ClientSession(auth=auth)
```

#### FastAPI Dependency

```python
# Define a dependency that can be used in FastAPI routes
ComfyUIClient = Callable[[], aiohttp.ClientSession]
get_async_comfyui_client = Depends(get_comfyui_client)
```

#### Request Helper

```python
async def comfyui_request(
    endpoint: str,
    method: str = "GET",
    data: Optional[Dict[str, Any]] = None,
    client: aiohttp.ClientSession = None,
) -> Dict[str, Any]:
    """
    Make a request to the ComfyUI API.
    """
    # Implementation details...
```

## Usage Examples

### Basic Usage in a Controller

```python
from fastapi import APIRouter, Depends
import aiohttp
from src.utils.comfyui_client import get_async_comfyui_client, comfyui_request

router = APIRouter(prefix="/comfyui", tags=["comfyui"])

@router.get("/status")
async def get_comfyui_status(
    client: aiohttp.ClientSession = get_async_comfyui_client
) -> Dict[str, Any]:
    """Get the status of the ComfyUI API."""
    result = await comfyui_request(
        endpoint="/status",
        method="GET",
        client=client
    )
    return {"status": "success", "data": result}
```

### Running a Workflow

```python
@router.post("/workflow")
async def run_comfyui_workflow(
    workflow_data: Dict[str, Any],
    client: aiohttp.ClientSession = get_async_comfyui_client
) -> Dict[str, Any]:
    """Run a workflow in ComfyUI."""
    result = await comfyui_request(
        endpoint="/api/workflow",
        method="POST",
        data=workflow_data,
        client=client
    )
    return {"status": "success", "data": result}
```

### Integration with FastAPI App

To use the ComfyUI endpoints in your FastAPI application, create a router and include it in your main app:

```python
# In your controller file
from fastapi import APIRouter
router = APIRouter(prefix="/comfyui", tags=["comfyui"])

# Define your endpoints...

# In src/api.py
from fastapi import FastAPI
from your_module.controller import router as comfyui_router

def register_routes(app: FastAPI):
    # Other routers...
    app.include_router(comfyui_router)
```

## Error Handling

The ComfyUI client includes comprehensive error handling:

- HTTP errors (401, 403, 404, etc.) are converted to appropriate FastAPI HTTPExceptions
- Network errors are caught and reported with clear error messages
- All errors are logged for debugging purposes

## Best Practices

1. **Dependency Injection**: Always use the provided dependency for getting the client
2. **Error Handling**: Let the client handle HTTP errors, but catch and handle application-specific errors
3. **Resource Management**: The client handles session cleanup automatically
4. **Configuration**: Keep credentials in environment variables, never hardcode them

## Troubleshooting

Common issues and solutions:

1. **Authentication Failures**: Ensure COMFYUI_USERNAME and COMFYUI_PASSWORD are correctly set
2. **Connection Errors**: Check if the ComfyUI service is available and accessible
3. **Timeout Errors**: For long-running operations, consider increasing the timeout settings

## Further Development

Potential enhancements for the ComfyUI client:

1. Add caching for frequently used endpoints
2. Implement retry logic for transient failures
3. Add support for WebSocket connections if needed
4. Create more specific models for request/response data