import os
import re
import asyncio
import pdfplumber
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from app.models.pdf import PDF
from app.errors.pdf_exceptions import PDFNotFoundException, PDFExtractionError
from app.decorators.pdf_handle_errors import handle_service_errors
import aiofiles


class PDFService:
    def __init__(self, upload_dir: str = "uploads/pdf_files"):
        """Initialize the service and create the upload directory if not exists."""
        self.upload_dir = upload_dir
        os.makedirs(self.upload_dir, exist_ok=True)

    @handle_service_errors
    async def process_pdf(self, file: UploadFile, db: AsyncSession) -> int:
        """Process a PDF file: save to disk, extract text, and save to database."""
        file_path = await self.save_pdf_to_disk(file)
        pdf_data = await self.extract_text_from_pdf(file_path)
        preprocessed_content = self.preprocess_text(pdf_data["content"])
        pdf_id = await self.save_pdf_record(file.filename, preprocessed_content, pdf_data["page_count"], db)
        return pdf_id

    @handle_service_errors
    async def save_pdf_to_disk(self, file: UploadFile) -> str:
        """Save an uploaded PDF file to disk asynchronously."""
        file_path = os.path.join(self.upload_dir, file.filename)
        async with aiofiles.open(file_path, "wb") as buffer:
            content = await file.read()  # Use async read
            await buffer.write(content)
        return file_path

    @handle_service_errors
    async def extract_text_from_pdf(self, file_path: str) -> dict:
        """Extract text and metadata from a PDF file asynchronously."""
        return await asyncio.to_thread(self._sync_extract_text, file_path)

    def _sync_extract_text(self, file_path: str) -> dict:
        """Synchronous helper method for extracting text using pdfplumber."""
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
