"""
Readings main use cases.

ponytail: this is the real entry module for reading workflows; `reading.py` stays only as a compatibility facade.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.application.use_cases.dto import ReadingCreateCommand
from api.application.use_cases.engine import analyze, should_use_dual
from api.application.use_cases.feedback import create_reading_feedback
from api.application.use_cases.reading_support import (
    build_payload,
    ensure_report_files,
    orm_to_response,
    orm_to_summary,
    payload_to_response,
)
from api.application.use_cases.templates import (
    create_template,
    delete_template,
    get_template,
    list_templates,
)
from api.core.config import get_settings
from api.core.exceptions import NotFoundError
from api.core.logging import get_logger
from api.infrastructure.cache.redis_client import (
    CacheKey,
    build_fingerprint,
    build_ganzhi_key,
    get_cache,
    invalidate_prefix,
    set_cache,
)
from api.infrastructure.database.models import AnalysisCache, ReadingSession

log = get_logger(__name__)
settings = get_settings()


class ReadingCacheRepo:
    """Redis + DB 两层 cache-aside，只负责缓存读写。"""

    def __init__(self, db: AsyncSession):
        self._db = db

    async def get(self, fingerprint: str) -> Optional[Dict[str, Any]]:
        """Check Redis first, fall back to DB cache."""
        cache_key = CacheKey.analysis(fingerprint)
        payload = await get_cache(cache_key)
        if payload:
            log.info("reading_cache_hit", fingerprint=fingerprint)
            if ensure_report_files(payload):
                await set_cache(cache_key, payload, settings.CACHE_TTL_ANALYSIS)
            return payload

        row = await self._get_db_row(fingerprint)
        if row:
            log.info("reading_db_cache_hit", fingerprint=fingerprint)
            payload = row.payload
            if ensure_report_files(payload):
                row.payload = payload
            await set_cache(cache_key, payload, settings.CACHE_TTL_ANALYSIS)
            return payload

        return None

    async def set(self, fingerprint: str, question_type: str, is_dual: bool, payload: Dict[str, Any]) -> None:
        """Upsert DB cache, warm Redis, invalidate collection caches."""
        await self._upsert_db_row(fingerprint, question_type, is_dual, payload)
        await set_cache(CacheKey.analysis(fingerprint), payload, settings.CACHE_TTL_ANALYSIS)
        await _invalidate_reading_collection_caches()

    async def _get_db_row(self, fingerprint: str) -> Optional[AnalysisCache]:
        stmt = select(AnalysisCache).where(AnalysisCache.fingerprint == fingerprint)
        return (await self._db.execute(stmt)).scalar_one_or_none()

    async def _upsert_db_row(self, fingerprint: str, question_type: str, is_dual: bool, payload: Dict[str, Any]) -> None:
        existing = (
            await self._db.execute(
                select(AnalysisCache).where(AnalysisCache.fingerprint == fingerprint)
            )
        ).scalar_one_or_none()

        if existing:
            existing.payload = payload
            existing.hit_count = (existing.hit_count or 0) + 1
            existing.last_hit_at = datetime.now(timezone.utc)
        else:
            self._db.add(AnalysisCache(
                fingerprint=fingerprint,
                question_type=question_type,
                is_dual=is_dual,
                payload=payload,
            ))


class ReadingRepo:
    """ORM CRUD for ReadingSession — no cache logic here."""

    def __init__(self, db: AsyncSession):
        self._db = db

    async def persist(
        self,
        req: ReadingCreateCommand,
        result: Dict[str, Any],
        is_dual: bool,
        fingerprint: str,
    ) -> uuid.UUID:
        meta = result["hexagram_meta"]
        analysis = result["analysis"]

        session = ReadingSession(
            question=req.question,
            question_type=req.question_type,
            querent_name=req.querent_name,
            is_dual=is_dual,
            yao_values=req.yao_values,
            cast_year=req.year,
            cast_month=req.month,
            cast_day=req.day,
            cast_hour=req.hour,
            ganzhi_override=req.ganzhi_override,
            ben_gua_name=meta["ben_gua_name"],
            bian_gua_name=meta["bian_gua_name"],
            palace_name=meta["palace_name"],
            palace_wu_xing=meta["palace_wu_xing"],
            xun_kong=meta["xun_kong"],
            gan_zhi=meta["gan_zhi"],
            lines_json=meta["lines"],
            wangshuai_json={"results": analysis.get("wangshuai", [])},
            dongbian_json=analysis.get("dongbian", {}),
            patterns_json=analysis.get("patterns", {}),
            jixiong_json=analysis.get("jixiong"),
            yingqi_json={"results": analysis.get("yingqi", [])},
            star_spirits_json=analysis.get("star_spirits", {}),
            report_text=result.get("report_text"),
            report_readable=result.get("report_readable"),
            dual_perspectives_json=(analysis.get("perspectives", []) if is_dual else None),
            dual_consensus=analysis.get("consensus") if is_dual else None,
            ji_xiong=result.get("ji_xiong"),
            gua_ju_pattern=result.get("gua_ju_pattern"),
        )
        self._db.add(session)
        await self._db.flush()
        return session.id

    async def get(self, reading_id: uuid.UUID) -> ReadingSession:
        row = await self._db.get(ReadingSession, reading_id)
        if not row:
            raise NotFoundError(f"Reading {reading_id} not found")
        return row

    async def list(
        self,
        question_type: Optional[str],
        ji_xiong: Optional[str],
        page: int,
        size: int,
    ) -> tuple[List[ReadingSession], int]:
        stmt = select(ReadingSession).order_by(desc(ReadingSession.created_at))
        count_stmt = select(func.count(ReadingSession.id))

        if question_type:
            stmt = stmt.where(ReadingSession.question_type == question_type)
            count_stmt = count_stmt.where(ReadingSession.question_type == question_type)
        if ji_xiong:
            stmt = stmt.where(ReadingSession.ji_xiong == ji_xiong)
            count_stmt = count_stmt.where(ReadingSession.ji_xiong == ji_xiong)

        total = (await self._db.execute(count_stmt)).scalar_one()
        rows = (await self._db.execute(stmt.offset((page - 1) * size).limit(size))).scalars().all()
        return list(rows), total

    async def delete(self, reading_id: uuid.UUID) -> None:
        row = await self._db.get(ReadingSession, reading_id)
        if not row:
            raise NotFoundError(f"Reading {reading_id} not found")
        await self._db.delete(row)


async def create_reading(
    req: ReadingCreateCommand,
    db: AsyncSession,
) -> Dict[str, Any]:
    """Full create-reading flow with cache-aside."""
    is_dual = should_use_dual(req.question_type, req.is_dual)

    ganzhi_key = build_ganzhi_key(req.year, req.month, req.day, req.hour, req.ganzhi_override)
    context_key = {
        "ganzhi": ganzhi_key,
        "question": req.question or "",
        "querent_name": req.querent_name or "",
    }
    fingerprint = build_fingerprint(req.yao_values, context_key, req.question_type, is_dual)

    cache = ReadingCacheRepo(db)
    cached_payload = await cache.get(fingerprint)
    if cached_payload:
        return payload_to_response(cached_payload, from_cache=True)

    log.info("reading_engine_start", question_type=req.question_type, is_dual=is_dual)
    result = await analyze(
        yao_values=req.yao_values,
        year=req.year,
        month=req.month,
        day=req.day,
        hour=req.hour,
        question_type=req.question_type,
        is_dual=is_dual,
        ganzhi_override=req.ganzhi_override,
        querent_name=req.querent_name,
        question=req.question,
    )
    log.info("reading_engine_done", ben_gua=result["hexagram_meta"]["ben_gua_name"])

    payload = build_payload(req, result, is_dual)

    repo = ReadingRepo(db)
    session_id = await repo.persist(req, result, is_dual, fingerprint)
    payload["id"] = str(session_id)
    payload["created_at"] = datetime.now(timezone.utc).isoformat()

    await cache.set(fingerprint, req.question_type, is_dual, payload)

    return payload_to_response(payload, from_cache=False)


async def get_reading(reading_id: uuid.UUID, db: AsyncSession) -> Dict[str, Any]:
    row = await ReadingRepo(db).get(reading_id)
    return orm_to_response(row)


async def list_readings(
    db: AsyncSession,
    question_type: Optional[str],
    ji_xiong: Optional[str],
    page: int,
    size: int,
) -> Dict[str, Any]:
    cache_key = CacheKey.listing(question_type or "all", page, size, ji_xiong or "all")
    cached = await get_cache(cache_key)
    if cached:
        return cached

    rows, total = await ReadingRepo(db).list(question_type, ji_xiong, page, size)
    items = [orm_to_summary(row) for row in rows]
    pages = (total + size - 1) // size
    result = {"items": items, "total": total, "page": page, "size": size, "pages": pages}
    await set_cache(cache_key, result, settings.CACHE_TTL_HEXAGRAM_LIST)
    return result


async def delete_reading(reading_id: uuid.UUID, db: AsyncSession) -> None:
    await ReadingRepo(db).delete(reading_id)
    await _invalidate_reading_collection_caches()


async def get_stats(db: AsyncSession) -> Dict[str, Any]:
    cache_key = CacheKey.stats()
    cached = await get_cache(cache_key)
    if cached:
        return cached

    total = (await db.execute(select(func.count(ReadingSession.id)))).scalar_one()

    by_type_rows = (
        await db.execute(
            select(ReadingSession.question_type, func.count(ReadingSession.id))
            .group_by(ReadingSession.question_type)
        )
    ).all()

    by_jx_rows = (
        await db.execute(
            select(ReadingSession.ji_xiong, func.count(ReadingSession.id))
            .group_by(ReadingSession.ji_xiong)
        )
    ).all()

    top_gua_rows = (
        await db.execute(
            select(ReadingSession.ben_gua_name, func.count(ReadingSession.id).label("cnt"))
            .group_by(ReadingSession.ben_gua_name)
            .order_by(desc("cnt"))
            .limit(10)
        )
    ).all()

    result = {
        "total_readings": total,
        "total_by_question_type": {qt: cnt for qt, cnt in by_type_rows if qt},
        "total_by_ji_xiong": {jx: cnt for jx, cnt in by_jx_rows if jx},
        "top_ben_gua": [{"gua": g, "count": c} for g, c in top_gua_rows if g],
        "cache_hit_rate": None,
    }

    await set_cache(cache_key, result, settings.CACHE_TTL_STATS)
    return result


async def _invalidate_reading_collection_caches() -> None:
    """Invalidate derived list/stat caches after reading mutations."""
    deleted_listing = await invalidate_prefix("listing")
    await invalidate_prefix("stats")
    log.info("reading_collection_cache_invalidated", listing_deleted=deleted_listing)
