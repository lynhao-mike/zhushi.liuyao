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

from api.core.config import get_settings
from api.interfaces.http.dependencies import check_database_health, get_redis

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
    db_ok, db_status = await check_database_health()
    checks["database"] = db_status
    ok = ok and db_ok

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
