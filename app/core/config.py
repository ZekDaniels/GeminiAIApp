from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    GEMINI_API_KEY: str
    DATABASE_URL: str = "sqlite+aiosqlite:///./pdf_chat.db"

    class Config:
        env_file = ".env"

settings = Settings()
