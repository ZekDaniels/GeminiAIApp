# app/schemas/pdf_schemas.py

from pydantic import BaseModel

class UploadPDFResponse(BaseModel):
    pdf_id: int
    filename: str

class ChatResponse(BaseModel):
    response: str
