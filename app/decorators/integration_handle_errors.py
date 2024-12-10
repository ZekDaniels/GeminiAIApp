from functools import wraps
from inspect import iscoroutinefunction
from fastapi import HTTPException, status
from app.errors.integration_exceptions import IntegrationNotFoundException

from functools import wraps
from fastapi import HTTPException, status
from app.errors.integration_exceptions import IntegrationNotFoundException

def handle_integration_service_errors(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except IntegrationNotFoundException as e:
            raise e.to_http_exception()
        except HTTPException as e:
            raise e
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Internal Server Error: {str(e)}"
            )
    return wrapper

