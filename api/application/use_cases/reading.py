"""
Reading Service — orchestrates the full request lifecycle:

  1. Resolve dual-perspective flag
  2. Build cache fingerprint
  3. Check Redis cache  → hit: return cached payload
  4. Run analysis engine (thread pool)
  5. Persist to PostgreSQL (ReadingSession + AnalysisCache rows)
  6. Warm Redis cache
  7. Build and return application payload dictionaries
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import func, select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from api.infrastructure.cache.redis_client import (
    CacheKey,
    build_fingerprint,
    build_ganzhi_key,
    get_cache,
    invalidate_prefix,
    set_cache,
)
from api.core.config import get_settings
from api.core.exceptions import NotFoundError
from api.core.logging import get_logger
from api.infrastructure.database.models import AnalysisCache, HexagramTemplate, ReadingFeedback, ReadingSession
from api.application.use_cases.dto import (
    ReadingCreateCommand,
    ReadingFeedbackCreateCommand,
    TemplateCreateCommand,
)
from api.application.use_cases.engine import analyze, should_use_dual
from liuyao.domain.data import QUESTION_TYPE_LABELS

log = get_logger(__name__)
settings = get_settings()


# ── Create Reading ────────────────────────────────────────────────────────────

async def create_reading(
    req: ReadingCreateCommand,
    db: AsyncSession,
) -> Dict[str, Any]:
    """Full create-reading flow with cache-aside."""

    # 1. Resolve dual flag
    is_dual = should_use_dual(req.question_type, req.is_dual)

    # 2. Build fingerprint
    ganzhi_override_dict = req.ganzhi_override
    ganzhi_key = build_ganzhi_key(req.year, req.month, req.day, req.hour, ganzhi_override_dict)
    fingerprint = build_fingerprint(req.yao_values, ganzhi_key, req.question_type, is_dual)

    cache_key = CacheKey.analysis(fingerprint)

    # 3. Check Redis
    cached_payload = await get_cache(cache_key)
    if cached_payload:
        log.info("reading_cache_hit", fingerprint=fingerprint)
        return _payload_to_response(cached_payload, from_cache=True)

    # 4. Check persistent analysis cache (DB layer)
    db_cache = await _get_db_cache(db, fingerprint)
    if db_cache:
        log.info("reading_db_cache_hit", fingerprint=fingerprint)
        payload = db_cache.payload
        # Warm Redis back up
        await set_cache(cache_key, payload, settings.CACHE_TTL_ANALYSIS)
        return _payload_to_response(payload, from_cache=True)

    # 5. Run analysis engine
    log.info("reading_engine_start", question_type=req.question_type, is_dual=is_dual)
    result = await analyze(
        yao_values=req.yao_values,
        year=req.year,
        month=req.month,
        day=req.day,
        hour=req.hour,
        question_type=req.question_type,
        is_dual=is_dual,
        ganzhi_override=ganzhi_override_dict,
        querent_name=req.querent_name,
        question=req.question,
    )
    log.info("reading_engine_done", ben_gua=result["hexagram_meta"]["ben_gua_name"])

    # 6. Build full payload
    payload = _build_payload(req, result, is_dual)

    # 7. Persist ReadingSession
    session_id = await _persist_reading_session(db, req, result, is_dual, fingerprint)
    payload["id"] = str(session_id)
    payload["created_at"] = datetime.now(timezone.utc).isoformat()

    # 8. Persist AnalysisCache (upsert)
    await _upsert_db_cache(db, fingerprint, req.question_type, is_dual, payload)

    # 9. Warm Redis and invalidate derived collection caches
    await set_cache(cache_key, payload, settings.CACHE_TTL_ANALYSIS)
    await _invalidate_reading_collection_caches()

    return _payload_to_response(payload, from_cache=False)


# ── Get / List ────────────────────────────────────────────────────────────────

async def get_reading(reading_id: uuid.UUID, db: AsyncSession) -> Dict[str, Any]:
    row = await db.get(ReadingSession, reading_id)
    if not row:
        raise NotFoundError(f"Reading {reading_id} not found")
    return _orm_to_response(row)


async def list_readings(
    db: AsyncSession,
    question_type: Optional[str],
    ji_xiong: Optional[str],
    page: int,
    size: int,
) -> Dict[str, Any]:
    cache_key = CacheKey.listing(question_type or "all", page, size)
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
    rows  = (await db.execute(stmt.offset((page - 1) * size).limit(size))).scalars().all()

    items = [_orm_to_summary(r) for r in rows]
    pages = (total + size - 1) // size

    result = {"items": items, "total": total, "page": page, "size": size, "pages": pages}

    # Cache listing for a short TTL
    await set_cache(cache_key, result, settings.CACHE_TTL_HEXAGRAM_LIST)
    return result


async def delete_reading(reading_id: uuid.UUID, db: AsyncSession) -> None:
    row = await db.get(ReadingSession, reading_id)
    if not row:
        raise NotFoundError(f"Reading {reading_id} not found")
    await db.delete(row)
    await _invalidate_reading_collection_caches()


# ── Feedback ──────────────────────────────────────────────────────────────────

async def create_reading_feedback(
    reading_id: uuid.UUID,
    req: ReadingFeedbackCreateCommand,
    db: AsyncSession,
) -> Dict[str, Any]:
    row = await db.get(ReadingSession, reading_id)
    if not row:
        raise NotFoundError(f"Reading {reading_id} not found")

    feedback = ReadingFeedback(
        reading_id=reading_id,
        actual_outcome=req.actual_outcome,
        feedback_text=req.feedback_text,
        status="submitted",
        original_judgement=row.jixiong_json,
    )
    db.add(feedback)
    await db.flush()
    return _feedback_to_dict(feedback)


# ── Stats ─────────────────────────────────────────────────────────────────────

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


# ── Template CRUD ─────────────────────────────────────────────────────────────

async def create_template(req: TemplateCreateCommand, db: AsyncSession) -> Dict[str, Any]:
    tmpl = HexagramTemplate(
        name=req.name,
        description=req.description,
        yao_values=req.yao_values,
        ganzhi_override=req.ganzhi_override,
        cast_hour=req.cast_hour,
        default_question_type=req.default_question_type,
        source_text=req.source_text,
    )
    db.add(tmpl)
    await db.flush()
    return _template_to_dict(tmpl)


async def list_templates(db: AsyncSession) -> List[Dict[str, Any]]:
    rows = (await db.execute(select(HexagramTemplate).order_by(HexagramTemplate.created_at))).scalars().all()
    return [_template_to_dict(r) for r in rows]


async def get_template(template_id: uuid.UUID, db: AsyncSession) -> Dict[str, Any]:
    row = await db.get(HexagramTemplate, template_id)
    if not row:
        raise NotFoundError(f"Template {template_id} not found")
    return _template_to_dict(row)


async def delete_template(template_id: uuid.UUID, db: AsyncSession) -> None:
    row = await db.get(HexagramTemplate, template_id)
    if not row:
        raise NotFoundError(f"Template {template_id} not found")
    await db.delete(row)


# ── Cache invalidation ─────────────────────────────────────────────────────────

async def _invalidate_reading_collection_caches() -> None:
    """Invalidate derived list/stat caches after reading mutations."""
    deleted_listing = await invalidate_prefix("listing")
    await invalidate_prefix("stats")
    log.info("reading_collection_cache_invalidated", listing_deleted=deleted_listing)


# ── Private helpers ───────────────────────────────────────────────────────────

def _build_payload(
    req: ReadingCreateCommand,
    result: Dict[str, Any],
    is_dual: bool,
) -> Dict[str, Any]:
    meta = result["hexagram_meta"]
    analysis = result["analysis"]

    payload: Dict[str, Any] = {
        "question_type":       req.question_type,
        "question_type_label": QUESTION_TYPE_LABELS.get(req.question_type, req.question_type),
        "question":            req.question,
        "querent_name":        req.querent_name,
        "is_dual":             is_dual,
        # Hexagram metadata
        "ben_gua_name":   meta["ben_gua_name"],
        "bian_gua_name":  meta["bian_gua_name"],
        "palace_name":    meta["palace_name"],
        "palace_wu_xing": meta["palace_wu_xing"],
        "xun_kong":       meta["xun_kong"],
        "gan_zhi":        meta["gan_zhi"],
        "lines":          meta["lines"],
        # Analysis
        "wangshuai": analysis.get("wangshuai", []),
        "dongbian":  analysis.get("dongbian", {}),
        "patterns":  analysis.get("patterns", {}),
        "star_spirits": analysis.get("star_spirits", {}),
        # Reports
        "report_text":     result.get("report_text"),
        "report_readable": result.get("report_readable"),
    }

    if is_dual:
        payload["dual_consensus"] = analysis.get("consensus")
        payload["perspectives"] = [
            {
                "perspective_label": p["perspective_label"],
                "yong_shen_liu_qin": p["yong_shen_liu_qin"],
                "jixiong":           p["jixiong"],
                "yingqi":            p["yingqi"],
            }
            for p in analysis.get("perspectives", [])
        ]
        payload["jixiong"] = None
        payload["yingqi"]  = None
    else:
        payload["jixiong"] = analysis.get("jixiong")
        payload["yingqi"]  = analysis.get("yingqi", [])
        payload["perspectives"]   = None
        payload["dual_consensus"] = None

    return payload


async def _persist_reading_session(
    db: AsyncSession,
    req: ReadingCreateCommand,
    result: Dict[str, Any],
    is_dual: bool,
    fingerprint: str,
) -> uuid.UUID:
    meta     = result["hexagram_meta"]
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
        # Computed hexagram
        ben_gua_name=meta["ben_gua_name"],
        bian_gua_name=meta["bian_gua_name"],
        palace_name=meta["palace_name"],
        palace_wu_xing=meta["palace_wu_xing"],
        xun_kong=meta["xun_kong"],
        gan_zhi=meta["gan_zhi"],
        lines_json=meta["lines"],
        # Analysis blobs
        wangshuai_json={"results": analysis.get("wangshuai", [])},
        dongbian_json=analysis.get("dongbian", {}),
        patterns_json=analysis.get("patterns", {}),
        jixiong_json=analysis.get("jixiong"),
        yingqi_json={"results": analysis.get("yingqi", [])},
        star_spirits_json=analysis.get("star_spirits", {}),
        # Reports
        report_text=result.get("report_text"),
        report_readable=result.get("report_readable"),
        # Dual
        dual_perspectives_json=(
            analysis.get("perspectives", []) if is_dual else None
        ),
        dual_consensus=analysis.get("consensus") if is_dual else None,
        # Summary
        ji_xiong=result.get("ji_xiong"),
        gua_ju_pattern=result.get("gua_ju_pattern"),
    )
    db.add(session)
    await db.flush()
    return session.id


async def _get_db_cache(db: AsyncSession, fingerprint: str) -> Optional[AnalysisCache]:
    stmt = select(AnalysisCache).where(AnalysisCache.fingerprint == fingerprint)
    row = (await db.execute(stmt)).scalar_one_or_none()
    # NOTE: hit_count / last_hit_at are updated only on the upsert path (_upsert_db_cache),
    # not here, to avoid a spurious DB write on every cache read.
    return row


async def _upsert_db_cache(
    db: AsyncSession,
    fingerprint: str,
    question_type: str,
    is_dual: bool,
    payload: Dict[str, Any],
) -> None:
    existing = (
        await db.execute(
            select(AnalysisCache).where(AnalysisCache.fingerprint == fingerprint)
        )
    ).scalar_one_or_none()

    if existing:
        existing.payload = payload
        existing.hit_count = (existing.hit_count or 0) + 1
        existing.last_hit_at = datetime.now(timezone.utc)
    else:
        row = AnalysisCache(
            fingerprint=fingerprint,
            question_type=question_type,
            is_dual=is_dual,
            payload=payload,
        )
        db.add(row)


def _payload_to_response(payload: Dict[str, Any], from_cache: bool) -> Dict[str, Any]:
    data = dict(payload)
    data["from_cache"] = from_cache

    # Ensure created_at is a datetime
    if isinstance(data.get("created_at"), str):
        data["created_at"] = datetime.fromisoformat(data["created_at"])
    elif "created_at" not in data:
        data["created_at"] = datetime.now(timezone.utc)

    return data


def _orm_to_response(row: ReadingSession) -> Dict[str, Any]:
    lines = row.lines_json or []
    wangshuai = row.wangshuai_json if isinstance(row.wangshuai_json, list) else (row.wangshuai_json or {}).get("results", [])
    yingqi = row.yingqi_json if isinstance(row.yingqi_json, list) else (row.yingqi_json or {}).get("results", [])

    perspectives = None
    if row.dual_perspectives_json:
        # Support both old wrapper format {"perspectives": [...]} and flat list
        dpj = row.dual_perspectives_json
        perspectives = dpj if isinstance(dpj, list) else dpj.get("perspectives")

    return {
        "id": row.id,
        "question_type": row.question_type,
        "question_type_label": QUESTION_TYPE_LABELS.get(row.question_type, row.question_type),
        "question": row.question,
        "querent_name": row.querent_name,
        "is_dual": row.is_dual,
        "ben_gua_name": row.ben_gua_name or "",
        "bian_gua_name": row.bian_gua_name or "",
        "palace_name": row.palace_name or "",
        "palace_wu_xing": row.palace_wu_xing or "",
        "xun_kong": list(row.xun_kong or []),
        "gan_zhi": dict(row.gan_zhi or {}),
        "lines": lines,
        "wangshuai": wangshuai,
        "dongbian": row.dongbian_json or {},
        "patterns": row.patterns_json or {},
        "star_spirits": row.star_spirits_json or {},
        "jixiong": row.jixiong_json,
        "yingqi": yingqi,
        "perspectives": perspectives,
        "dual_consensus": row.dual_consensus,
        "report_text": row.report_text,
        "report_readable": row.report_readable,
        "from_cache": False,
        "created_at": row.created_at,
    }


def _orm_to_summary(row: ReadingSession) -> Dict[str, Any]:
    return {
        "id": row.id,
        "question_type": row.question_type,
        "question_type_label": QUESTION_TYPE_LABELS.get(row.question_type, row.question_type),
        "question": row.question,
        "querent_name": row.querent_name,
        "ben_gua_name": row.ben_gua_name,
        "bian_gua_name": row.bian_gua_name,
        "ji_xiong": row.ji_xiong,
        "gua_ju_pattern": row.gua_ju_pattern,
        "is_dual": row.is_dual,
        "created_at": row.created_at,
    }


def _feedback_to_dict(row: ReadingFeedback) -> Dict[str, Any]:
    return {
        "id": row.id,
        "reading_id": row.reading_id,
        "actual_outcome": row.actual_outcome,
        "feedback_text": row.feedback_text,
        "status": row.status,
        "original_judgement": row.original_judgement,
        "created_at": row.created_at or datetime.now(timezone.utc),
    }


def _template_to_dict(row: HexagramTemplate) -> Dict[str, Any]:
    return {
        "id": row.id,
        "name": row.name,
        "description": row.description,
        "yao_values": row.yao_values,
        "ganzhi_override": row.ganzhi_override,
        "cast_hour": row.cast_hour,
        "default_question_type": row.default_question_type,
        "source_text": row.source_text,
        "created_at": row.created_at,
    }
