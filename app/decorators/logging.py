from functools import wraps
import time
import logging
import asyncio

logger = logging.getLogger("app")

def log_execution(logger_name="app"):
    """
    Decorator to log execution details of methods in services, supporting both sync and async functions.

    Args:
        logger_name (str): Logger to use for logging.
    """
    logger = logging.getLogger(logger_name)

    def decorator(func):
        if asyncio.iscoroutinefunction(func):
            # Asynchronous function wrapper
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                start_time = time.time()
                logger.info(f"Starting {func.__name__} with args: {args}, kwargs: {kwargs}")
                try:
                    result = await func(*args, **kwargs)
                    elapsed_time = time.time() - start_time
                    logger.info(f"{func.__name__} executed successfully in {elapsed_time:.2f}s.")
                    return result
                except Exception as e:
                    logger.exception(f"Error in {func.__name__}: {e}")
                    raise

            return async_wrapper
        else:
            # Synchronous function wrapper
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                start_time = time.time()
                logger.info(f"Starting {func.__name__} with args: {args}, kwargs: {kwargs}")
                try:
                    result = func(*args, **kwargs)
                    elapsed_time = time.time() - start_time
                    logger.info(f"{func.__name__} executed successfully in {elapsed_time:.2f}s.")
                    return result
                except Exception as e:
                    logger.exception(f"Error in {func.__name__}: {e}")
                    raise

            return sync_wrapper

    return decorator
