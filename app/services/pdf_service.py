import pdfplumber

async def process_pdf(file):
    try:
        with pdfplumber.open(file.file) as pdf:
            content = " ".join([page.extract_text() for page in pdf.pages])
        return content
    except Exception as e:
        raise HTTPException(status_code=400, detail="Error processing PDF")
