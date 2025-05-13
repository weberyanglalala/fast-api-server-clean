import aiohttp
from fastapi import FastAPI

from ..utils.comfyui_client import COMFYUI_BASE_URL, COMFYUI_USERNAME, COMFYUI_PASSWORD


def register_comfyui_session(app: FastAPI):
    """
    Register ComfyUI session middleware.
    
    This middleware creates an aiohttp ClientSession for ComfyUI on startup
    and closes it on shutdown.
    
    Args:
        app: FastAPI application instance
    """
    @app.on_event("startup")
    async def create_comfyui_session():
        auth = None
        if COMFYUI_USERNAME and COMFYUI_PASSWORD:
            auth = aiohttp.BasicAuth(COMFYUI_USERNAME, COMFYUI_PASSWORD)
        app.state.comfyui_client = aiohttp.ClientSession(
            base_url=COMFYUI_BASE_URL,
            auth=auth
        )

    @app.on_event("shutdown")
    async def close_comfyui_session():
        await app.state.comfyui_client.close()