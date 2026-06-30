"""
Domain-level exceptions and FastAPI exception handlers.
"""
from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

# ── Domain Exceptions ────────────────────────────────────────────────────────

class LiuyaoAPIError(Exception):
    """Base for all API-level errors."""
    status_code: int = 500
    error_code: str = "INTERNAL_ERROR"

    def __init__(self, detail: str, *, error_code: str | None = None):
        super().__init__(detail)
        self.detail = detail
        if error_code:
            self.error_code = error_code


class ValidationError(LiuyaoAPIError):
    status_code = 422
    error_code = "VALIDATION_ERROR"


class NotFoundError(LiuyaoAPIError):
    status_code = 404
    error_code = "NOT_FOUND"


class EngineError(LiuyaoAPIError):
    status_code = 500
    error_code = "ENGINE_ERROR"


class CacheError(LiuyaoAPIError):
    """Non-fatal; callers should fall through to DB/engine."""
    status_code = 500
    error_code = "CACHE_ERROR"


# ── FastAPI Exception Handlers ───────────────────────────────────────────────

def _error_body(error_code: str, detail: str) -> dict:
    return {"error": {"code": error_code, "message": detail}}


def register_exception_handlers(app: FastAPI) -> None:

    @app.exception_handler(LiuyaoAPIError)
    async def liuyao_error_handler(request: Request, exc: LiuyaoAPIError):
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_body(exc.error_code, exc.detail),
        )

    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError):
        return JSONResponse(
            status_code=422,
            content=_error_body("VALIDATION_ERROR", str(exc)),
        )

    @app.exception_handler(Exception)
    async def generic_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content=_error_body("INTERNAL_ERROR", "An unexpected error occurred."),
        )
