# -*- coding: utf-8 -*-
"""Auto-compile conservative 《黄金策》 dynamic candidate rules.

本脚本解决“人工编译门槛太高”的问题：只把已经能被现有
``ClassicRuleFacts`` 与动态条件 AST 明确表达的高置信断语，按保守模板
合并进 ``data/huangjince_candidate_rules.jsonl``。脚本不会把刑、害、墓、
任意爻量词等尚未完整支持的概念强行编译，所有输出仍停留在
``candidate_only`` 候选证据层，不覆盖 P0 或一般吉凶主判。
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Callable, Iterable

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from liuyao.domain.rules.classic_rule_schema import validate_classic_rules

DEFAULT_JUDGEMENTS_PATH = ROOT / "data" / "classic_judgements.jsonl"
DEFAULT_CANDIDATE_RULES_PATH = ROOT / "data" / "huangjince_candidate_rules.jsonl"

SAFETY_NOTES = "自动保守模板生成；候选层只输出证据，stop=False，不直接改变P0或一般吉凶终局。"
PARTIAL_FACT_NOTES = "仅编译现有事实抽取器可表达的部分；未覆盖的刑、害、墓、量词等古籍概念继续留待后续事实扩展。"

RuleBuilder = Callable[[dict[str, Any]], dict[str, Any] | list[dict[str, Any]]]


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    """Load JSONL records from a path."""
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as file:
        return [json.loads(line) for line in file if line.strip()]


def write_jsonl(records: Iterable[dict[str, Any]], output: Path) -> None:
    """Write records as compact deterministic JSONL."""
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="\n") as file:
        for record in records:
            file.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")


def build_auto_compiled_rules(judgements: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Build conservative auto-compiled rules for known high-confidence judgements."""
    judgements_by_id = {str(item.get("id")): item for item in judgements}
    rules: list[dict[str, Any]] = []
    for judgement_id, builder in AUTO_COMPILE_TEMPLATES.items():
        judgement = judgements_by_id.get(judgement_id)
        if judgement:
            built = builder(judgement)
            if isinstance(built, list):
                rules.extend(built)
            else:
                rules.append(built)
    issues = validate_classic_rules(rules)
    if issues:
        formatted = "; ".join(f"{issue.path}: {issue.message}" for issue in issues)
        raise ValueError(f"invalid auto-compiled rules: {formatted}")
    return rules


