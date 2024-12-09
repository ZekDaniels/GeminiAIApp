class ChatServiceException(Exception):
    """Base exception for ChatService errors."""

class PDFContentNotFound(ChatServiceException):
    def __init__(self, pdf_id: int):
        self.pdf_id = pdf_id
        self.message = f"Content not found for PDF with id {pdf_id}"
        super().__init__(self.message)
