from fastapi import FastAPI
from app.core.config import settings
from app.routes import chat_route, pdf_route
from app.utils.error_handling import setup_exception_handling

app = FastAPI(
    title="GeminiAIApp",
    description="Bu API, PDF yükleme ve sohbet özelliklerini sağlar.",
    version="1.0.0",
)

setup_exception_handling(app)
if settings.debug:
    @app.get("/debug-info")
    async def debug_info():
        return {"message": "Debugging is enabled", "log_level": settings.log_level}

# Register routes
app.include_router(pdf_route.router)
app.include_router(chat_route.router)