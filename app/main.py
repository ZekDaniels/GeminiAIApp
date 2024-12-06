from fastapi import FastAPI
from app.routes import pdf

app = FastAPI(
    title="GeminiAIApp",
    description="Bu API, PDF yükleme ve sohbet özelliklerini sağlar.",
    version="1.0.0",
)

# Register routes
app.include_router(pdf.router)

@app.get("/", tags=["General"])
def read_root():
    """
    Root endpoint. API'nin çalıştığını kontrol etmek için kullanılır.
    """
    return {"message": "Welcome to the PDF Chat API"}