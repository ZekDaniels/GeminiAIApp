from functools import wraps
import logging

logger = logging.getLogger("app")

def handle_transaction():
    """
    Decorator to handle exceptions and ensure rollback on failure.
    Assumes the decorated function has an `AsyncSession` argument named `db`.
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Locate the `db` argument
            db = kwargs.get('db') or next((arg for arg in args if hasattr(arg, "rollback") and hasattr(arg, "commit")), None)
            if not db:
                raise ValueError("Database session (db) is required for transaction handling.")
            
            # Ensure transaction context
            async with db.begin():  # Explicitly start a transaction
                try:
                    result = await func(*args, **kwargs)
                    return result
                except Exception as e:
                    logger.error("An error occurred, rolling back transaction: %s", str(e))
                    # Rollback will be automatically handled by `db.begin()` context manager
                    raise
        return wrapper
    return decorator

