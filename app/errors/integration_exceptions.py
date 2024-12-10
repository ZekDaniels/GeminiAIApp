from fastapi import HTTPException, status

class PDFServiceException(Exception):
    """Base exception for all PDF service errors."""
    def __init__(self, message: str, http_status: int = status.HTTP_500_INTERNAL_SERVER_ERROR):
        self.message = message
        self.http_status = http_status
        super().__init__(self.message)

    def to_http_exception(self):
        """
        Convert the exception to a FastAPI HTTPException.
        """
        return HTTPException(status_code=self.http_status, detail=self.message)


class IntegrationNotFoundException(PDFServiceException):
    def __init__(self, integration_id: int):
        super().__init__(f"Integration with ID {integration_id} not found.", http_status=status.HTTP_404_NOT_FOUND)


class PDFExtractionError(PDFServiceException):
    def __init__(self, detail: str):
        super().__init__(f"Error extracting text from PDF: {detail}", http_status=status.HTTP_400_BAD_REQUEST)


class PDFSaveError(PDFServiceException):
    def __init__(self, detail: str):
        super().__init__(f"Error saving PDF: {detail}", http_status=status.HTTP_500_INTERNAL_SERVER_ERROR)
