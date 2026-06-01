"""
Async SQLAlchemy session factory and dependency injection helper.
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from api.core.config import get_settings

settings = get_settings()

# ── Engine ────────────────────────────────────────────────────────────────────
# NullPool is used in tests; production uses the default QueuePool.
_engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_recycle=settings.DB_POOL_RECYCLE,
    echo=settings.DEBUG,
    future=True,
)

# ── Session factory ───────────────────────────────────────────────────────────
AsyncSessionFactory: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=_engine,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


# ── FastAPI dependency ────────────────────────────────────────────────────────
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async DB session, rolling back on error."""
    async with AsyncSessionFactory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@asynccontextmanager
async def managed_session() -> AsyncGenerator[AsyncSession, None]:
    """Context-manager form for use outside of FastAPI DI (e.g. scripts)."""
    async with AsyncSessionFactory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def check_database_health() -> tuple[bool, str]:
    """Return database health without exposing the internal engine."""
    try:
        async with _engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True, "ok"
    except Exception as exc:  # pragma: no cover - depends on external DB availability
        return False, f"error: {exc}"


async def close_engine() -> None:
    await _engine.dispose()
