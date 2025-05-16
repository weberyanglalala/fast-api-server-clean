from enum import Enum
from pydantic import BaseModel, validator

class FileType(str, Enum):
    HTML = "html"
    CSS = "css"
    JS = "js"
    
class DocumentInput(BaseModel):
    content: str
    input_format: str = "markdown"
    output_format: str = "html"

class CodeUploadInput(BaseModel):
    code: str
    filename: str
    file_type: FileType
    
    @validator("filename")
    def validate_filename_extension(cls, v, values):
        if "file_type" in values:
            expected_ext = values["file_type"].lower()
            if not v.lower().endswith(f".{expected_ext}"):
                return f"{v}.{expected_ext}"
        return v
