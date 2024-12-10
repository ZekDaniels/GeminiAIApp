import pytest
import os
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import UploadFile
from io import BytesIO
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.integration_service import PDFService
from app.models.integration import PDF
from app.errors.integration_exceptions import IntegrationNotFoundException, PDFExtractionError
from fastapi import HTTPException

@pytest.fixture
def integration_service():
    """Fixture for the PDFService instance."""
    return PDFService()


@pytest.fixture
def sample_pdf_file():
    """Fixture for a mock UploadFile representing a PDF."""
    content = b"%PDF-1.4 mock content"  # Simulated minimal valid PDF content
    file = UploadFile(filename="test.pdf", file=BytesIO(content))
    return file


@pytest.fixture
def mock_db():
    """Fixture for mocking the database session."""
    mock_session = AsyncMock(spec=AsyncSession)
    return mock_session


# ----------------------------
# Tests for Validation
# ----------------------------

def test_validate_file_type_valid(integration_service, sample_pdf_file):
    """Test that valid file types pass validation."""
    integration_service._validate_file(sample_pdf_file)


def test_validate_file_type_invalid(integration_service):
    """Test that invalid file types raise an error."""
    invalid_file = UploadFile(filename="test.txt", file=BytesIO(b"Mock content"))
    with pytest.raises(Exception, match="Invalid file type"):
        integration_service._validate_file(invalid_file)


def test_validate_file_size_valid(integration_service, sample_pdf_file):
    """Test that files under the size limit pass validation."""
    integration_service._validate_file(sample_pdf_file)


@patch("aiofiles.open", new_callable=AsyncMock)
async def test_validate_file_size_invalid(mock_open, integration_service):
    """Test that files exceeding the size limit raise an error."""
    large_file = UploadFile(
        filename="large.pdf", 
        file=BytesIO(b"x" * (1024 * 1024 * 11))  # 11 MB file
    )
    integration_service.MAX_FILE_SIZE_MB = 10  # Ensure this matches your service's limit
    with pytest.raises(HTTPException, match="File size exceeds the limit"):
        integration_service.validate_file(large_file)


# ----------------------------
# Tests for File Operations
# ----------------------------

@patch("aiofiles.open", new_callable=AsyncMock)
async def test_save_pdf_to_disk(mock_open, integration_service, sample_pdf_file):
    mock_open.return_value.__aenter__.return_value.write = AsyncMock()
    file_path = await integration_service.save_pdf_to_disk(sample_pdf_file)
    assert os.path.exists(file_path)


@patch("asyncio.to_thread")
async def test_extract_text_from_pdf(mock_to_thread, integration_service):
    """Test text extraction from a PDF."""
    mock_to_thread.return_value = {"content": "Mock text", "page_count": 1}
    result = await integration_service._extract_text_from_pdf("test_path.pdf")
    assert result["content"] == "Mock text"
    assert result["page_count"] == 1
    mock_to_thread.assert_called_once()


# ----------------------------
# Tests for Database Operations
# ----------------------------

async def test_save_pdf_record(integration_service, mock_db):
    """Test saving a PDF record to the database."""
    mock_db.add = MagicMock()
    mock_db.commit = AsyncMock()
    mock_db.refresh = AsyncMock()

    integration_id = await integration_service._save_pdf_record("test.pdf", "Mock content", 5, mock_db)
    assert isinstance(integration_id, int)
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()


async def test_get_integration_by_id(integration_service, mock_db):
    """Test retrieving a PDF record by ID."""
    mock_pdf = PDF(id=1, filename="test.pdf", content="Mock", page_count=5)
    mock_db.execute.return_value.scalars.return_value.first.return_value = mock_pdf

    pdf = await integration_service.get_integration_by_id(1, mock_db)
    assert pdf.filename == "test.pdf"
    mock_db.execute.assert_called_once()


async def test_get_integration_by_id_not_found(integration_service, mock_db):
    """Test retrieving a non-existent PDF record."""
    mock_db.execute.return_value.scalars.return_value.first.return_value = None

    with pytest.raises(IntegrationNotFoundException):
        await integration_service.get_integration_by_id(999, mock_db)


# ----------------------------
# Tests for Integration
# ----------------------------

@patch("aiofiles.open", new_callable=AsyncMock)
@patch("asyncio.to_thread")
async def test_process_integration(mock_to_thread, mock_open, integration_service, sample_pdf_file, mock_db):
    mock_open.return_value.__aenter__.return_value.write = AsyncMock()
    mock_to_thread.return_value = {"content": "Mock text", "page_count": 1}
    mock_db.add = MagicMock()
    mock_db.commit = AsyncMock()
    mock_db.refresh = AsyncMock()

    integration_id = await integration_service.process_integration(sample_pdf_file, mock_db)
    assert isinstance(integration_id, int)


@patch("os.remove")
async def test_delete_integration(mock_remove, integration_service, mock_db):
    """Test deleting a PDF record and file."""
    mock_pdf = PDF(id=1, filename="test.pdf", content="Mock", page_count=5)
    mock_db.execute.return_value.scalars.return_value.first.return_value = mock_pdf
    mock_db.delete = AsyncMock()
    mock_db.commit = AsyncMock()

    await integration_service.delete_integration(1, mock_db)
    mock_remove.assert_called_once_with("uploads/pdf_files/test.pdf")
    mock_db.delete.assert_called_once_with(mock_pdf)
    mock_db.commit.assert_called_once()
