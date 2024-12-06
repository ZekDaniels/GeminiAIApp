import os
import pdfplumber
from fastapi import HTTPException
from app.models.pdf import PDF
from app.db.session import get_db
from sqlalchemy.orm import Session
from fastapi import UploadFile
from shutil import copyfileobj

async def process_pdf(file: UploadFile, db: Session) -> int:
    """
    Process the uploaded PDF file, extract its text content, save it to disk,
    and store the record in the database. Returns a unique PDF ID.
    """
    try:
        # Define a path to save the uploaded file
        upload_dir = "uploads/pdf_files"
        os.makedirs(upload_dir, exist_ok=True)  # Create the directory if it doesn't exist

        file_path = os.path.join(upload_dir, file.filename)

        # Save the file to the disk
        with open(file_path, "wb") as buffer:
            copyfileobj(file.file, buffer)

        # Extract text from the uploaded PDF
        with pdfplumber.open(file_path) as pdf:
            content = " ".join(page.extract_text() for page in pdf.pages if page.extract_text())

        if not content:
            raise HTTPException(status_code=400, detail="No text found in the PDF.")
        
        # Create and save the PDF record in the database
        pdf_record = PDF(filename=file.filename, content=content)
        db.add(pdf_record)
        db.commit()
        db.refresh(pdf_record)  # Refresh to get the ID
        
        return pdf_record.id  # Return the generated PDF ID
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing PDF: {str(e)}")
