# GeminiAIApp
A FastAPI-based backend to upload, process PDFs, and chat using LLMs.

## Features
- Upload PDF files
- Chat functionality with PDFs
- Integrates with LLMs (e.g., Google Gemini API)

## Setup
1. Clone the repo.
2. Install dependencies: pip install -r requirements.txt
3. Run the server: uvicorn app.main:app --reload

## API Endpoints
- `POST /v1/pdf`: Upload a PDF file.
- `POST /v1/chat/{pdf_id}`: Chat with the content of the uploaded PDF.


pytest
pytest tests/pdf
pytest tests/pdf/test_services.py
pytest tests/pdf/test_services.py::test_save_pdf_to_disk

