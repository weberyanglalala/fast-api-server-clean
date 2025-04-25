from fastapi import APIRouter
from .models import DocumentInput
from .service import convert_and_upload
from ..auth.service import CurrentUser

router = APIRouter(
    prefix="/documents",
    tags=["Documents"]
)

@router.post("/convert")
async def convert_document(doc: DocumentInput):
    return await convert_and_upload(doc)
