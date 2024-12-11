import asyncio
import logging
import google.generativeai as genai
from app.core.config import settings
from app.decorators.logging import log_execution

logger = logging.getLogger("app")


class AIModelService:
    def __init__(self):
        """Initialize the AI Model Service."""
        api_key = settings.GEMINI_API_KEY
        if not api_key:
            raise ValueError("GEMINI_API_KEY is not configured.")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-1.5-flash")

    @log_execution()
    async def generate_response(self, prompt):
        """Generate a response from the AI model."""
        response = await asyncio.to_thread(self.model.generate_content, prompt)
        return response.text
