from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class PDF(Base):
    __tablename__ = "pdfs"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)
    content = Column(Text)
    page_count = Column(Integer)
