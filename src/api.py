from fastapi import FastAPI
from src.todos.controller import router as todos_router
from src.auth.controller import router as auth_router
from src.users.controller import router as users_router
from src.documents.controller import router as documents_router
from src.images.controller import router as images_router
from src.prompt.controller import router as prompt_router
from src.comfyui.controller import router as comfyui_router

def register_routes(app: FastAPI):
    app.include_router(todos_router)
    app.include_router(auth_router)
    app.include_router(users_router)
    app.include_router(documents_router)
    app.include_router(images_router)
    app.include_router(prompt_router)
    app.include_router(comfyui_router)
