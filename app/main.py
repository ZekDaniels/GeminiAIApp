from fastapi import FastAPI
from app.routes import pdf, chat

app = FastAPI(
    title="GeminiAIApp",
    description="Bu API, PDF yükleme ve sohbet özelliklerini sağlar.",
    version="1.0.0",
)

# Register routes
app.include_router(pdf.router)
app.include_router(chat.router)