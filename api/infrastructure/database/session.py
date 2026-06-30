"""
Async SQLAlchemy session factory and dependency injection helper.
"""
from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from api.core.config import get_settings

settings = get_settings()

_engine = None
AsyncSessionFactory: async_sessionmaker[AsyncSession] | None = None


def _get_engine():
    """Create the async SQLAlchemy engine lazily to keep imports side-effect free."""
    global _engine
    if _engine is None:
        _engine = create_async_engine(
            settings.DATABASE_URL,
            pool_size=settings.DB_POOL_SIZE,
            max_overflow=settings.DB_MAX_OVERFLOW,
            pool_recycle=settings.DB_POOL_RECYCLE,
            echo=settings.DEBUG,
            future=True,
        )
    return _engine


def _get_session_factory():
    global AsyncSessionFactory
    if AsyncSessionFactory is None:
        AsyncSessionFactory = async_sessionmaker(
            bind=_get_engine(),
            expire_on_commit=False,
            autoflush=False,
            autocommit=False,
        )
    return AsyncSessionFactory


# ── FastAPI dependency ────────────────────────────────────────────────────────
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async DB session, rolling back on error."""
    async with _get_session_factory()() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def check_database_health() -> tuple[bool, str]:
    """Return database health without exposing the internal engine."""
    try:
        async with _get_engine().connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True, "ok"
    except Exception as exc:  # pragma: no cover - depends on external DB availability
        return False, f"error: {exc}"


async def close_engine() -> None:
    global _engine, AsyncSessionFactory
    if _engine is not None:
        await _engine.dispose()
    _engine = None
    AsyncSessionFactory = None
