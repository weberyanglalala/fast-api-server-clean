import os
from datetime import datetime
import tempfile
import pypandoc
import boto3
from botocore.exceptions import ClientError
from fastapi import HTTPException
from dotenv import load_dotenv
from .models import DocumentInput

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
        binary_formats = ["docx", "pdf", "epub"]
        output_is_binary = doc.output_format in binary_formats
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_extension = doc.output_format if doc.output_format != "html" else "html"
        file_name = f"converted_{timestamp}.{file_extension}"
        if output_is_binary:
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_extension}") as temp_file:
                output_path = temp_file.name
                pypandoc.convert_text(
                    doc.content,
                    to=doc.output_format,
                    format=doc.input_format,
                    outputfile=output_path
                )
                with open(output_path, 'rb') as f:
                    file_content = f.read()
                os.unlink(output_path)
            converted_content = None
        else:
            file_content = pypandoc.convert_text(
                doc.content,
                to=doc.output_format,
                format=doc.input_format
            ).encode('utf-8')
            converted_content = file_content.decode('utf-8', errors='ignore')
        content_type_map = {
            "html": "text/html",
            "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "pdf": "application/pdf",
            "epub": "application/epub+zip",
            "txt": "text/plain"
        }
        content_type = content_type_map.get(doc.output_format, "application/octet-stream")
        try:
            s3_client.put_object(
                Bucket=R2_BUCKET_NAME,
                Key=file_name,
                Body=file_content,
                ContentType=content_type,
                ACL='public-read'
            )
            file_url = f"{R2_PUBLIC_URL}/{file_name}"
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
