from fastapi import APIRouter, UploadFile, File, Depends, Path, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.schemas.pdf_schemas import UploadPDFResponse, PDFResponse
from app.services.pdf_service import PDFService
from app.db.session import get_db
from app.decorators.pdf_handle_errors import handle_service_errors

router = APIRouter(
    prefix="/v1/pdf",
    tags=["PDF"],
)
pdf_service = PDFService()


@router.post("/", response_model=UploadPDFResponse)
@handle_service_errors
async def upload_pdf(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    """
    Upload a PDF document. The PDF file is processed, and a unique ID is generated.
    
    - **file**: The PDF file to be uploaded.
    
    Returns a unique identifier (`pdf_id`) for the uploaded PDF.
    """
    # Await the process_pdf method since it's async
    pdf_id = await pdf_service.process_pdf(file, db)
    return UploadPDFResponse(pdf_id=pdf_id, filename=file.filename)


@router.put("/{pdf_id}", response_model=UploadPDFResponse)
@handle_service_errors
async def update_pdf(
    pdf_id: int = Path(..., title="PDF ID", description="The unique ID of the PDF to update"),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Update an existing PDF document with a new file.

    - **pdf_id**: The unique ID of the PDF to update.
    - **file**: The new PDF file to replace the old one.

    Returns the updated PDF metadata.
    """
    updated_pdf_id = await pdf_service.update_pdf(pdf_id, file, db)
    return UploadPDFResponse(pdf_id=updated_pdf_id, filename=file.filename)


@router.delete("/{pdf_id}", status_code=status.HTTP_204_NO_CONTENT)
@handle_service_errors
async def delete_pdf(
    pdf_id: int = Path(..., title="PDF ID", description="The unique ID of the PDF to delete"),
    db: AsyncSession = Depends(get_db),
):
    """
    Deletes a PDF record and its associated file.

    - **pdf_id**: Unique identifier of the PDF to delete.
    """
    await pdf_service.delete_pdf(pdf_id, db)
    return  # Status 204: No Content


@router.get("/", response_model=List[PDFResponse])
@handle_service_errors
async def list_pdfs(db: AsyncSession = Depends(get_db)):
    """
    List all uploaded PDFs.

    Returns a list of all PDFs with their metadata.
    """
    pdfs = await pdf_service.list_pdfs(db)  # Asenkron çağrı
    return [PDFResponse.from_model(pdf) for pdf in pdfs]

@router.get("/{pdf_id}", response_model=PDFResponse)
@handle_service_errors
async def get_pdf_by_id(pdf_id: int, db: AsyncSession = Depends(get_db)):
    """
    Retrieve details of a specific PDF.

    - **pdf_id**: Unique identifier of the PDF to retrieve.
    """
    pdf = await pdf_service.get_pdf_by_id(pdf_id, db)
    return PDFResponse(
        id=pdf.id,
        filename=pdf.filename,
        content_preview=pdf.content[:100],
        page_count=pdf.page_count,
        updated_at=pdf.updated_at,
        processing_status=pdf.processing_status,
    )