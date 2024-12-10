from sqlalchemy import Column, Integer, String, Text, DateTime, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.session import Base
from enum import Enum as PyEnum  # Enum'ı SQLAlchemy ile karışmaması için yeniden adlandırıyoruz.
from app.models.chat import ConversationHistory

class ProcessingStatus(str, PyEnum):
    PROCESSED = "Processed"
    PENDING = "Pending"
    FAILED = "Failed"


class PDF(Base):
    __tablename__ = "pdfs"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True, nullable=False)
    content = Column(Text, nullable=False)
    page_count = Column(Integer, nullable=False)
    processing_status = Column(Enum(ProcessingStatus), default=ProcessingStatus.PROCESSED, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    conversation_history = relationship("ConversationHistory", back_populates="pdf", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<PDF(id={self.id}, filename={self.filename}, page_count={self.page_count})>"
