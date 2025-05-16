from datetime import datetime

from botocore.exceptions import ClientError
from fastapi import HTTPException
import logging

from src.utils.document_convert import convert_document
from src.utils.file_upload import upload_file_to_r2
from .models import DocumentInput, CodeUploadInput, FileType

logger = logging.getLogger(__name__)


async def convert_and_upload(doc: DocumentInput):
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_extension = doc.output_format if doc.output_format != "html" else "html"
        file_name = f"converted_{timestamp}.{file_extension}"

        file_content, converted_content, content_type = convert_document(doc)

        try:
            file_url = await upload_file_to_r2(
                file_name=file_name,
                file_content=file_content,
                content_type=content_type
            )
            response = {
                "uploaded_file_url": file_url,
                "file_name": file_name
            }
            if converted_content is not None:
                response["converted_content"] = converted_content
            return response
        except ClientError as e:
            logger.error(f"Failed to upload file to R2: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to upload to R2: {str(e)}")
    except RuntimeError as e:
        logger.error(f"Document conversion failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Conversion failed: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error during conversion: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


async def upload_code(code_input: CodeUploadInput):
    """
    Upload code snippets (HTML, CSS, JavaScript) directly to storage
    
    Args:
        code_input: Contains code content, filename, and file type
        
    Returns:
        Dict containing uploaded file URL and filename
    """
    try:
        # Map file types to proper MIME types
        content_type_map = {
            FileType.HTML: "text/html",
            FileType.CSS: "text/css", 
            FileType.JS: "application/javascript"
        }
        
        content_type = content_type_map[code_input.file_type]
        
        # Convert code string to bytes
        file_content = code_input.code.encode("utf-8")
        
        # Upload to R2
        file_url = await upload_file_to_r2(
            file_name=code_input.filename,
            file_content=file_content,
            content_type=content_type
        )
        
        return {
            "uploaded_file_url": file_url,
            "file_name": code_input.filename
        }
    except ClientError as e:
        logger.error(f"Failed to upload code to R2: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to upload code to R2: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error during code upload: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
