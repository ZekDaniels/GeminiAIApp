import os

def validate_pdf(file):
    if not file.filename.endswith(".pdf"):
        raise ValueError("Invalid file type")
    if os.path.getsize(file.file.fileno()) > 10 * 1024 * 1024:  # 10 MB limit
        raise ValueError("File too large")
