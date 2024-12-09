import os
import asyncio
import google.generativeai as genai
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.services.pdf_service import PDFService
from app.models.chat import ConversationHistory
from app.errors.chat_exceptions import ChatServiceException
from app.core.config import settings  # Import settings to get database URL


class ChatService:
    def __init__(self):
        """
        Initializes the ChatService with the Generative AI model and the PDFService.

        Raises:
            ValueError: If the GEMINI_API_KEY environment variable is not set.
        """
        api_key = settings.GEMINI_API_KEY
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is not set.")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-1.5-flash")
        self.pdf_service = PDFService()

    async def generate_response(
        self, pdf_id: int, user_query: str, db: AsyncSession, only_text: bool = False
    ) -> str:
        """
        Generates a response based on the user's query and the content of a specified PDF.

        Args:
            pdf_id (int): The unique identifier of the PDF.
            user_query (str): The user's input question or query.
            db (AsyncSession): The SQLAlchemy database session.
            only_text (bool, optional): Whether to include only conversation history. Defaults to False.

        Returns:
            str: The generated response text.

        Raises:
            ChatServiceException: If an error occurs during response generation.
        """
        try:
            pdf_content = await self._fetch_pdf_content(pdf_id, db)
            conversation_history = await self._fetch_conversation_history(pdf_id, db)
            prompt = self._construct_prompt(conversation_history, user_query, pdf_content, only_text)
            assistant_response = await self._generate_response_from_model(prompt)
            await self._save_conversation_history(pdf_id, user_query, assistant_response, db)
            return assistant_response
        except Exception as e:
            raise ChatServiceException(f"Error generating response: {str(e)}")

    async def _fetch_pdf_content(self, pdf_id: int, db: AsyncSession) -> str:
        """
        Retrieves the content of the specified PDF from the database.

        Args:
            pdf_id (int): The unique identifier of the PDF.
            db (AsyncSession): The SQLAlchemy database session.

        Returns:
            str: The content of the PDF.

        Raises:
            ValueError: If the PDF content is empty or not found.
        """
        pdf = await self.pdf_service.get_pdf_by_id(pdf_id, db)
        if not pdf.content:
            raise ValueError(f"PDF content is empty for PDF ID: {pdf_id}")
        return pdf.content

    async def _fetch_conversation_history(self, pdf_id: int, db: AsyncSession) -> list:
        """
        Retrieves the conversation history associated with the specified PDF ID.

        Args:
            pdf_id (int): The unique identifier of the PDF.
            db (AsyncSession): The SQLAlchemy database session.

        Returns:
            list: A list of ConversationHistory objects.
        """
        result = await db.execute(select(ConversationHistory).where(ConversationHistory.pdf_id == pdf_id))
        return result.scalars().all()

    def _construct_prompt(
        self, history: list, user_query: str, pdf_content: str, only_text: bool
    ) -> str:
        """
        Constructs the prompt to be sent to the Generative AI model.

        Args:
            history (list): The conversation history.
            user_query (str): The user's query.
            pdf_content (str): The content of the PDF.
            only_text (bool): Whether to include only the conversation history.

        Returns:
            str: The constructed prompt.
        """
        history_prompt = "\n".join(
            [f"User: {h.user_query}\nAssistant: {h.assistant_response}" for h in history]
        )
        if only_text:
            return f"{history_prompt}\nUser: {user_query}\n\nAssistant:"
        return f"{history_prompt}\nUser: {user_query}\n\nPDF Content:\n{pdf_content}\nAssistant:"

    async def _generate_response_from_model(self, prompt: str) -> str:
        """
        Sends the constructed prompt to the Generative AI model and retrieves the response.

        Args:
            prompt (str): The constructed prompt.

        Returns:
            str: The response from the AI model.
        """
        response = await asyncio.to_thread(self.model.generate_content, prompt)
        return response.text

    async def _save_conversation_history(
        self, pdf_id: int, user_query: str, assistant_response: str, db: AsyncSession
    ):
        """
        Saves the conversation history to the database.

        Args:
            pdf_id (int): The unique identifier of the PDF.
            user_query (str): The user's query.
            assistant_response (str): The response generated by the AI model.
            db (AsyncSession): The SQLAlchemy database session.
        """
        conversation_entry = ConversationHistory(
            pdf_id=pdf_id, user_query=user_query, assistant_response=assistant_response
        )
        db.add(conversation_entry)
        await db.commit()
