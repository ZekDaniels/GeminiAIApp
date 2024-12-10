# app/models/conversation.py
from sqlalchemy import Column, Integer, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.db.session import Base

class ConversationHistory(Base):
    __tablename__ = "conversation_history"

    id = Column(Integer, primary_key=True, index=True)
    integration_id = Column(Integer, ForeignKey("integrations.id"), nullable=False)  # Updated table name to 'integrations'
    user_query = Column(Text, nullable=False)
    assistant_response = Column(Text, nullable=False)

    integration = relationship("Integration", back_populates="conversation_history")
