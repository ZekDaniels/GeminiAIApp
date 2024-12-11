import asyncio
import logging
from google.api_core.exceptions import InvalidArgument, RetryError
import google.generativeai as genai
from app.core.config import settings
from app.decorators.logging import log_execution
from app.errors.chat_exceptions import AIModelError, RateLimitExceededError, TimeoutError

logger = logging.getLogger("app")


class AIModelService:
    def __init__(self):
        """Initialize the AI Model Service with settings from the configuration."""
        if not settings.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is not configured in the environment or .env file.")

        self.api_key = settings.GEMINI_API_KEY
        self.model_name = settings.AI_MODEL_NAME
        self.retry_attempts = settings.RETRY_ATTEMPTS
        self.timeout = settings.TIMEOUT_SECONDS

        # Configure the API key globally
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(self.model_name)

        logger.info(f"AIModelService initialized with model: {self.model_name}")

    @log_execution()
    async def generate_response(self, prompt):
        """
        Generate a response from the AI model with retry mechanism for rate limits and timeouts.

        Args:
            prompt (str): The prompt to send to the model.

        Returns:
            str: The model's response text.

        Raises:
            RateLimitExceededError: If the rate limit is exceeded after retries.
            TimeoutError: If the request times out after retries.
            AIModelError: For unexpected errors.
        """
        for attempt in range(1, self.retry_attempts + 1):
            try:
                logger.debug(f"Attempt {attempt}: Sending prompt to AI model.")
                response = await asyncio.wait_for(
                    asyncio.to_thread(self.model.generate_content, prompt),
                    timeout=self.timeout
                )
                return response.text
            except InvalidArgument as e:
                logger.error(f"Invalid API key or arguments: {e}")
                raise AIModelError("Invalid API key or arguments provided to the AI model.") from e
            except RetryError as e:
                logger.error(f"RetryError on attempt {attempt}: {e}")
                if attempt < self.retry_attempts:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                    continue
                raise RateLimitExceededError() from e
            except asyncio.TimeoutError:
                logger.error(f"TimeoutError on attempt {attempt}.")
                if attempt < self.retry_attempts:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                    continue
                raise TimeoutError()
            except Exception as e:
                logger.error(f"Unexpected error on attempt {attempt}: {e}")
                if attempt < self.retry_attempts:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                    continue
                raise AIModelError(f"Failed to generate a response: {e}") from e
