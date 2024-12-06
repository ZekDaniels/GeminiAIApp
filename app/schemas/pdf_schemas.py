# app/schemas/pdf_schemas.py

from pydantic import BaseModel

class UploadPDFResponse(BaseModel):
    pdf_id: int
    filename: str

class PDFResponse(BaseModel):
    id: int
    filename: str
    content: str

    class Config:
        orm_mode = True


class ChatResponse(BaseModel):
    response: str
