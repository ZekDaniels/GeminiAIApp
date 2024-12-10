import logging
from fastapi import UploadFile, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.services.file_service import FileHandler
from app.services.pdf_service import PDFProcessor
from app.models.integration import Integration
from app.decorators.integration_handle_errors import handle_integration_service_errors
from app.decorators.handle_transaction import handle_transaction
from app.decorators.logging import log_execution
from app.core.config import settings

logger = logging.getLogger("app")


class IntegrationService:
    """
    Manages PDF integrations, including file storage,
    text extraction, and database operations.
    """

    def __init__(self):
        self.file_handler = FileHandler(settings.UPLOAD_DIR)
        self.pdf_processor = PDFProcessor()

    @handle_transaction()
    @handle_integration_service_errors
    @log_execution()
    async def process_integration(self, file: UploadFile, db: AsyncSession) -> int:
        """Process a PDF file and save metadata."""
        self._validate_file(file)
        unique_filename = await self.file_handler.save_file(file)
        file_path = f"{settings.UPLOAD_DIR}/{unique_filename}"
        try:
            pdf_data = await self.pdf_processor.extract_text(file_path)
            content = self.pdf_processor.preprocess_text(pdf_data["content"])
            return await self._save_integration_record(unique_filename, content, pdf_data["page_count"], db)
        except Exception as e:
            logger.error("Error during integration processing.", exc_info=True)
            self.file_handler.delete_file(unique_filename)
            raise e

    @handle_transaction()
    @handle_integration_service_errors
    @log_execution()
    async def update_pdf(self, integration_id: int, file: UploadFile, db: AsyncSession) -> int:
        """Update an existing Integration record and replace its file."""
        integration_record = await self.get_integration_by_id(integration_id, db)
        backup_path = self.file_handler.backup_file(integration_record.filename)

        try:
            unique_filename = await self.file_handler.save_file(file)
            file_path = f"{settings.UPLOAD_DIR}/{unique_filename}"
            pdf_data = await self.pdf_processor.extract_text(file_path)
            content = self.pdf_processor.preprocess_text(pdf_data["content"])

            integration_record.filename = unique_filename
            integration_record.content = content
            integration_record.page_count = pdf_data["page_count"]
            await db.flush()
            self.file_handler.delete_file(backup_path)
            return integration_record.id
        except Exception as e:
            self.file_handler.restore_backup(backup_path, integration_record.filename)
            raise e

    @handle_transaction()
    @handle_integration_service_errors
    @log_execution()
    async def delete_integration(self, integration_id: int, db: AsyncSession) -> None:
        """
        Delete an Integration record and its associated file.

        Args:
            integration_id (int): ID of the Integration record to delete.
            db (AsyncSession): Database session for deleting the record.
        """
        logger.info("Deleting Integration with ID: %d", integration_id)
        integration_record = await self.get_integration_by_id(integration_id, db)
        self.file_handler.delete_file(integration_record.filename)
        await db.delete(integration_record)
        await db.flush()
        logger.info("Integration deleted successfully with ID: %d", integration_id)


    @handle_integration_service_errors
    @log_execution()
    async def list_integrations(self, db: AsyncSession) -> list[Integration]:
        """
        Retrieve all Integration records from the database.

        Args:
            db (AsyncSession): Database session for querying records.

        Returns:
            list[Integration]: A list of all Integration records.
        """
        logger.info("Fetching all Integration records.")
        result = await db.execute(select(Integration))
        integration_list = result.scalars().all()
        logger.info("Fetched %d Integration records.", len(integration_list))
        return integration_list
        
    @handle_integration_service_errors
    @log_execution()
    async def get_integration_by_id(self, integration_id: int, db: AsyncSession) -> Integration:
        """
        Retrieve a specific Integration record by its ID.

        Args:
            integration_id (int): The ID of the Integration to retrieve.
            db (AsyncSession): Database session for querying the record.

        Returns:
            Integration: The retrieved Integration record.

        Raises:
            HTTPException: If the Integration record is not found.
        """
        logger.info("Fetching Integration record with ID: %d", integration_id)
        result = await db.execute(select(Integration).where(Integration.id == integration_id))
        integration_record = result.scalars().first()

        if not integration_record:
            logger.warning("Integration record not found with ID: %d", integration_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Integration with ID {integration_id} not found."
            )

        logger.info("Fetched Integration record with ID: %d", integration_id)
        return integration_record

    @staticmethod
    def _validate_file(file: UploadFile):
        """Validate the file extension and size."""
        if file.filename.split('.')[-1].lower() != 'pdf':
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid file type. Only PDF allowed.")
        
    async def _save_integration_record(self, filename: str, content: str, page_count: int, db: AsyncSession) -> int:
        """
        Save Integration metadata to the database.

        Args:
            filename (str): The unique filename of the uploaded PDF.
            content (str): Extracted and preprocessed text content from the PDF.
            page_count (int): The number of pages in the PDF.
            db (AsyncSession): Database session for saving the record.

        Returns:
            int: The ID of the saved Integration record.
        """
        logger.info("Saving Integration record to the database: %s", filename)
        try:
            # Create a new Integration record
            integration_record = Integration(
                filename=filename,
                content=content,
                page_count=page_count
            )

            # Add and flush the record to the database
            db.add(integration_record)
            await db.flush()

            # Return the ID of the newly created record
            logger.info("Integration record saved with ID: %d", integration_record.id)
            return integration_record.id
        except Exception as e:
            logger.error("Error saving Integration record: %s", str(e), exc_info=True)
            raise Exception("Failed to save Integration record") from e
