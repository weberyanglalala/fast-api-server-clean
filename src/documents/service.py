import os
from datetime import datetime
import tempfile
import pypandoc
import boto3
from botocore.exceptions import ClientError
from fastapi import HTTPException
from dotenv import load_dotenv
from .models import DocumentInput
from src.utils.file_upload import upload_file_to_r2
from src.utils.document_convert import convert_document  # new import

load_dotenv()

R2_ACCESS_KEY_ID = os.getenv("R2_ACCESS_KEY_ID")
R2_SECRET_ACCESS_KEY = os.getenv("R2_SECRET_ACCESS_KEY")
R2_ENDPOINT_URL = os.getenv("R2_ENDPOINT_URL")
R2_BUCKET_NAME = os.getenv("R2_BUCKET_NAME")
R2_PUBLIC_URL = os.getenv("R2_PUBLIC_URL")

s3_client = boto3.client(
    's3',
    aws_access_key_id=R2_ACCESS_KEY_ID,
    aws_secret_access_key=R2_SECRET_ACCESS_KEY,
    endpoint_url=R2_ENDPOINT_URL
)

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
            return response
        except ClientError as e:
            raise HTTPException(status_code=500, detail=f"Failed to upload to R2: {str(e)}")
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=f"Conversion failed: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
