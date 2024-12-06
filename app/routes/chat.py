from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session
from typing import List

from app.schemas.pdf_schemas import ChatResponse
from app.models.pdf import PDF
from app.services.pdf_service import PDFService
from app.services.chat_service import get_gemini_response
from app.db.session import get_db

router = APIRouter(
    prefix="/v1/pdf",
    tags=["Chat"],
)
pdf_service = PDFService()

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
