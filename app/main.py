from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from app.routes import pdf, chat
from app.errors.pdf_exceptions import PDFNotFoundException


app = FastAPI(
    title="GeminiAIApp",
    description="Bu API, PDF yükleme ve sohbet özelliklerini sağlar.",
    version="1.0.0",
)
@app.exception_handler(PDFNotFoundException)
async def pdf_not_found_exception_handler(request: Request, exc: PDFNotFoundException):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"message": exc.message},
    )

# Register routes
app.include_router(pdf.router)
app.include_router(chat.router)