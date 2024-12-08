class PDFNotFoundException(Exception):
    def __init__(self, pdf_id: int):
        self.pdf_id = pdf_id
        self.message = f"PDF with id {pdf_id} not found."
        super().__init__(self.message)
