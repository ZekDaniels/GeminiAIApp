from fastapi import FastAPI
from app.core.config import settings
from app.routes import chat_route, integration_route
from app.utils.error_handling import setup_exception_handling
from app.utils.logging import setup_logging
app = FastAPI(
    title="GeminiAIApp",
    description="Bu API, AI ile LLM entegrasyonu e PDF dosyalarını yükleme ve sohbet özelliklerini sağlar.",
    version="1.0.0",
)

setup_logging()
setup_exception_handling(app)
if settings.DEBUG:
    @app.get("/debug-info")
    async def debug_info():
        return {"message": "Debugging is enabled", "LOG_LEVEL": settings.LOG_LEVEL}

# Register routes
app.include_router(integration_route.router)
app.include_router(chat_route.router)