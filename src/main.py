from fastapi import FastAPI

from .api import register_routes
from .log_config import configure_logging, LogLevels
from .middleware.exception_handlers import register_exception_handlers

configure_logging(LogLevels.info)

app = FastAPI()

# Register exception handlers middleware
register_exception_handlers(app)
register_routes(app)
