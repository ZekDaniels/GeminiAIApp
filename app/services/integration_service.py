import os
import re
import asyncio
import pdfplumber
import aiofiles
import uuid
import logging
from fastapi import UploadFile, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from app.models.integration import Integration
from app.errors.integration_exceptions import IntegrationNotFoundException, PDFExtractionError
from app.decorators.integration_handle_errors import handle_integration_service_errors
from app.core.config import settings
from app.decorators.logging import log_execution

# Configure logger
logger = logging.getLogger("app")

class IntegrationService:
    # Constants
    UPLOAD_DIR = "uploads/pdf_files"
    MAX_FILE_SIZE_MB = settings.MAX_FILE_SIZE_MB
    ALLOWED_EXTENSIONS = {".pdf"}

    def __init__(self):
        """
        Initialize the Integration service and ensure the upload directory exists.
        """
        os.makedirs(self.UPLOAD_DIR, exist_ok=True)
        logger.info("IntegrationService initialized, upload directory: %s", self.UPLOAD_DIR)

    # ------------------------------
    # Public Methods
    # ------------------------------

    @handle_integration_service_errors
    @log_execution()
    async def process_integration(self, file: UploadFile, db: AsyncSession) -> int:
        """
        Process a PDF file: validate, save to disk, extract text, and save to database.

        Args:
            file (UploadFile): The uploaded PDF file.
            db (AsyncSession): Database session for saving records.

        Returns:
            int: The ID of the saved Integration record.
        """
        logger.info("Starting Integration processing for file: %s", file.filename)
        self._validate_file(file)
        file_path = await self._save_file_to_disk(file)
        pdf_data = await self._extract_text_from_pdf(file_path)
        preprocessed_content = self._preprocess_text(pdf_data["content"])
        unique_filename = self._generate_unique_filename(file.filename)
        integration_id = await self._save_integration_record(unique_filename, preprocessed_content, pdf_data["page_count"], db)
        logger.info("Integration processing completed successfully for file: %s", file.filename)
        return integration_id

    @handle_integration_service_errors
    @log_execution()
    async def update_pdf(self, integration_id: int, file: UploadFile, db: AsyncSession) -> int:
        """
        Update an existing Integration record and replace its associated file.

        Args:
            integration_id (int): ID of the Integration record to update.
            file (UploadFile): New PDF file to upload.
            db (AsyncSession): Database session for updating records.

        Returns:
            int: The updated Integration record ID.
        """
        logger.info("Updating Integration with ID: %d", integration_id)
        self._validate_file(file)
        integration_record = await self.get_integration_by_id(integration_id, db)
        await self._delete_file_from_disk(integration_record.filename)

        new_file_path = await self._save_file_to_disk(file)
        pdf_data = await self._extract_text_from_pdf(new_file_path)
        preprocessed_content = self._preprocess_text(pdf_data["content"])

        integration_record.filename = file.filename
        integration_record.content = preprocessed_content
        integration_record.page_count = pdf_data["page_count"]

        await db.commit()
        await db.refresh(integration_record)
        logger.info("Integration updated successfully with ID: %d", integration_id)
        return integration_record.id

    @handle_integration_service_errors
    @log_execution()
    async def delete_integration(self, integration_id: int, db: AsyncSession) -> None:
        """
        Delete a Integration record and its associated file from the system.

        Args:
            integration_id (int): ID of the Integration record to delete.
            db (AsyncSession): Database session for deleting the record.
        """
        logger.info("Deleting Integration with ID: %d", integration_id)
        integration_record = await self.get_integration_by_id(integration_id, db)
        await self._delete_file_from_disk(integration_record.filename)
        await db.delete(integration_record)
        await db.commit()
        logger.info("Integration deleted successfully with ID: %d", integration_id)

    @handle_integration_service_errors
    @log_execution()
    async def list_integrations(self, db: AsyncSession) -> list:
        """
        Retrieve all Integration records from the database.

        Args:
            db (AsyncSession): Database session for querying records.

        Returns:
            list: A list of Integrations records.
        """
        logger.info("Fetching all Integration records from the database.")
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
            IntegrationNotFoundException: If the Integration record is not found.
        """
        logger.info("Fetching Integration record with ID: %d", integration_id)
        result = await db.execute(
            select(Integration).where(Integration.id == integration_id).options(selectinload(Integration.conversation_history))
        )
        integration_record = result.scalars().first()
        if not integration_record:
            logger.warning("Integration record not found with ID: %d", integration_id)
            raise IntegrationNotFoundException(integration_id)
        logger.info("Fetched Integration record with ID: %d", integration_id)
        return integration_record

    # ------------------------------
    # Private Helper Methods
    # ------------------------------

    def _validate_file(self, file: UploadFile):
        """Validate file extension and size."""
        file_extension = os.path.splitext(file.filename)[1].lower()
        if file_extension not in self.ALLOWED_EXTENSIONS:
            logger.error("Invalid file type: %s", file.filename)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file type. Allowed types: {', '.join(self.ALLOWED_EXTENSIONS)}"
            )

        file.file.seek(0, os.SEEK_END)
        file_size_mb = file.file.tell() / (1024 * 1024)
        file.file.seek(0)
        if file_size_mb > self.MAX_FILE_SIZE_MB:
            logger.error("File size exceeds limit for file: %s", file.filename)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File size exceeds the limit of {self.MAX_FILE_SIZE_MB} MB."
            )

    def _generate_unique_filename(self, original_filename: str) -> str:
        """Generate a unique filename using UUID."""
        unique_id = uuid.uuid4().hex
        file_extension = os.path.splitext(original_filename)[1]
        unique_filename = f"{unique_id}{file_extension}"
        logger.debug("Generated unique filename: %s", unique_filename)
        return unique_filename

    async def _save_file_to_disk(self, file: UploadFile) -> str:
        """Save the uploaded file to disk."""
        unique_filename = self._generate_unique_filename(file.filename)
        file_path = os.path.join(self.UPLOAD_DIR, unique_filename)
        async with aiofiles.open(file_path, "wb") as buffer:
            await buffer.write(await file.read())
        logger.debug("Saved file to disk: %s", file_path)
        return file_path

    async def _extract_text_from_pdf(self, file_path: str) -> dict:
        """Extract text and metadata from a PDF file."""
        logger.debug("Extracting text from PDF: %s", file_path)
        return await asyncio.to_thread(self._sync_extract_text, file_path)

    def _sync_extract_text(self, file_path: str) -> dict:
        """Synchronously extract text and metadata from a PDF."""
        logger.debug("Opening PDF file for text extraction: %s", file_path)
        with pdfplumber.open(file_path) as pdf:
            page_texts = [page.extract_text() for page in pdf.pages]
            content = " ".join(filter(None, page_texts))
            if not content.strip():
                logger.error("No extractable text found in PDF: %s", file_path)
                raise PDFExtractionError("No extractable text found.")
            logger.debug("Extracted text from PDF: %s", file_path)
            return {"content": content, "page_count": len(pdf.pages)}

    async def _delete_file_from_disk(self, filename: str):
        """Delete a file from disk."""
        file_path = os.path.join(self.UPLOAD_DIR, filename)
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.debug("Deleted file from disk: %s", file_path)
        else:
            logger.warning("File not found for deletion: %s", file_path)

    async def _save_integration_record(self, filename: str, content: str, page_count: int, db: AsyncSession) -> int:
        """Save Integration metadata to the database."""
        logger.debug("Saving Integration record to database: %s", filename)
        integration_record = Integration(filename=filename, content=content, page_count=page_count)
        db.add(integration_record)
        await db.commit()
        await db.refresh(integration_record)
        logger.debug("Integration record saved with ID: %d", integration_record.id)
        return integration_record.id

    def _preprocess_text(self, text: str) -> str:
        """Clean and preprocess extracted text."""
        logger.debug("Preprocessing extracted text.")
        text = re.sub(r"\s+", " ", text)
        text = re.sub(r"[^a-zA-Z0-9\s,.?!]", "", text)
        processed_text = text.strip()
        logger.debug("Text preprocessing completed.")
        return processed_text
