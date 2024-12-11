class ChatServiceException(Exception):
    """Base exception for ChatService errors."""

class PDFContentNotFound(ChatServiceException):
    def __init__(self, integration_id: int):
        self.integration_id = integration_id
        self.message = f"Content not found for integration with id {integration_id}"
        super().__init__(self.message)

class AIModelError(ChatServiceException):
    """Exception raised for AI Model errors."""
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

class RateLimitExceededError(AIModelError):
    """Exception raised for exceeding rate limits."""
    def __init__(self):
        super().__init__("Rate limit exceeded. Please try again later.")

class TimeoutError(AIModelError):
    """Exception raised for request timeouts."""
    def __init__(self):
        super().__init__("The request to the AI model timed out. Please try again later.")
