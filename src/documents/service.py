from datetime import datetime

from botocore.exceptions import ClientError
from fastapi import HTTPException
import logging

from src.utils.document_convert import convert_document
from src.utils.file_upload import upload_file_to_r2
from .models import DocumentInput


def convert_and_upload(doc: DocumentInput):
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_extension = doc.output_format if doc.output_format != "html" else "html"
        file_name = f"converted_{timestamp}.{file_extension}"

        file_content, converted_content, content_type = convert_document(doc)

        try:
            file_url = upload_file_to_r2(
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
                logging.info(f"Converted content: {converted_content[:100]}...")
            return response
        except ClientError as e:
            raise HTTPException(status_code=500, detail=f"Failed to upload to R2: {str(e)}")
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=f"Conversion failed: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
