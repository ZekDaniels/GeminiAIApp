import logging
from sqlalchemy.future import select
from app.models.chat import ConversationHistory
from app.decorators.logging import log_execution

logger = logging.getLogger("app")


class HistoryService:
    @log_execution()
    async def fetch_conversation_history(self, integration_id, db):
        """Fetch conversation history for a given Integration ID."""
        result = await db.execute(select(ConversationHistory).where(ConversationHistory.integration_id == integration_id))
        return result.scalars().all()

    @log_execution()
    async def save_conversation_history(self, integration_id, user_query, assistant_response, db):
        """Save conversation history to the database."""
        conversation_entry = ConversationHistory(
            integration_id=integration_id, user_query=user_query, assistant_response=assistant_response
        )
        db.add(conversation_entry)
        await db.commit()
