from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    GEMINI_API_KEY: str
    DATABASE_URL: str = "sqlite+aiosqlite:///./pdf_chat.db"
    MAX_FILE_SIZE_MB: int = 20
    debug: bool = True
    log_level: str = "INFO"

    class Config:
        env_file = ".env"

settings = Settings()
