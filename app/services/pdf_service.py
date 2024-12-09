import os
import re
import asyncio
import pdfplumber
import aiofiles
import uuid
from fastapi import UploadFile, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from app.models.pdf import PDF
from app.errors.pdf_exceptions import PDFNotFoundException, PDFExtractionError
from app.decorators.pdf_handle_errors import handle_service_errors
from app.core.config import settings  # Import settings for configurable limits


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

    # ------------------------------
    # Public Methods
    # ------------------------------

    @handle_service_errors
    async def process_pdf(self, file: UploadFile, db: AsyncSession) -> int:
        """
        Process a PDF file: validate, save to disk, extract text, and save to database.

        Args:
            file (UploadFile): The uploaded PDF file.
            db (AsyncSession): Database session for saving records.

        Returns:
            int: The ID of the saved PDF record.
        """
        self._validate_file(file)
        file_path = await self._save_file_to_disk(file)
        pdf_data = await self._extract_text_from_pdf(file_path)
        preprocessed_content = self._preprocess_text(pdf_data["content"])
        unique_filename = self._generate_unique_filename(file.filename)
        return await self._save_pdf_record(unique_filename, preprocessed_content, pdf_data["page_count"], db)

    @handle_service_errors
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
        self._validate_file(file)
        pdf_record = await self._get_pdf_by_id(pdf_id, db)
        await self._delete_file_from_disk(pdf_record.filename)

        new_file_path = await self._save_file_to_disk(file)
        pdf_data = await self._extract_text_from_pdf(new_file_path)
        preprocessed_content = self._preprocess_text(pdf_data["content"])

        pdf_record.filename = file.filename
        pdf_record.content = preprocessed_content
        pdf_record.page_count = pdf_data["page_count"]

        await db.commit()
        await db.refresh(pdf_record)
        return pdf_record.id

    @handle_service_errors
    async def delete_pdf(self, pdf_id: int, db: AsyncSession) -> None:
        """
        Delete a PDF record and its associated file from the system.

        Args:
            pdf_id (int): ID of the PDF record to delete.
            db (AsyncSession): Database session for deleting the record.
        """
        pdf_record = await self._get_pdf_by_id(pdf_id, db)
        await self._delete_file_from_disk(pdf_record.filename)
        await db.delete(pdf_record)
        await db.commit()

    @handle_service_errors
    async def list_pdfs(self, db: AsyncSession) -> list:
        """
        Retrieve all PDF records from the database.

        Args:
            db (AsyncSession): Database session for querying records.

        Returns:
            list: A list of PDF records.
        """
        result = await db.execute(select(PDF))
        return result.scalars().all()

    @handle_service_errors
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
        result = await db.execute(
            select(PDF).where(PDF.id == pdf_id).options(selectinload(PDF.conversation_history))
        )
        pdf_record = result.scalars().first()
        if not pdf_record:
            raise PDFNotFoundException(pdf_id)
        return pdf_record

    # ------------------------------
    # Private Helper Methods
    # ------------------------------

    def _validate_file(self, file: UploadFile):
        """Validate file extension and size."""
        file_extension = os.path.splitext(file.filename)[1].lower()
        if file_extension not in self.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file type. Allowed types: {', '.join(self.ALLOWED_EXTENSIONS)}"
            )

        file.file.seek(0, os.SEEK_END)
        file_size_mb = file.file.tell() / (1024 * 1024)
        file.file.seek(0)
        if file_size_mb > self.MAX_FILE_SIZE_MB:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File size exceeds the limit of {self.MAX_FILE_SIZE_MB} MB."
            )

    def _generate_unique_filename(self, original_filename: str) -> str:
        """Generate a unique filename using UUID."""
        unique_id = uuid.uuid4().hex
        file_extension = os.path.splitext(original_filename)[1]
        return f"{unique_id}{file_extension}"

    async def _save_file_to_disk(self, file: UploadFile) -> str:
        """Save the uploaded file to disk."""
        unique_filename = self._generate_unique_filename(file.filename)
        file_path = os.path.join(self.UPLOAD_DIR, unique_filename)
        async with aiofiles.open(file_path, "wb") as buffer:
            await buffer.write(await file.read())
        return file_path

    async def _extract_text_from_pdf(self, file_path: str) -> dict:
        """Extract text and metadata from a PDF file."""
        return await asyncio.to_thread(self._sync_extract_text, file_path)

    def _sync_extract_text(self, file_path: str) -> dict:
        """Synchronously extract text and metadata from a PDF."""
        with pdfplumber.open(file_path) as pdf:
            page_texts = [page.extract_text() for page in pdf.pages]
            content = " ".join(filter(None, page_texts))
            if not content.strip():
                raise PDFExtractionError("No extractable text found.")
            return {"content": content, "page_count": len(pdf.pages)}

    async def _delete_file_from_disk(self, filename: str):
        """Delete a file from disk."""
        file_path = os.path.join(self.UPLOAD_DIR, filename)
        if os.path.exists(file_path):
            os.remove(file_path)

    async def _save_pdf_record(self, filename: str, content: str, page_count: int, db: AsyncSession) -> int:
        """Save PDF metadata to the database."""
        pdf_record = PDF(filename=filename, content=content, page_count=page_count)
        db.add(pdf_record)
        await db.commit()
        await db.refresh(pdf_record)
        return pdf_record.id

    def _preprocess_text(self, text: str) -> str:
        """Clean and preprocess extracted text."""
        text = re.sub(r"\s+", " ", text)
        text = re.sub(r"[^a-zA-Z0-9\s,.?!]", "", text)
        return text.strip()
