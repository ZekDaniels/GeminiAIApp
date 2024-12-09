import os
import re
import asyncio
import pdfplumber
import aiofiles
from fastapi import UploadFile, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from app.models.pdf import PDF
from app.errors.pdf_exceptions import PDFNotFoundException, PDFExtractionError
from app.decorators.pdf_handle_errors import handle_service_errors
import uuid


class PDFService:
    UPLOAD_DIR = "uploads/pdf_files"
    MAX_FILE_SIZE_MB = 10  # Maximum file size in megabytes
    ALLOWED_EXTENSIONS = {".pdf"}  # Allowed file extensions

    def __init__(self):
        """Initialize the service and create the upload directory if it doesn't exist."""
        self.upload_dir = self.UPLOAD_DIR
        os.makedirs(self.upload_dir, exist_ok=True)

    @handle_service_errors
    async def process_pdf(self, file: UploadFile, db: AsyncSession) -> int:
        """
        Process a PDF file: validate, save to disk, extract text, and save to database.
        """
        self.validate_file(file)
        file_path = await self.save_pdf_to_disk(file)
        pdf_data = await self.extract_text_from_pdf(file_path)
        preprocessed_content = self.preprocess_text(pdf_data["content"])
        pdf_id = await self.save_pdf_record(
            filename=self.generate_unique_filename(file.filename),
            content=preprocessed_content,
            page_count=pdf_data["page_count"],
            db=db
        )
        return pdf_id

    def validate_file(self, file: UploadFile):
        """
        Validate the uploaded file type and size.

        Raises:
            HTTPException: If the file is invalid (wrong type or too large).
        """
        # Validate file extension
        file_extension = os.path.splitext(file.filename)[1].lower()
        if file_extension not in self.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file type. Allowed types: {', '.join(self.ALLOWED_EXTENSIONS)}"
            )

        # Validate file size
        file.file.seek(0, os.SEEK_END)  # Move to the end of the file
        file_size_mb = file.file.tell() / (1024 * 1024)  # File size in MB
        file.file.seek(0)  # Reset the file pointer for further operations
        if file_size_mb > self.MAX_FILE_SIZE_MB:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File size exceeds the limit of {self.MAX_FILE_SIZE_MB} MB"
            )

    def generate_unique_filename(self, original_filename: str) -> str:
        """
        Generate a unique identifier for the PDF file based on the original filename.
        """
        unique_id = uuid.uuid4().hex  # Generate a unique ID
        file_extension = os.path.splitext(original_filename)[1]
        return f"{unique_id}{file_extension}"

    @handle_service_errors
    async def save_pdf_to_disk(self, file: UploadFile) -> str:
        """
        Save an uploaded PDF file to disk asynchronously with a unique filename.
        """
        unique_filename = self.generate_unique_filename(file.filename)
        file_path = os.path.join(self.upload_dir, unique_filename)
        async with aiofiles.open(file_path, "wb") as buffer:
            content = await file.read()  # Use async read
            await buffer.write(content)  # Async write
        return file_path

    @handle_service_errors
    async def extract_text_from_pdf(self, file_path: str) -> dict:
        """Extract text and metadata from a PDF file asynchronously."""
        return await asyncio.to_thread(self._sync_extract_text, file_path)

    def _sync_extract_text(self, file_path: str) -> dict:
        """Helper method for synchronous text extraction using pdfplumber."""
        with pdfplumber.open(file_path) as pdf:
            page_texts = [page.extract_text() for page in pdf.pages]
            content = " ".join(filter(None, page_texts))
            if not content.strip():
                raise PDFExtractionError("No extractable text found.")
            return {"content": content, "page_count": len(pdf.pages)}

    @handle_service_errors
    async def save_pdf_record(self, filename: str, content: str, page_count: int, db: AsyncSession) -> int:
        """Save a PDF record with metadata to the database."""
        pdf_record = PDF(filename=filename, content=content, page_count=page_count)
        db.add(pdf_record)
        await db.commit()
        await db.refresh(pdf_record)
        return pdf_record.id

    @handle_service_errors
    async def get_pdf_by_id(self, pdf_id: int, db: AsyncSession) -> PDF:
        """Retrieve a PDF record by its ID."""
        result = await db.execute(select(PDF).where(PDF.id == pdf_id).options(selectinload(PDF.conversation_history)))
        pdf_record = result.scalars().first()
        if not pdf_record:
            raise PDFNotFoundException(pdf_id)
        return pdf_record

    @handle_service_errors
    async def update_pdf(self, pdf_id: int, file: UploadFile, db: AsyncSession) -> int:
        """Update an existing PDF record and file."""
        pdf_record = await self.get_pdf_by_id(pdf_id, db)

        # Delete the old file
        old_file_path = os.path.join(self.upload_dir, pdf_record.filename)
        if os.path.exists(old_file_path):
            os.remove(old_file_path)

        # Save the new file and update the database record
        new_file_path = await self.save_pdf_to_disk(file)
        pdf_data = await self.extract_text_from_pdf(new_file_path)
        preprocessed_content = self.preprocess_text(pdf_data["content"])
        pdf_record.filename = file.filename
        pdf_record.content = preprocessed_content
        pdf_record.page_count = pdf_data["page_count"]
        await db.commit()
        await db.refresh(pdf_record)
        return pdf_record.id

    @handle_service_errors
    async def delete_pdf(self, pdf_id: int, db: AsyncSession) -> None:
        """Delete a PDF record and its associated file."""
        pdf_record = await self.get_pdf_by_id(pdf_id, db)
        file_path = os.path.join(self.upload_dir, pdf_record.filename)
        if os.path.exists(file_path):
            os.remove(file_path)
        await db.delete(pdf_record)
        await db.commit()

    @handle_service_errors
    async def list_pdfs(self, db: AsyncSession) -> list:
        """List all PDF records from the database."""
        result = await db.execute(select(PDF))
        return result.scalars().all()

    def preprocess_text(self, text: str) -> str:
        """Clean and preprocess extracted text."""
        text = re.sub(r"\s+", " ", text)
        text = re.sub(r"[^a-zA-Z0-9\s,.?!]", "", text)
        return text.strip()
