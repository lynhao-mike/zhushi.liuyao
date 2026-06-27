"""
Engine Service — thin async wrapper around the synchronous liuyao library.

Design:
  - All liuyao calls are CPU-bound and synchronous.
  - We offload them to a dedicated ThreadPoolExecutor so FastAPI's event loop
    is never blocked.
  - Results are serialised to plain Python dicts so they can be cached in
    Redis (JSON-serialisable) and stored in PostgreSQL JSONB columns.
"""
from __future__ import annotations

import asyncio
import concurrent.futures
import dataclasses
from time import perf_counter
from typing import Any, Dict, List, Optional

from api.core.config import get_settings
from api.core.exceptions import EngineError
from api.core.logging import get_logger
# Import the existing liuyao library (synchronous)
from liuyao import (
    Hexagram,
    AnalysisReport,
    DualPerspectiveReport,
    run_analysis,
    run_dual_analysis,
    format_report,
    format_dual_report,
    format_readable_report,
)
from liuyao.report_archive import archive_reports
from liuyao.domain.jixiong import DUAL_PERSPECTIVE_TABLE

log = get_logger(__name__)

# ponytail: lazy init so tests/CLI never create the pool; created on first analyze() call
_executor: Optional[concurrent.futures.ThreadPoolExecutor] = None


def _get_executor() -> concurrent.futures.ThreadPoolExecutor:
    global _executor
    if _executor is None:
        settings = get_settings()
        _executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=settings.ENGINE_THREAD_POOL_SIZE,
            thread_name_prefix="liuyao-engine",
        )
    return _executor


def shutdown_executor() -> None:
    global _executor
    if _executor is not None:
        _executor.shutdown(wait=False)
        _executor = None


# ── Serialisation helpers ─────────────────────────────────────────────────────

def _yao_line_to_dict(line) -> Dict[str, Any]:
    # ponytail: dataclasses.asdict tracks YaoLine fields automatically
    return dataclasses.asdict(line)


def _hexagram_input_snapshot(
    *,
    yao_values: List[int],
    year: Optional[int],
    month: Optional[int],
    day: Optional[int],
    hour: int,
    question_type: str,
    is_dual: bool,
    ganzhi_override: Optional[Dict[str, Any]],
    querent_name: Optional[str],
    question: Optional[str],
    meta: Dict[str, Any],
) -> Dict[str, Any]:
    date = f"{year:04d}-{month:02d}-{day:02d}" if year and month and day else None
    return {
        "question": question or "",
        "querent": querent_name or "",
        "question_type": question_type,
        "is_dual": is_dual,
        "date": date,
        "hour": hour,
        "yao_values": list(yao_values),
        "ganzhi_override": ganzhi_override,
        "gan_zhi": meta.get("gan_zhi"),
        "xun_kong": meta.get("xun_kong"),
        "ben_gua_name": meta.get("ben_gua_name"),
        "bian_gua_name": meta.get("bian_gua_name"),
        "palace_name": meta.get("palace_name"),
        "palace_wu_xing": meta.get("palace_wu_xing"),
        "shi_pos": meta.get("shi_pos"),
        "ying_pos": meta.get("ying_pos"),
        "lines": meta.get("lines"),
    }


def _hexagram_meta(h: Hexagram) -> Dict[str, Any]:
    return {
        "ben_gua_name":   h.ben_gua_name,
        "bian_gua_name":  h.bian_gua_name,
        "palace_name":    h.palace_name,
        "palace_wu_xing": h.palace_wu_xing,
        "palace_order":   h.palace_order,
        "xun_kong":       list(h.xun_kong),
        "gan_zhi":        dict(h.gan_zhi),
        "shi_pos":        h.shi_pos,
        "ying_pos":       h.ying_pos,
        "lines":          [_yao_line_to_dict(l) for l in h.lines],
    }


def _report_to_dict(report: AnalysisReport) -> Dict[str, Any]:
    return {
        "yong_shen_liu_qin": report.yong_shen_liu_qin,
        "ji_shen_liu_qin":   report.ji_shen_liu_qin,
        "perspective_label": report.perspective_label,
        "wangshuai":         report.wangshuai_results,
        "dongbian":          report.dongbian_results,
        "patterns":          report.patterns_results,
        "star_spirits":      report.star_spirits,
        "jixiong":           report.jixiong_result,
        "yingqi":            report.yingqi_results,
    }


def _dual_report_to_dict(dual: DualPerspectiveReport) -> Dict[str, Any]:
    return {
        "consensus":    dual.consensus,
        "perspectives": [_report_to_dict(p) for p in dual.perspectives],
        "wangshuai":    dual.wangshuai_results,
        "dongbian":     dual.dongbian_results,
        "star_spirits": dual.star_spirits,
    }


# ── Core synchronous worker (runs inside the thread pool) ────────────────────

def _build_hexagram(
    yao_values: List[int],
    year: Optional[int],
    month: Optional[int],
    day: Optional[int],
    hour: int,
    ganzhi_override: Optional[Dict[str, Any]],
) -> Hexagram:
    if ganzhi_override:
        return Hexagram.from_ganzhi(
            yao_values,
            month_zhi=ganzhi_override["month_zhi"],
            day_zhi=ganzhi_override["day_zhi"],
            day_gan=ganzhi_override.get("day_gan"),
            xun_kong=ganzhi_override.get("xun_kong"),
            year_gan=ganzhi_override.get("year_gan", "甲"),
            year_zhi=ganzhi_override.get("year_zhi", "子"),
            month_gan=ganzhi_override.get("month_gan", "甲"),
            hour=hour,
        )
    return Hexagram(yao_values, year, month, day, hour)


