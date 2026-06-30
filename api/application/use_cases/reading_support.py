"""
Shared support helpers for reading use cases.

ponytail: keep helpers concrete and local to reading use cases; add abstractions only if a second caller appears.
"""
from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from liuyao import QUESTION_TYPE_LABELS, archive_reports


def ensure_report_files(payload: dict[str, Any]) -> bool:
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


def build_payload(
    req,
    result: dict[str, Any],
    is_dual: bool,
) -> dict[str, Any]:
    meta = result["hexagram_meta"]
    analysis = result["analysis"]

    payload: dict[str, Any] = {
        "question_type": req.question_type,
        "question_type_label": QUESTION_TYPE_LABELS.get(req.question_type, req.question_type),
        "question": req.question,
        "querent_name": req.querent_name,
        "is_dual": is_dual,
        "ben_gua_name": meta["ben_gua_name"],
        "bian_gua_name": meta["bian_gua_name"],
        "palace_name": meta["palace_name"],
        "palace_wu_xing": meta["palace_wu_xing"],
        "xun_kong": meta["xun_kong"],
        "gan_zhi": meta["gan_zhi"],
        "lines": meta["lines"],
        "wangshuai": analysis.get("wangshuai", []),
        "dongbian": analysis.get("dongbian", {}),
        "patterns": analysis.get("patterns", {}),
        "star_spirits": analysis.get("star_spirits", {}),
        "report_text": result.get("report_text"),
        "report_readable": result.get("report_readable"),
        "report_files": result.get("report_files", []),
    }

    if is_dual:
        payload["dual_consensus"] = analysis.get("consensus")
        payload["perspectives"] = [
            {
                "perspective_label": p["perspective_label"],
                "yong_shen_liu_qin": p["yong_shen_liu_qin"],
                "jixiong": p["jixiong"],
                "yingqi": p["yingqi"],
            }
            for p in analysis.get("perspectives", [])
        ]
        payload["jixiong"] = None
        payload["yingqi"] = None
    else:
        payload["jixiong"] = analysis.get("jixiong")
        payload["yingqi"] = analysis.get("yingqi", [])
        payload["perspectives"] = None
        payload["dual_consensus"] = None

    return payload


def payload_to_response(payload: dict[str, Any], from_cache: bool) -> dict[str, Any]:
    data = dict(payload)
    data["from_cache"] = from_cache

    if isinstance(data.get("created_at"), str):
        data["created_at"] = datetime.fromisoformat(data["created_at"])
    elif "created_at" not in data:
        data["created_at"] = datetime.now(UTC)

    return data


def orm_to_response(row) -> dict[str, Any]:
    lines = row.lines_json or []
    wangshuai = row.wangshuai_json if isinstance(row.wangshuai_json, list) else (row.wangshuai_json or {}).get("results", [])
    yingqi = row.yingqi_json if isinstance(row.yingqi_json, list) else (row.yingqi_json or {}).get("results", [])

    perspectives = None
    if row.dual_perspectives_json:
        dpj = row.dual_perspectives_json
        perspectives = dpj if isinstance(dpj, list) else dpj.get("perspectives")

    # GET must be read-only. Report files are archived during create/cache recovery,
    # not regenerated on every detail request.
    report_files: list[str] = []

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


def orm_to_summary(row) -> dict[str, Any]:
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


def feedback_to_dict(row) -> dict[str, Any]:
    return {
        "id": row.id,
        "reading_id": row.reading_id,
        "actual_outcome": row.actual_outcome,
        "feedback_text": row.feedback_text,
        "status": row.status,
        "original_judgement": row.original_judgement,
        "created_at": row.created_at or datetime.now(UTC),
    }


def template_to_dict(row) -> dict[str, Any]:
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
