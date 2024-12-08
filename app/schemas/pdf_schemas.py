from pydantic import BaseModel, ConfigDict
from datetime import datetime

class UploadPDFResponse(BaseModel):
    pdf_id: int
    filename: str

    model_config = ConfigDict(from_attributes=True)


class PDFResponse(BaseModel):
    id: int
    filename: str
    content: str
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

