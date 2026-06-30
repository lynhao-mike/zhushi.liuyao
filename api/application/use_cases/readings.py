"""
Readings main use cases.

ponytail: keep reading workflow concrete; add repositories only when a second storage path exists.
"""
from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.application.use_cases.engine import analyze, should_use_dual
from api.application.use_cases.reading_support import (
    build_payload,
    ensure_report_files,
    orm_to_response,
    orm_to_summary,
    payload_to_response,
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


async def create_reading(req, db: AsyncSession) -> dict[str, Any]:
    """Full create-reading flow with cache-aside."""
    is_dual = should_use_dual(req.question_type, req.is_dual)

    ganzhi_key = build_ganzhi_key(req.year, req.month, req.day, req.hour, req.ganzhi_override)
    context_key = {
        "ganzhi": ganzhi_key,
        "question": req.question or "",
        "querent_name": req.querent_name or "",
    }
    fingerprint = build_fingerprint(req.yao_values, context_key, req.question_type, is_dual)
    cache_key = CacheKey.analysis(fingerprint)

    payload = await get_cache(cache_key)
    if payload:
        log.info("reading_cache_hit", fingerprint=fingerprint)
        if ensure_report_files(payload):
            await set_cache(cache_key, payload, settings.CACHE_TTL_ANALYSIS)
        return payload_to_response(payload, from_cache=True)

    cached_row = (
        await db.execute(select(AnalysisCache).where(AnalysisCache.fingerprint == fingerprint))
    ).scalar_one_or_none()
    if cached_row:
        log.info("reading_db_cache_hit", fingerprint=fingerprint)
        payload = cached_row.payload
        if ensure_report_files(payload):
            cached_row.payload = payload
        await set_cache(cache_key, payload, settings.CACHE_TTL_ANALYSIS)
        return payload_to_response(payload, from_cache=True)

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
    db.add(session)
    await db.flush()
    payload["id"] = str(session.id)
    payload["created_at"] = datetime.now(UTC).isoformat()

    existing = (
        await db.execute(select(AnalysisCache).where(AnalysisCache.fingerprint == fingerprint))
    ).scalar_one_or_none()
    if existing:
        existing.payload = payload
        existing.hit_count = (existing.hit_count or 0) + 1
        existing.last_hit_at = datetime.now(UTC)
    else:
        db.add(AnalysisCache(
            fingerprint=fingerprint,
            question_type=req.question_type,
            is_dual=is_dual,
            payload=payload,
        ))
    await set_cache(cache_key, payload, settings.CACHE_TTL_ANALYSIS)
    await _invalidate_reading_collection_caches()

    return payload_to_response(payload, from_cache=False)


async def get_reading(reading_id: uuid.UUID, db: AsyncSession) -> dict[str, Any]:
    row = await db.get(ReadingSession, reading_id)
    if not row:
        raise NotFoundError(f"Reading {reading_id} not found")
    return orm_to_response(row)


async def list_readings(
    db: AsyncSession,
    question_type: str | None,
    ji_xiong: str | None,
    page: int,
    size: int,
) -> dict[str, Any]:
    cache_key = CacheKey.listing(question_type or "all", page, size, ji_xiong or "all")
    cached = await get_cache(cache_key)
    if cached:
        return cached

    stmt = select(ReadingSession).order_by(desc(ReadingSession.created_at))
    count_stmt = select(func.count(ReadingSession.id))
    if question_type:
        stmt = stmt.where(ReadingSession.question_type == question_type)
        count_stmt = count_stmt.where(ReadingSession.question_type == question_type)
    if ji_xiong:
        stmt = stmt.where(ReadingSession.ji_xiong == ji_xiong)
        count_stmt = count_stmt.where(ReadingSession.ji_xiong == ji_xiong)

    total = (await db.execute(count_stmt)).scalar_one()
    rows = (await db.execute(stmt.offset((page - 1) * size).limit(size))).scalars().all()
    result = {
        "items": [orm_to_summary(row) for row in rows],
        "total": total,
        "page": page,
        "size": size,
        "pages": (total + size - 1) // size,
    }
    await set_cache(cache_key, result, settings.CACHE_TTL_HEXAGRAM_LIST)
    return result


async def delete_reading(reading_id: uuid.UUID, db: AsyncSession) -> None:
    row = await db.get(ReadingSession, reading_id)
    if not row:
        raise NotFoundError(f"Reading {reading_id} not found")
    await db.delete(row)
    await _invalidate_reading_collection_caches()


async def get_stats(db: AsyncSession) -> dict[str, Any]:
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
    deleted_listing = await invalidate_prefix("listing")
    await invalidate_prefix("stats")
    log.info("reading_collection_cache_invalidated", listing_deleted=deleted_listing)
