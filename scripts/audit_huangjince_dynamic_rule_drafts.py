# -*- coding: utf-8 -*-
"""Audit 《黄金策》 dynamic rule drafts and build a deterministic compile queue.

本脚本只产出审计报告与“下一批待编译”队列，不生成运行时规则，
也不修改 ``data/huangjince_candidate_rules.jsonl``。队列记录用于提示
哪些草稿最适合进入人工拆解/编译流程。
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DEFAULT_DRAFTS_PATH = ROOT / "data" / "huangjince_dynamic_rule_drafts.jsonl"
DEFAULT_AUDIT_OUTPUT = ROOT / "data" / "huangjince_dynamic_rule_draft_audit.json"
DEFAULT_QUEUE_OUTPUT = ROOT / "data" / "huangjince_dynamic_rule_compile_queue.jsonl"

SUPPORTED_FACT_KEYWORDS = {
    "世": "line.is_shi / subject=shi",
    "应": "line.is_ying / subject=ying",
    "用": "subject=primary_yong",
    "爻": "line.exists",
    "动": "line.is_moving / line.moving.*",
    "变": "line.bian.*",
    "化": "line.bian.* / line.moving.*",
    "冲": "relationship.chong",
    "合": "relationship.he",
    "克": "relationship.ke",
    "生": "relationship.sheng",
    "扶": "relationship.sheng / 日月扶助需人工细化",
    "空": "line.is_empty",
    "亡": "line.is_empty",
    "旺": "line.wangshuai.*",
    "衰": "line.wangshuai.*",
    "财": "line.liu_qin",
    "官": "line.liu_qin",
    "鬼": "line.liu_qin",
    "父母": "line.liu_qin",
    "兄弟": "line.liu_qin",
    "子孙": "line.liu_qin",
    "妻财": "line.liu_qin",
    "福德": "line.liu_qin",
}

HIGH_VALUE_SECTIONS = {
    "总断千金赋": 8,
    "求财": 7,
    "婚姻": 7,
    "失脱附盗贼、捕贼民苦饥寒": 6,
    "医药病不求医": 6,
    "出行": 5,
    "功名": 5,
}

POLARITY_WEIGHT = {
    "吉": 3,
    "凶": 3,
    "中性": 2,
    "待审": 0,
}

RUNTIME_ISOLATION_NOTE = "审计队列不被默认动态规则加载器读取；只有人工编译后写入候选规则库才可能参与候选证据层。"


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    """Load JSONL records."""
    with path.open("r", encoding="utf-8") as file:
        return [json.loads(line) for line in file if line.strip()]


def write_jsonl(records: Iterable[dict[str, Any]], output: Path) -> None:
    """Write deterministic JSONL records."""
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="\n") as file:
        for record in records:
            file.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def write_json(record: dict[str, Any], output: Path) -> None:
    """Write deterministic pretty JSON."""
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(record, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def build_compile_queue(drafts: list[dict[str, Any]], *, limit: int | None = None) -> list[dict[str, Any]]:
    """Build ranked manual compile queue from draft-only records."""
    queue = [_queue_record(draft) for draft in drafts if _needs_manual_compile(draft)]
    queue.sort(key=lambda item: (-item["compile_priority_score"], item["source_file"], item["line_start"], item["draft_id"]))
    if limit is not None:
        return queue[:limit]
    return queue


def build_audit_report(drafts: list[dict[str, Any]], queue: list[dict[str, Any]]) -> dict[str, Any]:
    """Build aggregate audit statistics for dynamic rule drafts."""
    by_compilability = Counter(str(draft.get("compilability", "unknown")) for draft in drafts)
    by_section = Counter(str(draft.get("section", "")) for draft in drafts)
    by_polarity = Counter(str(draft.get("polarity", "")) for draft in drafts)
    by_question_type: Counter[str] = Counter()
    for draft in drafts:
        for question_type in draft.get("question_types") or []:
            by_question_type[str(question_type)] += 1

    compiled = [draft for draft in drafts if draft.get("compiled_rule_id")]
    manual = [draft for draft in drafts if _needs_manual_compile(draft)]
    return {
        "source": "huangjince_dynamic_rule_drafts",
        "total_drafts": len(drafts),
        "compiled_drafts": len(compiled),
        "manual_compile_drafts": len(manual),
        "queue_size": len(queue),
        "by_compilability": dict(sorted(by_compilability.items())),
        "by_polarity": dict(sorted(by_polarity.items())),
        "by_question_type": dict(sorted(by_question_type.items())),
        "top_sections": dict(by_section.most_common(12)),
        "top_queue_candidates": [
            {
                "queue_id": item["queue_id"],
                "draft_id": item["draft_id"],
                "section": item["section"],
                "line_start": item["line_start"],
                "compile_priority_score": item["compile_priority_score"],
                "source_text": item["source_text"],
                "reasons": item["compile_priority_reasons"],
            }
            for item in queue[:10]
        ],
        "runtime_isolation": {
            "candidate_rules_path": "data/huangjince_candidate_rules.jsonl",
            "audit_outputs": [
                "data/huangjince_dynamic_rule_draft_audit.json",
                "data/huangjince_dynamic_rule_compile_queue.jsonl",
            ],
            "note": RUNTIME_ISOLATION_NOTE,
        },
    }


def _needs_manual_compile(draft: dict[str, Any]) -> bool:
    return draft.get("draft_status") == "draft_only" and not draft.get("compiled_rule_id")


def _queue_record(draft: dict[str, Any]) -> dict[str, Any]:
    score, reasons = _score_draft(draft)
    return {
        "queue_id": f"compile_queue_{draft['id'].removeprefix('draft_')}",
        "draft_id": draft["id"],
        "classic_judgement_id": draft.get("classic_judgement_id", ""),
        "source": draft.get("source", "huangjince"),
        "source_text": draft.get("source_text", ""),
        "source_file": draft.get("source_file", ""),
        "line_start": draft.get("line_start", 0),
        "line_end": draft.get("line_end", 0),
        "section": draft.get("section", ""),
        "polarity": draft.get("polarity", ""),
        "question_types": list(draft.get("question_types") or []),
        "keywords": list(draft.get("keywords") or []),
        "compile_priority_score": score,
        "compile_priority_reasons": reasons,
        "suggested_fact_targets": _suggested_fact_targets(draft),
        "suggested_next_step": "人工拆分条件 AST 与结论；通过 schema 校验后再晋级到候选规则库。",
        "runtime_isolation": {
            "draft_status": draft.get("draft_status", ""),
            "default_loader": "not_loaded",
            "note": RUNTIME_ISOLATION_NOTE,
        },
        "safety": {
            "allow_override": False,
            "p0_safe": True,
            "notes": "队列项仅用于编译排期，不可直接作为运行时规则。",
        },
    }


def _score_draft(draft: dict[str, Any]) -> tuple[int, list[str]]:
    keywords = list(draft.get("keywords") or [])
    section = str(draft.get("section", ""))
    polarity = str(draft.get("polarity", ""))
    question_types = list(draft.get("question_types") or [])

    score = 0
    reasons: list[str] = []

    supported_keywords = [keyword for keyword in keywords if keyword in SUPPORTED_FACT_KEYWORDS]
    if supported_keywords:
        keyword_score = min(len(supported_keywords), 6) * 4
        score += keyword_score
        reasons.append(f"含 {len(supported_keywords)} 个现有事实抽取器可支持关键词")

    section_score = HIGH_VALUE_SECTIONS.get(section, 0)
    if section_score:
        score += section_score
        reasons.append(f"高价值章节：{section}")

    polarity_score = POLARITY_WEIGHT.get(polarity, 0)
    if polarity_score:
        score += polarity_score
        reasons.append(f"吉凶倾向较明确：{polarity}")

    specific_question_types = [item for item in question_types if item != "other"]
    if specific_question_types:
        score += 3
        reasons.append(f"可绑定问事类型：{','.join(specific_question_types)}")

    text = str(draft.get("source_text", ""))
    if "；" in text or ";" in text:
        score += 1
        reasons.append("断语可按分句拆解")
    if not reasons:
        reasons.append("低优先级：需先补充事实抽取或人工释义")
    return score, reasons


def _suggested_fact_targets(draft: dict[str, Any]) -> list[str]:
    targets = []
    seen = set()
    for keyword in draft.get("keywords") or []:
        target = SUPPORTED_FACT_KEYWORDS.get(keyword)
        if target and target not in seen:
            seen.add(target)
            targets.append(target)
    return targets or ["needs_manual_fact_mapping"]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--drafts", type=Path, default=DEFAULT_DRAFTS_PATH)
    parser.add_argument("--audit-output", type=Path, default=DEFAULT_AUDIT_OUTPUT)
    parser.add_argument("--queue-output", type=Path, default=DEFAULT_QUEUE_OUTPUT)
    parser.add_argument("--limit", type=int, default=None, help="optional queue output limit")
    args = parser.parse_args()

    drafts = load_jsonl(args.drafts)
    queue = build_compile_queue(drafts, limit=args.limit)
    audit = build_audit_report(drafts, queue)
    write_json(audit, args.audit_output)
    write_jsonl(queue, args.queue_output)
    print(f"wrote audit report to {args.audit_output}")
    print(f"wrote {len(queue)} compile queue records to {args.queue_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
