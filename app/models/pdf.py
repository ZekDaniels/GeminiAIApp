from sqlalchemy import Column, Integer, String, Text
from app.db.session import Base

class PDF(Base):
    __tablename__ = "pdfs"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)
    content = Column(Text)
    page_count = Column(Integer)  # Make sure this field is defined if it's used