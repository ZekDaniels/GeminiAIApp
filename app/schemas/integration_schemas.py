from pydantic import BaseModel, ConfigDict
from datetime import datetime
from app.models.integration import ProcessingStatus

class UploadIntegrationResponse(BaseModel):
    integration_id: int
    filename: str
    processing_status: str = ProcessingStatus.PENDING

    model_config = ConfigDict(from_attributes=True)


class IntegrationResponse(BaseModel):
    id: int
    filename: str
    content_preview: str
    page_count: int
    updated_at: datetime
    processing_status: str

    @classmethod
    def from_model(cls, integration):
        """
        Converts a SQLAlchemy Integration model into a Pydantic IntegrationResponse model.
        """
        return cls(
            id=integration.id,
            filename=integration.filename,
            content_preview=integration.content[:100] if integration.content else "",
            page_count=integration.page_count,
            updated_at=integration.updated_at,
            processing_status=integration.processing_status,
        )

