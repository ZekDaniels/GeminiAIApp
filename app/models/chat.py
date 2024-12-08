# app/models/conversation.py
from sqlalchemy import Column, Integer, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.db.session import Base

class ConversationHistory(Base):
    __tablename__ = "conversation_history"

    id = Column(Integer, primary_key=True, index=True)
    pdf_id = Column(Integer, ForeignKey("pdfs.id"), nullable=False)  # Updated table name to 'pdfs'
    user_query = Column(Text, nullable=False)
    assistant_response = Column(Text, nullable=False)

    pdf = relationship("PDF", back_populates="conversation_history")
