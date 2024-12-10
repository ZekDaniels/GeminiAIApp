from unittest.mock import patch, MagicMock
from app.services.pdf_service import PDFProcessor

@patch("pdfplumber.open")
def test_extract_text(mock_pdfplumber):
    # Create a mock for a single PDF page
    mock_page = MagicMock()
    mock_page.extract_text.return_value = "Test text"

    # Mock the behavior of pdfplumber.open
    mock_pdf = mock_pdfplumber.return_value.__enter__.return_value
    mock_pdf.pages = [mock_page]

    # Call the method under test
    result = PDFProcessor._sync_extract_text("test.pdf")

    # Assertions
    assert result["content"] == "Test text"
    assert result["page_count"] == 1
    mock_pdfplumber.assert_called_once_with("test.pdf")



def test_preprocess_text():
    text = "This is a   test! \n With spaces \t and \n newlines."
    processed_text = PDFProcessor.preprocess_text(text)
    assert processed_text == "This is a test! With spaces and newlines."
