import tempfile
import os
import pypandoc
from fastapi import HTTPException
from .file_upload import upload_file_to_r2  # not used here, just for context

def convert_document(doc):
    binary_formats = ["docx", "pdf", "epub"]
    output_is_binary = doc.output_format in binary_formats
    file_extension = doc.output_format if doc.output_format != "html" else "html"
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
    return file_content, converted_content, content_type
