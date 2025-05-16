from fastapi import APIRouter
from .models import DocumentInput, CodeUploadInput
from .service import convert_and_upload, upload_code
from ..auth.service import CurrentUser

router = APIRouter(
    prefix="/documents",
    tags=["Documents"]
)

@router.post("/convert")
async def convert_document(doc: DocumentInput):
    return await convert_and_upload(doc)

@router.post("/upload-code")
async def upload_code_endpoint(code_input: CodeUploadInput, current_user: CurrentUser = None):
    """
    Upload code snippets as HTML, CSS, or JavaScript files
    
    Parameters:
    - code: String content of the code to upload
    - filename: Name to save the file as (extension should match file_type)
    - file_type: Type of file (html, css, js)
    
    Returns:
    - uploaded_file_url: Public URL where the file can be accessed
    - file_name: Name of the uploaded file
    """
    return await upload_code(code_input)
