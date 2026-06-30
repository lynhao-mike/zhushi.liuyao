"""
Alembic env.py — supports both offline and online (async) migration modes.
"""
from __future__ import annotations

import asyncio
import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection

# Import all models so Alembic can detect them
from api.infrastructure.database.models import Base  # noqa: F401

# Alembic Config object
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Use our ORM metadata for autogenerate
target_metadata = Base.metadata

# Override DB URL from environment if provided
db_url = os.environ.get("DATABASE_URL_SYNC")
if db_url:
    config.set_main_option("sqlalchemy.url", db_url)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations using an async engine (psycopg2 sync adapter)."""
    # We use the sync URL for Alembic (asyncpg doesn't support it directly)
    sync_url = config.get_main_option("sqlalchemy.url")
    from sqlalchemy import create_engine

    sync_engine = create_engine(
        sync_url,
        poolclass=pool.NullPool,
    )
    with sync_engine.connect() as connection:
        do_run_migrations(connection)
    sync_engine.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
