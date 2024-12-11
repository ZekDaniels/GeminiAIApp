import logging
from app.services.integration_service import IntegrationService
from app.decorators.logging import log_execution

logger = logging.getLogger("app")


class PDFContentService:
    def __init__(self, integration_service=None):
        self.integration_service = integration_service or IntegrationService()

    @log_execution()
    async def fetch_pdf_content(self, integration_id, db):
        """Fetch the PDF content for a given Integration ID."""
        pdf = await self.integration_service.get_integration_by_id(integration_id, db)
        if not pdf.content:
            raise ValueError(f"PDF content is empty for Integration ID: {integration_id}")
        return pdf.content
