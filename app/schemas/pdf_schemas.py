from pydantic import BaseModel, ConfigDict

class UploadPDFResponse(BaseModel):
    pdf_id: int
    filename: str

    model_config = ConfigDict(from_attributes=True)


class PDFResponse(BaseModel):
    id: int
    filename: str
    content: str

    model_config = ConfigDict(from_attributes=True)


class ChatResponse(BaseModel):
    response: str

    model_config = ConfigDict()
