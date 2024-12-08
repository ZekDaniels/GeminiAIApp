from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Path, status
from sqlalchemy.orm import Session
from typing import List

from app.schemas.pdf_schemas import UploadPDFResponse, PDFResponse
from app.services.pdf_service import PDFService
from app.db.session import get_db
from app.errors.pdf_exceptions import PDFNotFoundException

router = APIRouter(
    prefix="/v1/pdf",
    tags=["PDF"],
)
pdf_service = PDFService()

@router.post("/", response_model=UploadPDFResponse)
async def upload_pdf(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Upload a PDF document. The PDF file is processed, and a unique ID is generated.
    
    - **file**: The PDF file to be uploaded.
    
    Returns a unique identifier (`pdf_id`) for the uploaded PDF.
    """
    try:
        pdf_id = pdf_service.process_pdf(file, db)
        return UploadPDFResponse(pdf_id=pdf_id, filename=file.filename)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal Server Error: {str(e)}")
    

@router.delete("/{pdf_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_pdf(pdf_id: int = Path(..., title="PDF ID", description="The unique ID of the PDF to delete"), db: Session = Depends(get_db)):
    """
    Deletes a PDF record and its associated file.

    - **pdf_id**: Unique identifier of the PDF to delete.
    """
    try:
        pdf_service.delete_pdf(pdf_id, db)
        return  # Status 204: No Content
    except PDFNotFoundException as e:
        raise e
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal Server Error: {str(e)}")
    

@router.get("/", response_model=List[PDFResponse])
async def list_pdfs(db: Session = Depends(get_db)):
    """
    List all uploaded PDFs.

    Returns a list of all PDFs with their metadata.
    """
    try:
        pdfs = pdf_service.list_pdfs(db)
        return pdfs
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal Server Error: {str(e)}")
    
@router.get("/{pdf_id}", response_model=PDFResponse)
async def get_pdf_by_id(pdf_id: int = Path(..., title="PDF ID", description="The unique ID of the PDF to retrieve"), db: Session = Depends(get_db)):
    """
    Retrieve details of a specific PDF.

    - **pdf_id**: Unique identifier of the PDF to retrieve.
    """
    try:
        pdf = pdf_service.get_pdf_by_id(pdf_id, db)
        return pdf
    except PDFNotFoundException as e:
        raise e
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {str(e)}")