def _run_analysis_sync(
    yao_values: List[int],
    year: Optional[int],
    month: Optional[int],
    day: Optional[int],
    hour: int,
    question_type: str,
    is_dual: bool,
    ganzhi_override: Optional[Dict[str, Any]],
    querent_name: Optional[str],
    question: Optional[str],
) -> Dict[str, Any]:
    """Full synchronous analysis — runs in thread pool."""
    try:
        h = _build_hexagram(yao_values, year, month, day, hour, ganzhi_override)
    except Exception as exc:
        raise EngineError(f"Hexagram construction failed: {exc}") from exc

    meta = _hexagram_meta(h)

    try:
        analysis_started = perf_counter()
        if is_dual:
            dual = run_dual_analysis(h, question_type)
            analysis_elapsed_ms = round((perf_counter() - analysis_started) * 1000, 3)

            report_started = perf_counter()
            report_meta = {
                "question": question or "",
                "querent":  querent_name or "",
                "hexagram_input": _hexagram_input_snapshot(
                    yao_values=yao_values,
                    year=year,
                    month=month,
                    day=day,
                    hour=hour,
                    question_type=question_type,
                    is_dual=is_dual,
                    ganzhi_override=ganzhi_override,
                    querent_name=querent_name,
                    question=question,
                    meta=meta,
                ),
            }
            report_text     = format_dual_report(dual)
            report_readable = format_readable_report(dual, meta=report_meta)
            report_files = archive_reports(
                report_text=report_text,
                report_readable=report_readable,
                meta=report_meta,
            )
            report_elapsed_ms = round((perf_counter() - report_started) * 1000, 3)
            analysis_data   = _dual_report_to_dict(dual)
            log.info(
                "engine_analysis_sync_done",
                is_dual=True,
                question_type=question_type,
                analysis_elapsed_ms=analysis_elapsed_ms,
                report_elapsed_ms=report_elapsed_ms,
            )

            return {
                "hexagram_meta":  meta,
                "is_dual":        True,
                "analysis":       analysis_data,
                "report_text":    report_text,
                "report_readable": report_readable,
                "report_files":   report_files,
                # Summary fields (for DB denormalisation)
                "ji_xiong":       _extract_ji_xiong_dual(dual),
                "gua_ju_pattern": _extract_pattern_dual(dual),
            }
        else:
            report      = run_analysis(h, question_type)
            analysis_elapsed_ms = round((perf_counter() - analysis_started) * 1000, 3)

            report_started = perf_counter()
            report_meta = {
                "question": question or "",
                "querent":  querent_name or "",
                "hexagram_input": _hexagram_input_snapshot(
                    yao_values=yao_values,
                    year=year,
                    month=month,
                    day=day,
                    hour=hour,
                    question_type=question_type,
                    is_dual=is_dual,
                    ganzhi_override=ganzhi_override,
                    querent_name=querent_name,
                    question=question,
                    meta=meta,
                ),
            }
            report_text = format_report(report)
            report_readable = format_readable_report(report, meta=report_meta)
            report_files = archive_reports(
                report_text=report_text,
                report_readable=report_readable,
                meta=report_meta,
            )
            report_elapsed_ms = round((perf_counter() - report_started) * 1000, 3)
            analysis_data = _report_to_dict(report)
            log.info(
                "engine_analysis_sync_done",
                is_dual=False,
                question_type=question_type,
                analysis_elapsed_ms=analysis_elapsed_ms,
                report_elapsed_ms=report_elapsed_ms,
            )

            return {
                "hexagram_meta":  meta,
                "is_dual":        False,
                "analysis":       analysis_data,
                "report_text":    report_text,
                "report_readable": report_readable,
                "report_files":   report_files,
                "ji_xiong":       report.jixiong_result.get("ji_xiong", "平"),
                "gua_ju_pattern": report.jixiong_result.get("pattern", ""),
            }
    except Exception as exc:
        raise EngineError(f"Analysis pipeline failed: {exc}") from exc


def _extract_ji_xiong_dual(dual: DualPerspectiveReport) -> str:
    """Pick the dominant ji_xiong from the first perspective."""
    if dual.perspectives:
        return dual.perspectives[0].jixiong_result.get("ji_xiong", "平")
    return "平"


def _extract_pattern_dual(dual: DualPerspectiveReport) -> str:
    if dual.perspectives:
        return dual.perspectives[0].jixiong_result.get("pattern", "")
    return ""


# ── Public async interface ────────────────────────────────────────────────────

async def analyze(
    yao_values: List[int],
    year: Optional[int],
    month: Optional[int],
    day: Optional[int],
    hour: int,
    question_type: str,
    is_dual: bool,
    ganzhi_override: Optional[Dict[str, Any]],
    querent_name: Optional[str],
    question: Optional[str],
) -> Dict[str, Any]:
    """
    Async entry point. Offloads the CPU-bound analysis to the thread pool.
    """
    loop = asyncio.get_running_loop()
    started = perf_counter()
    result = await loop.run_in_executor(
        _get_executor(),
        _run_analysis_sync,
        yao_values,
        year,
        month,
        day,
        hour,
        question_type,
        is_dual,
        ganzhi_override,
        querent_name,
        question,
    )
    log.info(
        "engine_analysis_async_done",
        question_type=question_type,
        is_dual=is_dual,
        elapsed_ms=round((perf_counter() - started) * 1000, 3),
        thread_pool_size=_get_executor()._max_workers,
    )
    return result


def should_use_dual(question_type: str, is_dual_override: Optional[bool]) -> bool:
    """Resolve dual-perspective flag with sensible defaults."""
    if is_dual_override is not None:
        return is_dual_override
    return question_type in DUAL_PERSPECTIVE_TABLE
