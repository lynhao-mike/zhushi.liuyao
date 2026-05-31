"""
Health check endpoints — used by Kubernetes liveness/readiness probes
and Docker Compose healthchecks.

GET /health/live    — liveness:  is the process alive?
GET /health/ready   — readiness: can the process serve traffic?
GET /health/full    — full diagnostic (DB + Redis status)
"""
from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from api.cache.redis_client import get_redis
from api.core.config import get_settings
from api.db.session import _engine

router = APIRouter(prefix="/health", tags=["health"])
settings = get_settings()


@router.get("/live", include_in_schema=False)
async def liveness():
    """Always returns 200 if the process is running."""
    return {"status": "ok", "version": settings.APP_VERSION}


@router.get("/ready")
async def readiness():
    """
    Returns 200 only when both DB and Redis are reachable.
    Returns 503 otherwise — Kubernetes will not route traffic here.
    """
    checks = {}
    ok = True

    # DB check
    try:
        async with _engine.connect() as conn:
            await conn.execute(__import__("sqlalchemy").text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as exc:
        checks["database"] = f"error: {exc}"
        ok = False

    # Redis check
    r = get_redis()
    if r:
        try:
            await r.ping()
            checks["redis"] = "ok"
        except Exception as exc:
            checks["redis"] = f"error: {exc}"
            ok = False
    else:
        checks["redis"] = "not_initialized"
        ok = False

    status_code = 200 if ok else 503
    return JSONResponse(
        status_code=status_code,
        content={"status": "ready" if ok else "not_ready", "checks": checks},
    )


@router.get("/full")
async def full_health():
    """Extended diagnostic — include version + config summary."""
    liveness_data = {"version": settings.APP_VERSION, "debug": settings.DEBUG}
    readiness_data = (await readiness()).body  # type: ignore[attr-defined]
    import json
    return {**liveness_data, **json.loads(readiness_data)}
