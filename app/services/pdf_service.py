import pdfplumber
from fastapi import HTTPException
from app.models.pdf import PDF
from app.db.session import get_db
from sqlalchemy.orm import Session

async def process_pdf(file, db: Session) -> int:
    """
    Process the uploaded PDF file, extract its text content, and save it to the database.
    Returns a unique PDF ID.
    """
    try:
        with pdfplumber.open(file.file) as pdf:
            content = " ".join(page.extract_text() for page in pdf.pages if page.extract_text())
        
        if not content:
            raise HTTPException(status_code=400, detail="No text found in the PDF.")
        
        # Create and save the PDF record to the database
        pdf_record = PDF(filename=file.filename, content=content)
        db.add(pdf_record)
        db.commit()
        db.refresh(pdf_record)  # Refresh to get the ID
        
        return pdf_record.id  # Return the generated PDF ID
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing PDF: {str(e)}")
