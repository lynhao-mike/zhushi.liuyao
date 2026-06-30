"""
FastAPI application factory.

Lifecycle:
  startup  → configure logging → connect Redis → run DB migrations
  shutdown → close Redis → close DB engine
"""
from __future__ import annotations

from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from api.application.use_cases.engine import shutdown_executor
from api.core.config import get_settings
from api.core.exceptions import register_exception_handlers
from api.core.logging import configure_logging
from api.infrastructure.cache.redis_client import close_redis, init_redis
from api.infrastructure.database.session import close_engine
from api.interfaces.http.routers import health, readings, templates

settings = get_settings()
log = structlog.get_logger(__name__)


# ── Application Lifespan ──────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ───────────────────────────────────────────────────────
    configure_logging()
    log.info("app_starting", version=settings.APP_VERSION)

    await init_redis()

    log.info("app_ready")

    yield

    # ── Shutdown ──────────────────────────────────────────────────────
    log.info("app_shutting_down")
    await close_redis()
    await close_engine()
    shutdown_executor()
    log.info("app_stopped")


# ── Factory ───────────────────────────────────────────────────────────────────

def create_app() -> FastAPI:
    app = FastAPI(
        title="Zhushi Liuyao API",
        description=(
            "Production-grade REST API for the 六爻 (Six-Line) divination analysis system. "
            "Based on 《古筮真诠》 theory."
        ),
        version=settings.APP_VERSION,
        debug=settings.DEBUG,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # ── Middleware ─────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(GZipMiddleware, minimum_size=1024)

    # ── Exception handlers ────────────────────────────────────────────
    register_exception_handlers(app)

    # ── Routers ───────────────────────────────────────────────────────
    API_PREFIX = "/api/v1"
    app.include_router(health.router)                           # /health/*
    app.include_router(readings.router,  prefix=API_PREFIX)    # /api/v1/readings
    app.include_router(templates.router, prefix=API_PREFIX)    # /api/v1/templates

    return app


app = create_app()
