from fastapi import APIRouter, UploadFile, File, Depends, Path, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.schemas.integration_schemas import UploadIntegrationResponse, IntegrationResponse
from app.services.integration_service import IntegrationService
from app.db.session import get_db
from app.decorators.integration_handle_errors import handle_service_errors

router = APIRouter(
    prefix="/v1/integration",
    tags=["Integration"],
)
integration_service = IntegrationService()


@router.post("/", response_model=UploadIntegrationResponse)
@handle_service_errors
async def create_integration(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    """
    Create the inrgeration. The PDF file is processed, and a unique ID is generated.
    
    - **file**: The PDF file to be uploaded.
    
    Returns a unique identifier (`integration_id`) for the uploaded PDF.
    """
    # Await the process_integration method since it's async
    integration_id = await integration_service.process_integration(file, db)
    return UploadIntegrationResponse(integration_id=integration_id, filename=file.filename)


@router.put("/{integration_id}", response_model=UploadIntegrationResponse)
@handle_service_errors
async def update_pdf(
    integration_id: int = Path(..., title="Integration ID", description="The unique ID of the Integration to update"),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Update an existing Integration document with a new file.

    - **integration_id**: The unique ID of the Integration to update.
    - **file**: The new PDF file to replace the old one.

    Returns the updated Integration metadata.
    """
    updated_integration_id = await integration_service.update_pdf(integration_id, file, db)
    return UploadIntegrationResponse(integration_id=updated_integration_id, filename=file.filename)


@router.delete("/{integration_id}", status_code=status.HTTP_204_NO_CONTENT)
@handle_service_errors
async def delete_integration(
    integration_id: int = Path(..., title="Integration ID", description="The unique ID of the Integration to delete"),
    db: AsyncSession = Depends(get_db),
):
    """
    Deletes a Integration record and its associated file.

    - **integration_id**: Unique identifier of the Integration to delete.
    """
    await integration_service.delete_integration(integration_id, db)
    return  # Status 204: No Content


@router.get("/", response_model=List[IntegrationResponse])
@handle_service_errors
async def list_integrations(db: AsyncSession = Depends(get_db)):
    """
    List all saved Integrations.

    Returns a list of all Integrations with their metadata.
    """
    pdfs = await integration_service.list_integrations(db)  # Asenkron çağrı
    return [IntegrationResponse.from_model(pdf) for pdf in pdfs]

@router.get("/{integration_id}", response_model=IntegrationResponse)
@handle_service_errors
async def get_integration_by_id(integration_id: int, db: AsyncSession = Depends(get_db)):
    """
    Retrieve details of a specific Integration.

    - **integration_id**: Unique identifier of the Integration to retrieve.
    """
    pdf = await integration_service.get_integration_by_id(integration_id, db)
    return IntegrationResponse(
        id=pdf.id,
        filename=pdf.filename,
        content_preview=pdf.content[:100],
        page_count=pdf.page_count,
        updated_at=pdf.updated_at,
        processing_status=pdf.processing_status,
    )