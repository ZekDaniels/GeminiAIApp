from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Path
from sqlalchemy.orm import Session
from typing import List

from app.schemas.pdf_schemas import UploadPDFResponse, PDFResponse, ChatResponse
from app.models.pdf import PDF
from app.services.pdf_service import PDFService
from app.services.chat_service import get_gemini_response
from app.db.session import get_db

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
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
    

@router.delete("/{pdf_id}", status_code=204)
async def delete_pdf(pdf_id: int = Path(..., title="PDF ID", description="The unique ID of the PDF to delete"), db: Session = Depends(get_db)):
    """
    Deletes a PDF record and its associated file.

    - **pdf_id**: Unique identifier of the PDF to delete.
    """
    try:
        pdf_service.delete_pdf(pdf_id, db)
        return  # Status 204: No Content
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
    

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
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
    
@router.get("/{pdf_id}", response_model=PDFResponse)
async def get_pdf_detail(pdf_id: int = Path(..., title="PDF ID", description="The unique ID of the PDF to retrieve"), db: Session = Depends(get_db)):
    """
    Retrieve details of a specific PDF.

    - **pdf_id**: Unique identifier of the PDF to retrieve.
    """
    try:
        pdf_detail = pdf_service.get_pdf_detail(pdf_id, db)
        return pdf_detail
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")


@router.post("/chat/{pdf_id}", response_model=ChatResponse)
async def chat_with_pdf(pdf_id: int, message: str, db: Session = Depends(get_db)):
    """
    Chat with the content of a PDF document. The user can send queries related to the PDF.
    
    - **pdf_id**: The unique identifier of the PDF.
    - **message**: The query message to ask the AI about the PDF content.
    
    Returns an AI-generated response based on the content of the PDF.
    """
    try:
        # Retrieve PDF content from the database
        pdf_content = db.query(PDF).filter(PDF.id == pdf_id).first()
        if not pdf_content:
            raise HTTPException(status_code=404, detail="PDF not found.")

        # Query Gemini API for response
        response = get_gemini_response(pdf_content.content, message)
        return ChatResponse(response=response['answer'])
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
