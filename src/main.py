from fastapi import FastAPI
from .database.core import engine, Base
from .api import register_routes
from .logging import configure_logging, LogLevels

configure_logging(LogLevels.info)

app = FastAPI()
# Base.metadata.create_all(bind=engine)
register_routes(app)