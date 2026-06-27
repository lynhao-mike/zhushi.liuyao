"""
Reading Service — orchestrates the full request lifecycle:

  1. Resolve dual-perspective flag
  2. Build cache fingerprint
  3. ReadingCacheRepo.get()  → hit: return cached payload
  4. Run analysis engine (thread pool)
  5. ReadingRepo.persist()   → INSERT ReadingSession
  6. ReadingCacheRepo.set()  → UPSERT AnalysisCache + warm Redis
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
from liuyao.report_archive import archive_reports

log = get_logger(__name__)
settings = get_settings()


# ── ReadingCacheRepo ──────────────────────────────────────────────────────────

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
            if _ensure_report_files(payload):
                await set_cache(cache_key, payload, settings.CACHE_TTL_ANALYSIS)
            return payload

        row = await self._get_db_row(fingerprint)
        if row:
            log.info("reading_db_cache_hit", fingerprint=fingerprint)
            payload = row.payload
            if _ensure_report_files(payload):
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


# ── ReadingRepo ───────────────────────────────────────────────────────────────

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
            dual_perspectives_json=(
                analysis.get("perspectives", []) if is_dual else None
            ),
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
        rows  = (await self._db.execute(stmt.offset((page - 1) * size).limit(size))).scalars().all()
        return list(rows), total

    async def delete(self, reading_id: uuid.UUID) -> None:
        row = await self._db.get(ReadingSession, reading_id)
        if not row:
            raise NotFoundError(f"Reading {reading_id} not found")
        await self._db.delete(row)


# ── Create Reading ────────────────────────────────────────────────────────────

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
        return _payload_to_response(cached_payload, from_cache=True)

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

    payload = _build_payload(req, result, is_dual)

    repo = ReadingRepo(db)
    session_id = await repo.persist(req, result, is_dual, fingerprint)
    payload["id"] = str(session_id)
    payload["created_at"] = datetime.now(timezone.utc).isoformat()

    await cache.set(fingerprint, req.question_type, is_dual, payload)

    return _payload_to_response(payload, from_cache=False)


# ── Get / List ────────────────────────────────────────────────────────────────

async def get_reading(reading_id: uuid.UUID, db: AsyncSession) -> Dict[str, Any]:
    row = await ReadingRepo(db).get(reading_id)
    return _orm_to_response(row)


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
    items = [_orm_to_summary(r) for r in rows]
    pages = (total + size - 1) // size
    result = {"items": items, "total": total, "page": page, "size": size, "pages": pages}
    await set_cache(cache_key, result, settings.CACHE_TTL_HEXAGRAM_LIST)
    return result


async def delete_reading(reading_id: uuid.UUID, db: AsyncSession) -> None:
    await ReadingRepo(db).delete(reading_id)
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

def _ensure_report_files(payload: Dict[str, Any]) -> bool:
    if payload.get("report_files"):
        return False
    payload["report_files"] = archive_reports(
        report_text=payload.get("report_text"),
        report_readable=payload.get("report_readable"),
        meta={
            "question": payload.get("question") or "",
            "querent": payload.get("querent_name") or "",
            "hexagram_input": {
                "question": payload.get("question") or "",
                "querent": payload.get("querent_name") or "",
                "question_type": payload.get("question_type"),
                "is_dual": payload.get("is_dual"),
                "gan_zhi": payload.get("gan_zhi"),
                "xun_kong": payload.get("xun_kong"),
                "ben_gua_name": payload.get("ben_gua_name"),
                "bian_gua_name": payload.get("bian_gua_name"),
                "palace_name": payload.get("palace_name"),
                "palace_wu_xing": payload.get("palace_wu_xing"),
                "lines": payload.get("lines"),
            },
        },
    )
    return True


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
        "ben_gua_name":   meta["ben_gua_name"],
        "bian_gua_name":  meta["bian_gua_name"],
        "palace_name":    meta["palace_name"],
        "palace_wu_xing": meta["palace_wu_xing"],
        "xun_kong":       meta["xun_kong"],
        "gan_zhi":        meta["gan_zhi"],
        "lines":          meta["lines"],
        "wangshuai": analysis.get("wangshuai", []),
        "dongbian":  analysis.get("dongbian", {}),
        "patterns":  analysis.get("patterns", {}),
        "star_spirits": analysis.get("star_spirits", {}),
        "report_text":     result.get("report_text"),
        "report_readable": result.get("report_readable"),
        "report_files":    result.get("report_files", []),
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


def _payload_to_response(payload: Dict[str, Any], from_cache: bool) -> Dict[str, Any]:
    data = dict(payload)
    data["from_cache"] = from_cache

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
        dpj = row.dual_perspectives_json
        perspectives = dpj if isinstance(dpj, list) else dpj.get("perspectives")

    # GET must be read-only. Report files are archived during create/cache recovery,
    # not regenerated on every detail request.
    report_files: List[str] = []

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
        "report_files": report_files,
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
