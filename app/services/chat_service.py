import logging
from app.services.pdf_content_service import PDFContentService
from app.services.history_service import HistoryService
from app.services.ai_model_service import AIModelService
from app.utils.prompt_builder import PromptBuilder
from app.decorators.chat_handle_errors import handle_chat_service_errors
from app.decorators.logging import log_execution
from app.decorators.handle_transaction import handle_transaction

logger = logging.getLogger("app")


class ChatService:
    def __init__(self, pdf_service=None, history_service=None, ai_service=None):
        self.pdf_service = pdf_service or PDFContentService()
        self.history_service = history_service or HistoryService()
        self.ai_service = ai_service or AIModelService()
        logger.info("ChatService initialized.")

    @handle_transaction()
    @handle_chat_service_errors
    @log_execution()
    async def generate_response(self, integration_id, user_query, db, only_text=False):
        """Generate a response based on user query and PDF content."""
        pdf_content = await self.pdf_service.fetch_pdf_content(integration_id, db)
        conversation_history = await self.history_service.fetch_conversation_history(integration_id, db)
        prompt = PromptBuilder.construct_prompt(conversation_history, user_query, pdf_content, only_text)
        assistant_response = await self.ai_service.generate_response(prompt)
        await self.history_service.save_conversation_history(integration_id, user_query, assistant_response, db)
        return assistant_response
