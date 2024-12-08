from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import relationship
from app.db.session import Base

class PDF(Base):
    __tablename__ = "pdfs"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)
    content = Column(Text)
    page_count = Column(Integer) 
    conversation_history = relationship("ConversationHistory", back_populates="pdf", cascade="all, delete-orphan")
