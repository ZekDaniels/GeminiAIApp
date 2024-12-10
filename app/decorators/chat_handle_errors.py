from functools import wraps
from inspect import iscoroutinefunction
from fastapi import HTTPException, status
from app.errors.chat_exceptions import ChatServiceException

def handle_chat_service_errors(func):
    """
    Decorator to handle exceptions in ChatService methods.

    Args:
        func (function): The ChatService method to wrap.

    Returns:
        function: Wrapped function with error handling.
    """
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except ChatServiceException as e:
            # Raise the custom ChatServiceException as is
            raise e
        except HTTPException as e:
            # Pass through HTTPExceptions as is
            raise e
        except Exception as e:
            # Log and raise a generic HTTPException for unexpected errors
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Internal Server Error: {str(e)}"
            )

    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ChatServiceException as e:
            raise e
        except HTTPException as e:
            raise e
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Internal Server Error: {str(e)}"
            )

    # Check if the function is a coroutine
    return async_wrapper if iscoroutinefunction(func) else sync_wrapper
