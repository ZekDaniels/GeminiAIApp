from logging.config import fileConfig
from sqlalchemy import create_engine, pool
from alembic import context
from app.db.session import Base  # Import Base containing all models' metadata
from app.core.config import settings  # Import settings for database URL

# Alembic configuration object
config = context.config

# Set up logging configuration
fileConfig(config.config_file_name)
# Import your models to make sure they are registered in Base.metadata
from app.models.integration import Integration  # Import your model to register its metadata
from app.models.chat import ConversationHistory  # Import your model to register its metadata
# SQLAlchemy metadata for Alembic
target_metadata = Base.metadata

# Convert the database URL to synchronous mode for Alembic compatibility
sync_database_url = settings.DATABASE_URL.replace("sqlite+aiosqlite", "sqlite")

def run_migrations_offline():
    """Run migrations in 'offline' mode."""
    context.configure(
        url=sync_database_url, 
        target_metadata=target_metadata, 
        literal_binds=True
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    """Run migrations in 'online' mode."""
    connectable = create_engine(sync_database_url, poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(
            connection=connection, 
            target_metadata=target_metadata
        )
        with context.begin_transaction():
            context.run_migrations()

# Determine whether migrations should run in offline or online mode
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
