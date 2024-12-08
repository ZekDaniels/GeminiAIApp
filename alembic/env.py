# alembic/env.py

import sys
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
from app.db.session import Base  # Import Base from session module
from app.core.config import settings  # Import settings to get database URL

# Alembic Config object provides access to configuration
config = context.config

# Setup logging configuration
fileConfig(config.config_file_name)

# Import your models to make sure they are registered in Base.metadata
from app.models.pdf import PDF  # Import your model to register its metadata
from app.models.chat import ConversationHistory  # Import your model to register its metadata

# Access the metadata object for all models
target_metadata = Base.metadata

# Set the database URL dynamically if needed
config.set_main_option('sqlalchemy.url', settings.DATABASE_URL)

def run_migrations_offline():
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)
    
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(config.get_section(config.config_ini_section),
                                     prefix='sqlalchemy.',
                                     poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()

# Run migrations in either offline or online mode
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
