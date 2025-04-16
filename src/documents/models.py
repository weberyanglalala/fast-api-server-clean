from pydantic import BaseModel

class DocumentInput(BaseModel):
    content: str
    input_format: str = "markdown"
    output_format: str = "html"
