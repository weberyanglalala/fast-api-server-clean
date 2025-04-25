import os
import boto3
from botocore.exceptions import ClientError
from fastapi import HTTPException
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

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

def upload_file_to_r2(file_name: str, file_content: bytes, content_type: str) -> str:
    try:
        s3_client.put_object(
            Bucket=R2_BUCKET_NAME,
            Key=file_name,
            Body=file_content,
            ContentType=content_type,
            ACL='public-read'
        )
        file_url = f"{R2_PUBLIC_URL}/{file_name}"
        logger.info(f"File uploaded to R2: {file_url}")
        return file_url
    except ClientError as e:
        logger.error(f"Failed to upload file to R2: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to upload to R2: {str(e)}")
