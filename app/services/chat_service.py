import os
import asyncio
import logging
import google.generativeai as genai
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.services.pdf_service import PDFService
from app.models.chat import ConversationHistory
from app.errors.chat_exceptions import ChatServiceException
from app.decorators.chat_handle_errors import handle_chat_service_errors
from app.decorators.logging import log_execution
from app.core.config import settings

# Configure logger
logger = logging.getLogger("app")


class ChatService:
    def __init__(self):
        """
        Initializes the ChatService with the Generative AI model and the PDFService.

        Raises:
            ValueError: If the GEMINI_API_KEY environment variable is not set.
        """
        api_key = settings.GEMINI_API_KEY
        if not api_key:
            logger.error("GEMINI_API_KEY environment variable is not set.")
            raise ValueError("GEMINI_API_KEY environment variable is not set.")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-1.5-flash")
        self.pdf_service = PDFService()
        logger.info("ChatService initialized with Generative AI model: gemini-1.5-flash")

    @handle_chat_service_errors
    @log_execution()
    async def generate_response(
        self, pdf_id: int, user_query: str, db: AsyncSession, only_text: bool = False
    ) -> str:
        """
        Generate a response to a user query based on the content of a specified PDF.

        Args:
            pdf_id (int): The unique identifier of the PDF.
            user_query (str): The user's question or query.
            db (AsyncSession): The database session.
            only_text (bool, optional): Whether to exclude PDF content from the prompt. Defaults to False.

        Returns:
            str: The assistant's response.
        """
        logger.info("Generating response for PDF ID: %d, User Query: %s", pdf_id, user_query)
        pdf_content = await self._fetch_pdf_content(pdf_id, db)
        conversation_history = await self._fetch_conversation_history(pdf_id, db)
        prompt = self._construct_prompt(conversation_history, user_query, pdf_content, only_text)
        assistant_response = await self._generate_response_from_model(prompt)
        await self._save_conversation_history(pdf_id, user_query, assistant_response, db)
        logger.info("Response successfully generated for PDF ID: %d", pdf_id)
        return assistant_response

    @handle_chat_service_errors
    @log_execution()
    async def _fetch_pdf_content(self, pdf_id: int, db: AsyncSession) -> str:
        """
        Fetch the content of the specified PDF from the database.

        Args:
            pdf_id (int): The unique identifier of the PDF.
            db (AsyncSession): The database session.

        Returns:
            str: The content of the PDF.

        Raises:
            ValueError: If the PDF content is empty.
        """
        logger.debug("Fetching PDF content for PDF ID: %d", pdf_id)
        pdf = await self.pdf_service.get_pdf_by_id(pdf_id, db)
        if not pdf.content:
            logger.error("PDF content is empty for PDF ID: %d", pdf_id)
            raise ValueError(f"PDF content is empty for PDF ID: {pdf_id}")
        return pdf.content

    @handle_chat_service_errors
    @log_execution()
    async def _fetch_conversation_history(self, pdf_id: int, db: AsyncSession) -> list:
        """
        Fetch the conversation history for a specified PDF ID.

        Args:
            pdf_id (int): The unique identifier of the PDF.
            db (AsyncSession): The database session.

        Returns:
            list: A list of ConversationHistory objects.
        """
        logger.debug("Fetching conversation history for PDF ID: %d", pdf_id)
        result = await db.execute(select(ConversationHistory).where(ConversationHistory.pdf_id == pdf_id))
        history = result.scalars().all()
        logger.debug("Fetched %d conversation history entries for PDF ID: %d", len(history), pdf_id)
        return history

    @log_execution()
    def _construct_prompt(
        self, history: list, user_query: str, pdf_content: str, only_text: bool
    ) -> str:
        """
        Construct the prompt for the Generative AI model.

        Args:
            history (list): The conversation history.
            user_query (str): The user's query.
            pdf_content (str): The PDF content.
            only_text (bool): Whether to exclude the PDF content.

        Returns:
            str: The constructed prompt.
        """
        logger.debug("Constructing prompt for AI model.")
        history_prompt = "\n".join(
            [f"User: {h.user_query}\nAssistant: {h.assistant_response}" for h in history]
        )
        if only_text:
            return f"{history_prompt}\nUser: {user_query}\n\nAssistant:"
        return f"{history_prompt}\nUser: {user_query}\n\nPDF Content:\n{pdf_content}\nAssistant:"


    @log_execution()
    async def _generate_response_from_model(self, prompt: str) -> str:
        """
        Send the constructed prompt to the Generative AI model and retrieve the response.

        Args:
            prompt (str): The constructed prompt.

        Returns:
            str: The response from the AI model.
        """
        logger.debug("Sending prompt to Generative AI model.")
        response = await asyncio.to_thread(self.model.generate_content, prompt)
        logger.debug("Response received from AI model.")
        return response.text

    @log_execution()
    async def _save_conversation_history(
        self, pdf_id: int, user_query: str, assistant_response: str, db: AsyncSession
    ):
        """
        Save the conversation history to the database.

        Args:
            pdf_id (int): The unique identifier of the PDF.
            user_query (str): The user's query.
            assistant_response (str): The AI model's response.
            db (AsyncSession): The database session.
        """
        logger.debug("Saving conversation history for PDF ID: %d", pdf_id)
        conversation_entry = ConversationHistory(
            pdf_id=pdf_id, user_query=user_query, assistant_response=assistant_response
        )
        db.add(conversation_entry)
        await db.commit()
        logger.debug("Conversation history saved successfully for PDF ID: %d", pdf_id)
