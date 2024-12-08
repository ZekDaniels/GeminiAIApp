import os
import google.generativeai as genai
from sqlalchemy.orm import Session
from app.services.pdf_service import PDFService
from app.models.chat import ConversationHistory

class ChatService:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is not set.")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        self.pdf_service = PDFService()

    def generate_response(self, pdf_id: int, user_query: str, db: Session, only_text: bool = False) -> str:
        """
        Generates a response based on the user's query and the content of a specified PDF.

        Args:
            pdf_id (int): The unique identifier of the PDF.
            user_query (str): The user's input question or query.
            db (Session): The SQLAlchemy database session.
            only_text (bool, optional): Whether to only generate text response. Defaults to False.

        Returns:
            str: The generated response text.

        Raises:
            ValueError: If the PDF content is not found.
        """
        # Retrieve PDF content from the database
        pdf = self.pdf_service.get_pdf_by_id(pdf_id, db)
        history = db.query(ConversationHistory).filter(ConversationHistory.pdf_id == pdf_id).all()
        history_prompt = "\n".join([f"User: {h.user_query}\nAssistant: {h.assistant_response}" for h in history])

        # Construct the prompt with user query and PDF content
        if only_text:
            prompt = f"{history_prompt}\nUser: {user_query}\n\nAssistant:"
        else:
            prompt = f"{history_prompt}\nUser: {user_query}\n\nPDF Content:\n{pdf.content}\nAssistant:"

        # Send request to Gemini API
        response = self.model.generate_content(prompt)

         # Generate response
        assistant_response = response.text

        # Save conversation history
        conversation_entry = ConversationHistory(
            pdf_id=pdf_id,
            user_query=user_query,
            assistant_response=assistant_response
        )
        db.add(conversation_entry)
        db.commit()

        return assistant_response