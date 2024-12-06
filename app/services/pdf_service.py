import os
import pdfplumber
from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session
from app.models.pdf import PDF
from shutil import copyfileobj

class PDFService:
    def __init__(self, upload_dir: str = "uploads/pdf_files"):
        """
        Initialize the PDFService.

        :param upload_dir: Directory where uploaded PDF files will be stored.
        """
        self.upload_dir = upload_dir
        os.makedirs(self.upload_dir, exist_ok=True)  # Ensure the directory exists

    def save_pdf_to_disk(self, file: UploadFile) -> str:
        """
        Save the uploaded PDF file to disk.

        :param file: The uploaded PDF file.
        :return: The file path where the PDF was saved.
        """
        try:
            file_path = os.path.join(self.upload_dir, file.filename)
            with open(file_path, "wb") as buffer:
                copyfileobj(file.file, buffer)
            return file_path
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error saving PDF to disk: {str(e)}")

    def extract_text_from_pdf(self, file_path: str) -> str:
        """
        Extract text from a PDF file.

        :param file_path: Path to the PDF file.
        :return: Extracted text content.
        """
        try:
            with pdfplumber.open(file_path) as pdf:
                content = " ".join(page.extract_text() for page in pdf.pages if page.extract_text())
            if not content:
                raise HTTPException(status_code=400, detail="No text found in the PDF.")
            return content
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error extracting text from PDF: {str(e)}")

    def save_pdf_record(self, filename: str, content: str, db: Session) -> int:
        """
        Save a PDF record in the database.

        :param filename: The filename of the PDF.
        :param content: The extracted text content of the PDF.
        :param db: SQLAlchemy database session.
        :return: The unique ID of the saved PDF record.
        """
        try:
            pdf_record = PDF(filename=filename, content=content)
            db.add(pdf_record)
            db.commit()
            db.refresh(pdf_record)  # Refresh to get the ID
            return pdf_record.id
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error saving PDF record: {str(e)}")

    def process_pdf(self, file: UploadFile, db: Session) -> int:
        """
        Process an uploaded PDF file: save to disk, extract text, and store in the database.

        :param file: The uploaded PDF file.
        :param db: SQLAlchemy database session.
        :return: The unique ID of the processed PDF.
        """
        file_path = self.save_pdf_to_disk(file)
        content = self.extract_text_from_pdf(file_path)
        pdf_id = self.save_pdf_record(file.filename, content, db)
        return pdf_id
    
    def delete_pdf(self, pdf_id: int, db: Session) -> None:
        """
        Deletes a PDF record from the database and its associated file from the disk.

        :param pdf_id: The unique ID of the PDF to delete.
        :param db: SQLAlchemy database session.
        """
        try:
            # Retrieve the PDF record from the database
            pdf_record = db.query(PDF).filter(PDF.id == pdf_id).first()
            if not pdf_record:
                raise HTTPException(status_code=404, detail="PDF not found.")

            # Construct the file path
            file_path = os.path.join(self.upload_dir, pdf_record.filename)

            # Delete the file from disk if it exists
            if os.path.exists(file_path):
                os.remove(file_path)

            # Delete the record from the database
            db.delete(pdf_record)
            db.commit()
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error deleting PDF: {str(e)}")

    def list_pdfs(self, db: Session) -> list:
        """
        Lists all PDFs stored in the database.

        :param db: SQLAlchemy database session.
        :return: A list of PDF records.
        """
        try:
            return db.query(PDF).all()
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error listing PDFs: {str(e)}")

    def get_pdf_by_id(self, pdf_id: int, db: Session) -> PDF:
        """
        Retrieves the details of a single PDF by its ID.

        :param pdf_id: The unique ID of the PDF.
        :param db: SQLAlchemy database session.
        :return: The PDF record.
        """
        try:
            pdf_record = db.query(PDF).filter(PDF.id == pdf_id).first()
            if not pdf_record:
                raise HTTPException(status_code=404, detail="PDF not found.")
            return pdf_record
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error retrieving PDF detail: {str(e)}")
