from fastapi import FastAPI

from .api import register_routes
from .log_config import configure_logging, LogLevels
from .middleware.exception_handlers import register_exception_handlers
from .middleware.comfyui_session import register_comfyui_session

configure_logging(LogLevels.info)

app = FastAPI()

# Register middleware
register_exception_handlers(app)
register_comfyui_session(app)
register_routes(app)
