from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.pdf_service import process_pdf

router = APIRouter()

@router.post("/v1/pdf")
async def upload_pdf(file: UploadFile = File(...)):
    pdf_id = await process_pdf(file)
    return {"pdf_id": pdf_id}

@router.post("/v1/chat/{pdf_id}")
async def chat_with_pdf(pdf_id: int, message: str):
    # Mock chat response
    return {"response": f"Answer based on PDF {pdf_id}"}
