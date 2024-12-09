from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

# Base class for models
Base = declarative_base()

# Define the database URL
DATABASE_URL = "sqlite+aiosqlite:///./pdf_chat.db"

# Create the async engine
engine = create_async_engine(DATABASE_URL, echo=True)

# Create the async session factory
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Dependency to get the async database session
async def get_db() -> AsyncSession:
    """
    Dependency to get an AsyncSession for database operations.
    """
    async with AsyncSessionLocal() as session:
        yield session
