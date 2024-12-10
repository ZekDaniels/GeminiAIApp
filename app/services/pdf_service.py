import re
import pdfplumber
import asyncio
import logging

logger = logging.getLogger("app")


class PDFProcessor:
    """
    Handles PDF-related operations such as text extraction
    and preprocessing.
    """

    @staticmethod
    async def extract_text(file_path: str) -> dict:
        """Extract text and metadata from a PDF file."""
        return await asyncio.to_thread(PDFProcessor._sync_extract_text, file_path)

    @staticmethod
    def _sync_extract_text(file_path: str) -> dict:
        """Synchronously extract text and metadata from a PDF."""
        with pdfplumber.open(file_path) as pdf:
            page_texts = [page.extract_text() for page in pdf.pages]
            content = " ".join(filter(None, page_texts))
            if not content.strip():
                logger.error("No extractable text found in PDF: %s", file_path)
                raise Exception("No extractable text found.")
            return {"content": content, "page_count": len(pdf.pages)}

    @staticmethod
    def preprocess_text(text: str) -> str:
        """Clean and preprocess extracted text."""
        text = re.sub(r"\s+", " ", text)
        text = re.sub(r"[^a-zA-Z0-9\s,.?!]", "", text)
        return text.strip()
