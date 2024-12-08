from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from sqlalchemy.orm import declarative_base

Base = declarative_base()  # This is the base for your models, and all models should inherit from it

# Create an engine and session factory
engine = create_engine(settings.DATABASE_URL, connect_args={"check_same_thread": False})  # for SQLite
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency to get the session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
