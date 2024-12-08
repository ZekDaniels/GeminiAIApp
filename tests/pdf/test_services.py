import pytest
from unittest.mock import Mock
from app.services.pdf_service import PDFService
from fastapi.datastructures import UploadFile
from fpdf import FPDF
from fpdf.enums import XPos, YPos
from io import BytesIO
import os

@pytest.fixture
def pdf_service(tmp_path):
    return PDFService(upload_dir=str(tmp_path))

@pytest.fixture
def mock_db_session():
    return Mock()

def create_mock_upload_file(filename, content):
    return UploadFile(filename=filename, file=BytesIO(content))

def create_valid_pdf(file_path):
    """
    Creates a valid PDF file with text content for testing.
    """
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("helvetica", size=12)
    pdf.cell(200, 10, text="Sample PDF Content", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
    pdf.output(file_path)

def create_empty_pdf(file_path):
    """
    Creates a valid but empty PDF file for testing.
    """
    pdf = FPDF()
    pdf.add_page()
    pdf.output(file_path)

def test_save_pdf_to_disk_saves_file_correctly(pdf_service, tmp_path):
    """
    Test that save_pdf_to_disk saves a file to the specified directory.
    """
    file_content = b"Sample PDF content"
    mock_file = create_mock_upload_file("test.pdf", file_content)

    file_path = pdf_service.save_pdf_to_disk(mock_file)

    assert os.path.exists(file_path)
    assert file_path.endswith("test.pdf")

    with open(file_path, "rb") as f:
        assert f.read() == file_content

def test_extract_text_from_pdf_returns_text(pdf_service, tmp_path):
    """
    Test that extract_text_from_pdf extracts text from a valid PDF file.
    """
    test_file_path = tmp_path / "test.pdf"
    create_valid_pdf(test_file_path)

    text = pdf_service.extract_text_from_pdf(str(test_file_path))
    assert "Sample PDF Content" in text

def test_extract_text_from_empty_pdf_raises_error(pdf_service, tmp_path):
    """
    Test that extract_text_from_pdf raises an error for an empty PDF file.
    """
    test_file_path = tmp_path / "empty.pdf"
    create_empty_pdf(test_file_path)

    with pytest.raises(Exception) as exc_info:
        pdf_service.extract_text_from_pdf(str(test_file_path))
    assert "No text found" in str(exc_info.value)

def test_delete_pdf_removes_file_and_record(pdf_service, mock_db_session, mocker, tmp_path):
    """
    Test that delete_pdf removes the file from disk and deletes the database record.
    """
    # Create a valid file
    test_file_path = tmp_path / "test.pdf"
    with open(test_file_path, "wb") as f:
        f.write(b"Sample PDF content")

    # Mock database record
    pdf_record = Mock()
    pdf_record.filename = "test.pdf"
    mock_db_session.query().filter().first.return_value = pdf_record

    # Mock os.remove
    mock_remove = mocker.patch("os.remove")

    # Test delete functionality
    pdf_service.delete_pdf(1, mock_db_session)

    # Assertions
    mock_db_session.delete.assert_called_once_with(pdf_record)
    mock_db_session.commit.assert_called_once()
    mock_remove.assert_called_once_with(str(test_file_path))


