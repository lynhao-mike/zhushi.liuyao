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
from dataclasses import asdict, fields
from typing import Any, Dict, List, Optional

from api.core.config import get_settings
from api.core.exceptions import EngineError
from api.core.logging import get_logger
from api.interfaces.http.schemas.reading import GanzhiOverride

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
from liuyao.domain.jixiong import DUAL_PERSPECTIVE_TABLE

log = get_logger(__name__)
settings = get_settings()

# Dedicated thread pool — keeps CPU-bound work off the event loop
_executor = concurrent.futures.ThreadPoolExecutor(
    max_workers=settings.ENGINE_THREAD_POOL_SIZE,
    thread_name_prefix="liuyao-engine",
)


# ── Serialisation helpers ─────────────────────────────────────────────────────

def _yao_line_to_dict(line) -> Dict[str, Any]:
    return {
        "position":      line.position,
        "yao_type":      line.yao_type,
        "yin_yang":      line.yin_yang,
        "is_moving":     line.is_moving,
        "tian_gan":      line.tian_gan,
        "di_zhi":        line.di_zhi,
        "wu_xing":       line.wu_xing,
        "liu_qin":       line.liu_qin,
        "liu_shen":      line.liu_shen,
        "is_shi":        line.is_shi,
        "is_ying":       line.is_ying,
        "is_xun_kong":   line.is_xun_kong,
        "bian_tian_gan": line.bian_tian_gan,
        "bian_di_zhi":   line.bian_di_zhi,
        "bian_wu_xing":  line.bian_wu_xing,
        "bian_liu_qin":  line.bian_liu_qin,
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
        if is_dual:
            dual = run_dual_analysis(h, question_type)
            report_text     = format_dual_report(dual)
            report_readable = format_readable_report(dual, meta={
                "question": question or "",
                "querent":  querent_name or "",
            })
            analysis_data   = _dual_report_to_dict(dual)

            return {
                "hexagram_meta":  meta,
                "is_dual":        True,
                "analysis":       analysis_data,
                "report_text":    report_text,
                "report_readable": report_readable,
                # Summary fields (for DB denormalisation)
                "ji_xiong":       _extract_ji_xiong_dual(dual),
                "gua_ju_pattern": _extract_pattern_dual(dual),
            }
        else:
            report      = run_analysis(h, question_type)
            report_text = format_report(report)
            report_readable = format_readable_report(report, meta={
                "question": question or "",
                "querent":  querent_name or "",
            })
            analysis_data = _report_to_dict(report)

            return {
                "hexagram_meta":  meta,
                "is_dual":        False,
                "analysis":       analysis_data,
                "report_text":    report_text,
                "report_readable": report_readable,
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
    result = await loop.run_in_executor(
        _executor,
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
    return result


def should_use_dual(question_type: str, is_dual_override: Optional[bool]) -> bool:
    """Resolve dual-perspective flag with sensible defaults."""
    if is_dual_override is not None:
        return is_dual_override
    return question_type in DUAL_PERSPECTIVE_TABLE
