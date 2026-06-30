"""Build auditable draft dynamic rules from 《黄金策》 candidate judgements.

草稿文件用于“全量规则化”的审计与编译排队，不作为运行时默认执行
规则库。只有已经在 ``data/huangjince_candidate_rules.jsonl`` 中人工审过的
规则会被映射为 ``auto_compilable`` 草稿；其余断语保留可追溯来源，并以
``not_compilable`` 标记隔离，避免未审古籍断语进入吉凶判断。
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Iterable
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from liuyao.domain.classic_judgements import ClassicJudgement, load_classic_judgements
from liuyao.domain.rules.classic_rule_schema import validate_classic_rules

DEFAULT_JUDGEMENTS_PATH = ROOT / "data" / "classic_judgements.jsonl"
DEFAULT_REVIEWED_RULES_PATH = ROOT / "data" / "huangjince_candidate_rules.jsonl"
DEFAULT_OUTPUT = ROOT / "data" / "huangjince_dynamic_rule_drafts.jsonl"

DRAFT_SAFETY_NOTES = "草稿层只用于审计与编译排队；默认运行时不加载，不覆盖P0或一般吉凶终局。"
NOT_COMPILABLE_CONDITION = {
    "fact_type": "line.exists",
    "subject": "__manual_review_required__",
    "relation": "is_true",
}


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    """Load a JSONL file into dictionaries."""
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as file:
        return [json.loads(line) for line in file if line.strip()]


def write_jsonl(records: Iterable[dict[str, Any]], output: Path) -> None:
    """Write records as deterministic JSONL."""
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="\n") as file:
        for record in records:
            file.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def build_drafts(
    judgements_path: Path | None = None,
    reviewed_rules_path: Path | None = None,
) -> list[dict[str, Any]]:
    """Build auditable draft dynamic rules from extracted classic judgements."""
    judgements = load_classic_judgements(judgements_path or DEFAULT_JUDGEMENTS_PATH)
    reviewed_rules = load_jsonl(reviewed_rules_path or DEFAULT_REVIEWED_RULES_PATH)
    reviewed_by_source = {_source_key(rule): rule for rule in reviewed_rules}

    drafts = []
    for judgement in judgements:
        reviewed_rule = reviewed_by_source.get(_source_key_from_judgement(judgement))
        if reviewed_rule:
            drafts.append(_compiled_draft(judgement, reviewed_rule))
        else:
            drafts.append(_manual_review_draft(judgement))
    return drafts


def assert_drafts_are_schema_safe(drafts: Iterable[dict[str, Any]]) -> None:
    """Validate that every draft remains compatible with the dynamic rule schema."""
    issues = validate_classic_rules(drafts)
    if issues:
        formatted = "; ".join(f"{issue.path}: {issue.message}" for issue in issues)
        raise ValueError(f"invalid dynamic rule drafts: {formatted}")


def _source_key(rule: dict[str, Any]) -> tuple[str, str, int, str]:
    return (
        str(rule.get("source", "")),
        str(rule.get("source_file", "")),
        int(rule.get("line_start", 0) or 0),
        str(rule.get("source_text", "")),
    )


def _source_key_from_judgement(judgement: ClassicJudgement) -> tuple[str, str, int, str]:
    return (
        judgement.source,
        judgement.source_file,
        judgement.line_start,
        judgement.raw_text,
    )


def _compiled_draft(judgement: ClassicJudgement, reviewed_rule: dict[str, Any]) -> dict[str, Any]:
    draft = dict(reviewed_rule)
    draft.update(
        {
            "id": f"draft_{reviewed_rule['id']}",
            "classic_judgement_id": judgement.id,
            "compiled_rule_id": reviewed_rule["id"],
            "draft_status": "draft_only",
            "keywords": list(judgement.keywords),
            "polarity": judgement.polarity,
            "question_types": list(judgement.question_types),
            "compile_notes": "已存在人工审查候选动态规则；草稿仅用于追溯与批量审计，不作为默认执行入口。",
        }
    )
    draft["execution_tier"] = "candidate_only"
    draft["safety"] = _safe_safety(reviewed_rule.get("safety"))
    return draft


def _manual_review_draft(judgement: ClassicJudgement) -> dict[str, Any]:
    ji_xiong = _draft_ji_xiong(judgement.polarity)
    return {
        "id": f"draft_{judgement.id}",
        "classic_judgement_id": judgement.id,
        "source": judgement.source,
        "source_text": judgement.raw_text,
        "source_file": judgement.source_file,
        "line_start": judgement.line_start,
        "line_end": judgement.line_end,
        "section": judgement.section,
        "review_status": "candidate",
        "compilability": "not_compilable",
        "execution_tier": "candidate_only",
        "priority": 1,
        "conditions": dict(NOT_COMPILABLE_CONDITION),
        "conclusion": {
            "ji_xiong": ji_xiong,
            "pattern": "经典草稿：待人工编译",
            "explanation": f"《黄金策》原文“{judgement.raw_text}”尚未编译为可执行条件 AST；仅保留为审计草稿，不参与吉凶判断。",
        },
        "effects": [{"type": "sign", "value": "draft_only_manual_review_required"}],
        "safety": _safe_safety(None),
        "draft_status": "draft_only",
        "keywords": list(judgement.keywords),
        "polarity": judgement.polarity,
        "question_types": list(judgement.question_types),
        "compile_notes": "未识别为可安全自动编译的条件 AST；保留来源、断语和分类，等待人工拆解事实与结论。",
    }


def _draft_ji_xiong(polarity: str) -> str:
    if polarity == "吉":
        return "吉"
    if polarity == "凶":
        return "凶"
    return "平"


def _safe_safety(safety: Any) -> dict[str, Any]:
    notes = DRAFT_SAFETY_NOTES
    if isinstance(safety, dict) and safety.get("notes"):
        notes = f"{safety['notes']} {DRAFT_SAFETY_NOTES}"
    return {
        "allow_override": False,
        "p0_safe": True,
        "notes": notes,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--judgements", type=Path, default=DEFAULT_JUDGEMENTS_PATH)
    parser.add_argument("--reviewed-rules", type=Path, default=DEFAULT_REVIEWED_RULES_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--no-validate", action="store_true", help="skip schema compatibility validation")
    args = parser.parse_args()

    drafts = build_drafts(args.judgements, args.reviewed_rules)
    if not args.no_validate:
        assert_drafts_are_schema_safe(drafts)
    write_jsonl(drafts, args.output)
    print(f"wrote {len(drafts)} draft dynamic rules to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
