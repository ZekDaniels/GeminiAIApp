import logging
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from app.errors.pdf_exceptions import PDFNotFoundException

logger = logging.getLogger("uvicorn.error")

async def custom_error_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred. Please try again later."},
    )

def setup_exception_handling(app: FastAPI):
    @app.middleware("http")
    async def exception_handling_middleware(request: Request, call_next):
        try:
            return await call_next(request)
        except Exception as exc:
            return await custom_error_handler(request, exc)

@app.exception_handler(PDFNotFoundException)
async def pdf_not_found_exception_handler(request: Request, exc: PDFNotFoundException):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"message": exc.message},
    )