def merge_candidate_rules(existing: Iterable[dict[str, Any]], generated: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Merge generated rules into candidate rules by id while preserving existing order."""
    generated_by_id = {rule["id"]: rule for rule in generated}
    merged: list[dict[str, Any]] = []
    seen: set[str] = set()

    for record in existing:
        rule_id = str(record.get("id", ""))
        if not rule_id or rule_id in seen:
            continue
        merged.append(generated_by_id.get(rule_id, record))
        seen.add(rule_id)

    for rule in generated:
        rule_id = rule["id"]
        if rule_id not in seen:
            merged.append(rule)
            seen.add(rule_id)

    issues = validate_classic_rules(merged)
    if issues:
        formatted = "; ".join(f"{issue.path}: {issue.message}" for issue in issues)
        raise ValueError(f"invalid merged candidate rules: {formatted}")
    return merged


def _base_rule(
    judgement: dict[str, Any],
    *,
    rule_id: str,
    priority: int,
    conditions: dict[str, Any],
    ji_xiong: str,
    pattern: str,
    explanation: str,
    effects: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "id": rule_id,
        "source": "huangjince",
        "source_text": str(judgement["raw_text"]),
        "source_file": str(judgement["source_file"]),
        "line_start": int(judgement["line_start"]),
        "line_end": int(judgement["line_end"]),
        "section": str(judgement["section"]),
        "review_status": "candidate",
        "compilability": "auto_compilable",
        "execution_tier": "candidate_only",
        "priority": priority,
        "conditions": conditions,
        "conclusion": {
            "ji_xiong": ji_xiong,
            "pattern": pattern,
            "explanation": explanation,
        },
        "effects": effects,
        "safety": {
            "allow_override": False,
            "p0_safe": True,
            "notes": f"{SAFETY_NOTES} {PARTIAL_FACT_NOTES}",
        },
    }


def _question_type(question_type: str) -> dict[str, Any]:
    return {"fact_type": "question.type", "relation": "eq", "value": question_type}


def _line_exists(subject: str) -> dict[str, Any]:
    return {"fact_type": "line.exists", "subject": subject, "relation": "is_true"}


def _line_liu_qin(subject: str, liu_qin: str) -> dict[str, Any]:
    return {"fact_type": "line.liu_qin", "subject": subject, "relation": "eq", "value": liu_qin}


def _relationship(relation: str, subject: str, object_: str) -> dict[str, Any]:
    return {"fact_type": f"relationship.{relation}", "subject": subject, "object": object_, "relation": "is_true"}


def _primary_yong_moving_decline(judgement: dict[str, Any]) -> dict[str, Any]:
    return _base_rule(
        judgement,
        rule_id="classic_huangjince_dynamic_primary_yong_moving_decline",
        priority=130,
        conditions={
            "op": "AND",
            "children": [
                _question_type("bing"),
                _line_exists("primary_yong"),
                {"fact_type": "line.is_moving", "subject": "primary_yong", "relation": "is_true"},
                {
                    "op": "OR",
                    "children": [
                        {"fact_type": "line.wangshuai.overall", "subject": "primary_yong", "relation": "eq", "value": "衰"},
                        {"fact_type": "line.is_empty", "subject": "primary_yong", "relation": "is_true"},
                        {"fact_type": "line.moving.trend_shuai", "subject": "primary_yong", "relation": "contains", "value": "回头克"},
                        {"fact_type": "line.moving.trend_shuai", "subject": "primary_yong", "relation": "contains", "value": "化破"},
                        {"fact_type": "line.moving.trend_shuai", "subject": "primary_yong", "relation": "contains", "value": "化绝"},
                    ],
                },
            ],
        },
        ji_xiong="凶",
        pattern="经典候选：用爻动而趋衰",
        explanation="《黄金策》云“主象休囚，怕见刑冲克害；用爻变动，忌遭死墓绝空”。当前主用神发动且见休囚、空亡或化绝/化破/回头克等趋衰信号，可作事体根基受损的候选证据；未编译刑、害、墓等未覆盖概念，且不覆盖核心主判。",
        effects=[
            {"type": "sign", "value": "primary_yong_moving_decline"},
            {"type": "score_delta", "value": -1},
        ],
    )


def _shi_ying_empty_he(judgement: dict[str, Any]) -> dict[str, Any]:
    return _base_rule(
        judgement,
        rule_id="classic_huangjince_dynamic_shi_ying_empty_he",
        priority=126,
        conditions={
            "op": "AND",
            "children": [
                _question_type("cai"),
                _line_exists("shi"),
                _line_exists("ying"),
                {"fact_type": "relationship.he", "subject": "shi", "object": "ying", "relation": "is_true"},
                {
                    "op": "OR",
                    "children": [
                        {"fact_type": "line.is_empty", "subject": "shi", "relation": "is_true"},
                        {"fact_type": "line.is_empty", "subject": "ying", "relation": "is_true"},
                    ],
                },
            ],
        },
        ji_xiong="平",
        pattern="经典候选：世应空合虚约",
        explanation="《黄金策》云“世应二爻空合，虚约难凭”。当前世应相合但世爻或应爻空亡，可作为约定虽有合意但根基虚浮、难凭落实的候选证据；仍为候选参考，不覆盖求财主判。",
        effects=[
            {"type": "sign", "value": "shi_ying_empty_agreement"},
            {"type": "block", "value": "empty_he_unreliable"},
        ],
    )


def _chuxing_ying_ke_shi(judgement: dict[str, Any]) -> dict[str, Any]:
    return _base_rule(
        judgement,
        rule_id="classic_huangjince_dynamic_chuxing_ying_ke_shi",
        priority=116,
        conditions={
            "op": "AND",
            "children": [
                _question_type("chuxing"),
                _line_exists("shi"),
                _line_exists("ying"),
                {"fact_type": "relationship.ke", "subject": "ying", "object": "shi", "relation": "is_true"},
            ],
        },
        ji_xiong="凶",
        pattern="经典候选：出行应克世不利",
        explanation="《黄金策》云“应克世爻，无问公私皆不利”。当前出行问事中应爻五行克世爻，可作为外部目的地、对方或环境压制自身的候选证据；仍为候选参考，不覆盖核心吉凶。",
        effects=[
            {"type": "sign", "value": "travel_external_overcomes_self"},
            {"type": "score_delta", "value": -1},
        ],
    )


def _chuxing_ying_empty(judgement: dict[str, Any]) -> dict[str, Any]:
    return _base_rule(
        judgement,
        rule_id="classic_huangjince_dynamic_chuxing_ying_empty",
        priority=112,
        conditions={
            "op": "AND",
            "children": [
                _question_type("chuxing"),
                _line_exists("ying"),
                {"fact_type": "line.is_empty", "subject": "ying", "relation": "is_true"},
            ],
        },
        ji_xiong="平",
        pattern="经典候选：出行应空难成",
        explanation="《黄金策》云“应若空亡，难望谋成事就”。当前出行问事中应爻空亡，可作为目标、对方或外部条件落空的候选证据；仍为候选参考，不覆盖核心吉凶。",
        effects=[
            {"type": "sign", "value": "travel_response_empty"},
            {"type": "block", "value": "external_target_empty"},
        ],
    )


def _hun_shi_ying_relationships(judgement: dict[str, Any]) -> dict[str, Any]:
    return _base_rule(
        judgement,
        rule_id="classic_huangjince_dynamic_hun_shi_ying_relationships",
        priority=125,
        conditions={
            "op": "AND",
            "children": [
                _question_type("hun_male"),
                _line_exists("shi"),
                _line_exists("ying"),
                {
                    "op": "OR",
                    "children": [
                        _relationship("sheng", "ying", "shi"),
                        _relationship("ke", "shi", "ying"),
                    ],
                },
            ],
        },
        ji_xiong="平",
        pattern="经典候选：婚姻世应生克成局",
        explanation="《黄金策》云“应生世，悦服成亲；世克应，用强劫娶”。当前婚姻问事中见应生世或世克应，可作为双方关系推动成局的候选证据；其中世克应只保守记录为主动性过强，不直接作吉断，不覆盖核心主判。",
        effects=[{"type": "sign", "value": "marriage_shi_ying_relation_drives_match"}],
    )


def _hun_shi_ying_he(judgement: dict[str, Any]) -> dict[str, Any]:
    return _base_rule(
        judgement,
        rule_id="classic_huangjince_dynamic_hun_shi_ying_he",
        priority=124,
        conditions={
            "op": "AND",
            "children": [
                _question_type("hun_male"),
                _line_exists("shi"),
                _line_exists("ying"),
                _relationship("he", "shi", "ying"),
            ],
        },
        ji_xiong="吉",
        pattern="经典候选：婚姻世应相合",
        explanation="《黄金策》云“世合应应合世，终成种玉之缘”。当前婚姻问事中世应六合，可作为双方契合、婚缘可成的候选证据；仍为候选参考，不覆盖核心吉凶。",
        effects=[
            {"type": "sign", "value": "marriage_shi_ying_he"},
            {"type": "score_delta", "value": 1},
        ],
    )


def _hun_ying_moving_or_empty(judgement: dict[str, Any]) -> dict[str, Any]:
    return _base_rule(
        judgement,
        rule_id="classic_huangjince_dynamic_hun_ying_moving_or_empty",
        priority=123,
        conditions={
            "op": "AND",
            "children": [
                _question_type("hun_male"),
                _line_exists("ying"),
                {
                    "op": "OR",
                    "children": [
                        {"fact_type": "line.is_moving", "subject": "ying", "relation": "is_true"},
                        {"fact_type": "line.is_empty", "subject": "ying", "relation": "is_true"},
                    ],
                },
            ],
        },
        ji_xiong="平",
        pattern="经典候选：婚姻应动应空不宜",
        explanation="《黄金策》云“欲求庚帖，岂宜应动应空？”当前婚姻问事中应爻发动或空亡，可作为对方一侧不稳、文书聘约不宜急定的候选证据；仍为候选参考，不覆盖核心吉凶。",
        effects=[
            {"type": "sign", "value": "marriage_ying_unstable"},
            {"type": "block", "value": "engagement_document_not_stable"},
        ],
    )


def _hun_shi_ying_both_empty(judgement: dict[str, Any]) -> dict[str, Any]:
    return _base_rule(
        judgement,
        rule_id="classic_huangjince_dynamic_hun_shi_ying_both_empty",
        priority=122,
        conditions={
            "op": "AND",
            "children": [
                _question_type("hun_male"),
                _line_exists("shi"),
                _line_exists("ying"),
                {"fact_type": "line.is_empty", "subject": "shi", "relation": "is_true"},
                {"fact_type": "line.is_empty", "subject": "ying", "relation": "is_true"},
            ],
        },
        ji_xiong="凶",
        pattern="经典候选：婚姻世应俱空",
        explanation="《黄金策》云“世应俱空，难遂百年之连理”。当前婚姻问事中世爻、应爻皆空，可作为双方根基皆虚、婚缘难落实的候选证据；仍为候选参考，不覆盖核心吉凶。",
        effects=[
            {"type": "sign", "value": "marriage_both_sides_empty"},
            {"type": "score_delta", "value": -1},
        ],
    )


def _bing_shi_ghost(judgement: dict[str, Any]) -> dict[str, Any]:
    return _base_rule(
        judgement,
        rule_id="classic_huangjince_dynamic_bing_shi_ghost",
        priority=117,
        conditions={
            "op": "AND",
            "children": [
                _question_type("bing"),
                _line_exists("shi"),
                _line_liu_qin("shi", "官鬼"),
            ],
        },
        ji_xiong="凶",
        pattern="经典候选：疾病世持鬼爻",
        explanation="《黄金策》云“世持鬼爻，病纵轻而难疗”。当前疾病问事中世爻六亲为官鬼，可作为病气临身、轻病亦缠绵难疗的候选证据；仍为候选参考，不覆盖疾病主判。",
        effects=[
            {"type": "sign", "value": "illness_shi_holds_ghost"},
            {"type": "score_delta", "value": -1},
        ],
    )


def _chuxing_shi_empty(judgement: dict[str, Any]) -> dict[str, Any]:
    return _base_rule(
        judgement,
        rule_id="classic_huangjince_dynamic_chuxing_shi_empty",
        priority=111,
        conditions={
            "op": "AND",
            "children": [
                _question_type("chuxing"),
                _line_exists("shi"),
                {"fact_type": "line.is_empty", "subject": "shi", "relation": "is_true"},
            ],
        },
        ji_xiong="吉",
        pattern="经典候选：出行世空利往",
        explanation="《黄金策》云“世若逢空，最利九流出往”。当前出行问事中世爻空亡，可作为自身离位、外出变动反而相宜的候选证据；仍为候选参考，不覆盖核心吉凶。",
        effects=[
            {"type": "sign", "value": "travel_shi_empty_favors_departure"},
            {"type": "score_delta", "value": 1},
        ],
    )


AUTO_COMPILE_TEMPLATES: dict[str, RuleBuilder] = {
    "classic_huangjince_90e429f17b7c": _primary_yong_moving_decline,
    "classic_huangjince_6b9330281536": _shi_ying_empty_he,
    "classic_huangjince_e5b514484df7": _chuxing_ying_ke_shi,
    "classic_huangjince_d3ba2859902b": _chuxing_ying_empty,
    "classic_huangjince_3e9aa6a9b461": _hun_shi_ying_relationships,
    "classic_huangjince_eefbc0805e37": _hun_shi_ying_he,
    "classic_huangjince_e17691681a8f": _hun_ying_moving_or_empty,
    "classic_huangjince_2caba4ce3669": _hun_shi_ying_both_empty,
    "classic_huangjince_a346e5ba72f2": _bing_shi_ghost,
    "classic_huangjince_fe880f90b7d4": _chuxing_shi_empty,
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--judgements", type=Path, default=DEFAULT_JUDGEMENTS_PATH)
    parser.add_argument("--candidate-rules", type=Path, default=DEFAULT_CANDIDATE_RULES_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_CANDIDATE_RULES_PATH)
    parser.add_argument("--dry-run", action="store_true", help="validate and print counts without writing output")
    args = parser.parse_args()

    judgements = load_jsonl(args.judgements)
    existing = load_jsonl(args.candidate_rules)
    generated = build_auto_compiled_rules(judgements)
    merged = merge_candidate_rules(existing, generated)

    if not args.dry_run:
        write_jsonl(merged, args.output)
    print(f"generated {len(generated)} conservative auto-compiled rules")
    print(f"merged candidate rules: {len(existing)} -> {len(merged)}")
    if args.dry_run:
        print("dry run: no files written")
    else:
        print(f"wrote candidate rules to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
