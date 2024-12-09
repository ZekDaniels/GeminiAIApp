from functools import wraps
from inspect import iscoroutinefunction
from fastapi import HTTPException, status
from app.errors.pdf_exceptions import PDFNotFoundException

from functools import wraps
from fastapi import HTTPException, status
from app.errors.pdf_exceptions import PDFNotFoundException

def handle_service_errors(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except PDFNotFoundException as e:
            raise e.to_http_exception()
        except HTTPException as e:
            raise e
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Internal Server Error: {str(e)}"
            )
    return wrapper

