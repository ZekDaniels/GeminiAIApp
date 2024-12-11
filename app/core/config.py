from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    GEMINI_API_KEY: str
    AI_MODEL_NAME: str = "gemini-1.5-flash"
    RETRY_ATTEMPTS: int = 3
    TIMEOUT_SECONDS: int = 10
    DATABASE_URL: str = "sqlite+aiosqlite:///./pdf_chat.db"
    MAX_FILE_SIZE_MB: int = 20
    UPLOAD_DIR: str = "uploads/pdf_files"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"

settings = Settings()
