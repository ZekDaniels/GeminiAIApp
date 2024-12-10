import logging
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from app.errors.integration_exceptions import IntegrationNotFoundException

logger = logging.getLogger("uvicorn.error")

async def custom_error_handler(request: Request, exc: Exception):
    """
    Handle unexpected errors globally and log them.
    """
    logger.exception(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred. Please try again later."},
    )

async def integration_not_found_exception_handler(request: Request, exc: IntegrationNotFoundException):
    """
    Handle IntegrationNotFoundException with a custom message.
    """
    logger.warning(f"Integration not found: {exc.message}")
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"message": exc.message},
    )

def setup_exception_handling(app: FastAPI):
    """
    Setup middleware and custom exception handlers for the FastAPI app.
    """
    @app.middleware("http")
    async def exception_handling_middleware(request: Request, call_next):
        try:
            return await call_next(request)
        except Exception as exc:
            return await custom_error_handler(request, exc)

    # Register custom exception handlers
    app.add_exception_handler(IntegrationNotFoundException, integration_not_found_exception_handler)
