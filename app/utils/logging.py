import os
from app.core.config import settings
from logging.config import dictConfig

LOG_LEVEL = "DEBUG" if settings.debug else settings.log_level


# Dynamic log level based on settin
def setup_logging():
    """
    Configure logging for the application, supporting rotating file handlers, JSON format, 
    and environment-based dynamic log levels.
    """
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)  # Ensure the logs directory exists
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            },
            "json": {
                "format": '{"timestamp": "%(asctime)s", "name": "%(name)s", "level": "%(levelname)s", "message": "%(message)s", "file": "%(pathname)s", "line": %(lineno)d}',
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "default",
            },
            "rotating_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "filename": os.path.join(log_dir, "app.log"),
                "maxBytes": 5 * 1024 * 1024,  # 5 MB
                "backupCount": 3,
                "formatter": "json",
            },
        },
        "loggers": {
            "uvicorn.error": {
                "level": LOG_LEVEL,
                "handlers": ["console", "rotating_file"],
                "propagate": False,
            },
            "uvicorn.access": {
                "level": LOG_LEVEL,
                "handlers": ["console", "rotating_file"],
                "propagate": False,
            },
            "app": {
                "level": LOG_LEVEL,
                "handlers": ["console", "rotating_file"],
                "propagate": False,
            },
        },
        "root": {
            "level": LOG_LEVEL,
            "handlers": ["console", "rotating_file"],
        },
    }
    dictConfig(logging_config)
