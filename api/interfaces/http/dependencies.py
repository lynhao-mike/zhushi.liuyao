"""HTTP dependency adapters.

Keep FastAPI routers depending on interface-local names instead of importing
infrastructure modules directly.
"""
from __future__ import annotations

from api.infrastructure.cache.redis_client import get_redis
from api.infrastructure.database.session import check_database_health, get_db

__all__ = ["check_database_health", "get_db", "get_redis"]
