from app.services.pdf_service import process_pdf

def test_pdf_processing():
    with open("sample.pdf", "rb") as f:
        content = process_pdf(f)
    assert "Expected Text" in content
