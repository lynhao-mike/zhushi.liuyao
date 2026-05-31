"""
Redis client — connection pool, get/set helpers, and cache decorators.

Strategy
--------
All analysis results are deterministic given the same inputs, so we key
by a SHA-256 fingerprint of the request. TTLs are configurable in Settings.

The module exposes:
  - init_redis() / close_redis()  — lifecycle (called from app lifespan)
  - get_cache() / set_cache()     — low-level typed helpers
  - CacheKey                      — structured key builder
  - cache_or_compute()            — thin async wrapper pattern
"""
from __future__ import annotations

import hashlib
import json
from typing import Any, Awaitable, Callable, TypeVar

import redis.asyncio as aioredis

from api.core.config import get_settings
from api.core.logging import get_logger

log = get_logger(__name__)
settings = get_settings()

_redis: aioredis.Redis | None = None

T = TypeVar("T")


# ── Lifecycle ─────────────────────────────────────────────────────────────────

async def init_redis() -> None:
    global _redis
    pool = aioredis.ConnectionPool.from_url(
        settings.REDIS_URL,
        max_connections=settings.REDIS_MAX_CONNECTIONS,
        decode_responses=True,
    )
    _redis = aioredis.Redis(connection_pool=pool)
    try:
        await _redis.ping()
        log.info("redis_connected", url=settings.REDIS_URL)
    except Exception as exc:
        log.warning("redis_unavailable", error=str(exc))


async def close_redis() -> None:
    global _redis
    if _redis:
        await _redis.aclose()
        _redis = None
        log.info("redis_closed")


def get_redis() -> aioredis.Redis | None:
    return _redis


# ── Key builder ───────────────────────────────────────────────────────────────

class CacheKey:
    """
    Typed cache key builder.

    Namespaces:
      analysis:{fingerprint}         — full analysis payload
      listing:{question_type}:{page} — paginated listing
      stats:global                   — dashboard aggregates
    """

    @staticmethod
    def analysis(fingerprint: str) -> str:
        return f"analysis:{fingerprint}"

    @staticmethod
    def listing(question_type: str, page: int, size: int) -> str:
        return f"listing:{question_type}:{page}:{size}"

    @staticmethod
    def stats() -> str:
        return "stats:global"

    @staticmethod
    def template(template_id: str) -> str:
        return f"template:{template_id}"


# ── Fingerprint ───────────────────────────────────────────────────────────────

def build_fingerprint(
    yao_values: list[int],
    ganzhi_key: str,
    question_type: str,
    is_dual: bool,
) -> str:
    """
    Deterministic SHA-256 fingerprint for an analysis request.
    Same inputs → same fingerprint → cache hit.
    """
    raw = json.dumps(
        {
            "y": sorted(enumerate(yao_values), key=lambda x: x[0]),  # positional
            "g": ganzhi_key,
            "q": question_type,
            "d": is_dual,
        },
        sort_keys=True,
        ensure_ascii=False,
    )
    return hashlib.sha256(raw.encode()).hexdigest()


def build_ganzhi_key(
    year: int | None,
    month: int | None,
    day: int | None,
    hour: int,
    ganzhi_override: dict | None,
) -> str:
    """Canonical string key for the date/ganzhi component."""
    if ganzhi_override:
        return json.dumps(ganzhi_override, sort_keys=True, ensure_ascii=False)
    return f"{year}-{month}-{day}-{hour}"


# ── Low-level helpers ─────────────────────────────────────────────────────────

async def get_cache(key: str) -> Any | None:
    """Return deserialized value or None on miss/error."""
    r = get_redis()
    if not r:
        return None
    try:
        raw = await r.get(key)
        if raw is None:
            return None
        return json.loads(raw)
    except Exception as exc:
        log.warning("cache_get_error", key=key, error=str(exc))
        return None


async def set_cache(key: str, value: Any, ttl: int) -> bool:
    """Serialize and store value. Returns True on success."""
    r = get_redis()
    if not r:
        return False
    try:
        await r.setex(key, ttl, json.dumps(value, ensure_ascii=False, default=str))
        return True
    except Exception as exc:
        log.warning("cache_set_error", key=key, error=str(exc))
        return False


async def delete_cache(key: str) -> None:
    r = get_redis()
    if r:
        try:
            await r.delete(key)
        except Exception:
            pass


async def invalidate_prefix(prefix: str) -> int:
    """Delete all keys matching prefix:*. Returns count deleted."""
    r = get_redis()
    if not r:
        return 0
    try:
        keys = await r.keys(f"{prefix}:*")
        if keys:
            return await r.delete(*keys)
    except Exception as exc:
        log.warning("cache_invalidate_error", prefix=prefix, error=str(exc))
    return 0


# ── cache_or_compute helper ───────────────────────────────────────────────────

async def cache_or_compute(
    cache_key: str,
    ttl: int,
    compute_fn: Callable[[], Awaitable[T]],
) -> tuple[T, bool]:
    """
    Try cache first; fall back to compute_fn, then store result.

    Returns:
        (value, from_cache)
    """
    cached = await get_cache(cache_key)
    if cached is not None:
        log.debug("cache_hit", key=cache_key)
        return cached, True

    log.debug("cache_miss", key=cache_key)
    value = await compute_fn()
    await set_cache(cache_key, value, ttl)
    return value, False
