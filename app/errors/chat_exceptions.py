class ChatServiceException(Exception):
    """Base exception for ChatService errors."""

class PDFContentNotFound(ChatServiceException):
    def __init__(self, integration_id: int):
        self.integration_id = integration_id
        self.message = f"Content not found for integration with id {integration_id}"
        super().__init__(self.message)
