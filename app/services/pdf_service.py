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
from app.models.pdf import PDF
from app.errors.pdf_exceptions import PDFNotFoundException, PDFExtractionError
from app.decorators.pdf_handle_errors import handle_service_errors
from app.core.config import settings
from app.decorators.logging import log_execution

# Configure logger
logger = logging.getLogger("app")

class PDFService:
    # Constants
    UPLOAD_DIR = "uploads/pdf_files"
    MAX_FILE_SIZE_MB = settings.MAX_FILE_SIZE_MB
    ALLOWED_EXTENSIONS = {".pdf"}

    def __init__(self):
        """
        Initialize the PDF service and ensure the upload directory exists.
        """
        os.makedirs(self.UPLOAD_DIR, exist_ok=True)
        logger.info("PDFService initialized, upload directory: %s", self.UPLOAD_DIR)

    # ------------------------------
    # Public Methods
    # ------------------------------

    @handle_service_errors
    @log_execution()
    async def process_pdf(self, file: UploadFile, db: AsyncSession) -> int:
        """
        Process a PDF file: validate, save to disk, extract text, and save to database.

        Args:
            file (UploadFile): The uploaded PDF file.
            db (AsyncSession): Database session for saving records.

        Returns:
            int: The ID of the saved PDF record.
        """
        logger.info("Starting PDF processing for file: %s", file.filename)
        self._validate_file(file)
        file_path = await self._save_file_to_disk(file)
        pdf_data = await self._extract_text_from_pdf(file_path)
        preprocessed_content = self._preprocess_text(pdf_data["content"])
        unique_filename = self._generate_unique_filename(file.filename)
        pdf_id = await self._save_pdf_record(unique_filename, preprocessed_content, pdf_data["page_count"], db)
        logger.info("PDF processing completed successfully for file: %s", file.filename)
        return pdf_id

    @handle_service_errors
    @log_execution()
    async def update_pdf(self, pdf_id: int, file: UploadFile, db: AsyncSession) -> int:
        """
        Update an existing PDF record and replace its associated file.

        Args:
            pdf_id (int): ID of the PDF record to update.
            file (UploadFile): New PDF file to upload.
            db (AsyncSession): Database session for updating records.

        Returns:
            int: The updated PDF record ID.
        """
        logger.info("Updating PDF with ID: %d", pdf_id)
        self._validate_file(file)
        pdf_record = await self.get_pdf_by_id(pdf_id, db)
        await self._delete_file_from_disk(pdf_record.filename)

        new_file_path = await self._save_file_to_disk(file)
        pdf_data = await self._extract_text_from_pdf(new_file_path)
        preprocessed_content = self._preprocess_text(pdf_data["content"])

        pdf_record.filename = file.filename
        pdf_record.content = preprocessed_content
        pdf_record.page_count = pdf_data["page_count"]

        await db.commit()
        await db.refresh(pdf_record)
        logger.info("PDF updated successfully with ID: %d", pdf_id)
        return pdf_record.id

    @handle_service_errors
    @log_execution()
    async def delete_pdf(self, pdf_id: int, db: AsyncSession) -> None:
        """
        Delete a PDF record and its associated file from the system.

        Args:
            pdf_id (int): ID of the PDF record to delete.
            db (AsyncSession): Database session for deleting the record.
        """
        logger.info("Deleting PDF with ID: %d", pdf_id)
        pdf_record = await self.get_pdf_by_id(pdf_id, db)
        await self._delete_file_from_disk(pdf_record.filename)
        await db.delete(pdf_record)
        await db.commit()
        logger.info("PDF deleted successfully with ID: %d", pdf_id)

    @handle_service_errors
    @log_execution()
    async def list_pdfs(self, db: AsyncSession) -> list:
        """
        Retrieve all PDF records from the database.

        Args:
            db (AsyncSession): Database session for querying records.

        Returns:
            list: A list of PDF records.
        """
        logger.info("Fetching all PDF records from the database.")
        result = await db.execute(select(PDF))
        pdf_list = result.scalars().all()
        logger.info("Fetched %d PDF records.", len(pdf_list))
        return pdf_list

    @handle_service_errors
    @log_execution()
    async def get_pdf_by_id(self, pdf_id: int, db: AsyncSession) -> PDF:
        """
        Retrieve a specific PDF record by its ID.

        Args:
            pdf_id (int): The ID of the PDF to retrieve.
            db (AsyncSession): Database session for querying the record.

        Returns:
            PDF: The retrieved PDF record.

        Raises:
            PDFNotFoundException: If the PDF record is not found.
        """
        logger.info("Fetching PDF record with ID: %d", pdf_id)
        result = await db.execute(
            select(PDF).where(PDF.id == pdf_id).options(selectinload(PDF.conversation_history))
        )
        pdf_record = result.scalars().first()
        if not pdf_record:
            logger.warning("PDF record not found with ID: %d", pdf_id)
            raise PDFNotFoundException(pdf_id)
        logger.info("Fetched PDF record with ID: %d", pdf_id)
        return pdf_record

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

    async def _save_pdf_record(self, filename: str, content: str, page_count: int, db: AsyncSession) -> int:
        """Save PDF metadata to the database."""
        logger.debug("Saving PDF record to database: %s", filename)
        pdf_record = PDF(filename=filename, content=content, page_count=page_count)
        db.add(pdf_record)
        await db.commit()
        await db.refresh(pdf_record)
        logger.debug("PDF record saved with ID: %d", pdf_record.id)
        return pdf_record.id

    def _preprocess_text(self, text: str) -> str:
        """Clean and preprocess extracted text."""
        logger.debug("Preprocessing extracted text.")
        text = re.sub(r"\s+", " ", text)
        text = re.sub(r"[^a-zA-Z0-9\s,.?!]", "", text)
        processed_text = text.strip()
        logger.debug("Text preprocessing completed.")
        return processed_text
