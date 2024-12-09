from pydantic import BaseModel, ConfigDict
from datetime import datetime
from app.models.pdf import ProcessingStatus


class UploadPDFResponse(BaseModel):
    pdf_id: int
    filename: str
    processing_status: str = ProcessingStatus.PENDING

    model_config = ConfigDict(from_attributes=True)


from datetime import datetime
from pydantic import BaseModel

class PDFResponse(BaseModel):
    id: int
    filename: str
    content_preview: str
    page_count: int
    updated_at: datetime
    processing_status: str

    @classmethod
    def from_model(cls, pdf):
        """
        Converts a SQLAlchemy PDF model into a Pydantic PDFResponse model.
        """
        return cls(
            id=pdf.id,
            filename=pdf.filename,
            content_preview=pdf.content[:100] if pdf.content else "",
            page_count=pdf.page_count,
            updated_at=pdf.updated_at,
            processing_status=pdf.processing_status,
        )

