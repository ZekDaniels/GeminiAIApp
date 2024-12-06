from pydantic import BaseSettings

class Settings(BaseSettings):
    gemini_api_key: str
    openai_api_key: str
    database_url: str = "sqlite:///./pdf_chat.db"

    class Config:
        env_file = ".env"

settings = Settings()
