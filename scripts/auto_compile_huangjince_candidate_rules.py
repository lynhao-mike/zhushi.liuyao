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


def _bing_shi_fumu(judgement: dict[str, Any]) -> dict[str, Any]:
    """疾病章节：世持父母，药效不显之象。
    原文：世为敌者，父母加临，非比寻常之药饵。
    """
    return _base_rule(
        judgement,
        rule_id="classic_huangjince_dynamic_bing_shi_fumu",
        priority=49,
        conditions={
            "op": "AND",
            "children": [
                _question_type("bing"),
                _line_exists("shi"),
                _line_liu_qin("shi", "父母"),
            ],
        },
        ji_xiong="凶",
        pattern="经典候选：疾病世持父母爻",
        explanation="《黄金策》云：世为敌者，父母加临，非比寻常之药饵。疾病占中世爻为父母，药效不显，可作凶象候选证据。",
        effects=[
            {"type": "sign", "value": "bing_shi_fumu"},
            {"type": "score_delta", "value": -1},
        ],
    )


def _hun_shi_wang(judgement: dict[str, Any]) -> dict[str, Any]:
    """婚姻章节：世爻旺相，吉象。
    原文：旺相在生乡，定有利名之志。
    """
    return _base_rule(
        judgement,
        rule_id="classic_huangjince_dynamic_hun_shi_wang",
        priority=48,
        conditions={
            "op": "AND",
            "children": [
                _question_type("hun_male"),
                _line_exists("shi"),
                {
                    "op": "OR",
                    "children": [
                        {"fact_type": "line.wangshuai.overall", "subject": "shi", "relation": "eq", "value": "旺"},
                        {"fact_type": "line.wangshuai.overall", "subject": "shi", "relation": "eq", "value": "相"},
                    ],
                },
            ],
        },
        ji_xiong="吉",
        pattern="经典候选：婚姻世爻旺相",
        explanation="《黄金策》云：旺相在生乡，定有利名之志。婚姻占中世爻旺相，自身状态佳，可作吉象候选证据。",
        effects=[
            {"type": "sign", "value": "hun_shi_wang"},
            {"type": "score_delta", "value": 1},
        ],
    )


def _kaoshi_shi_empty(judgement: dict[str, Any]) -> dict[str, Any]:
    """考试章节：世爻空亡，考试不利。
    原文：世若无根，难期雁塔之题。
    """
    return _base_rule(
        judgement,
        rule_id="classic_huangjince_dynamic_kaoshi_shi_empty",
        priority=47,
        conditions={
            "op": "AND",
            "children": [
                _question_type("kaoshi"),
                _line_exists("shi"),
                {"fact_type": "line.is_empty", "subject": "shi", "relation": "is_true"},
            ],
        },
        ji_xiong="凶",
        pattern="经典候选：考试世爻空亡",
        explanation="《黄金策》云：世若无根，难期雁塔之题。考试占中世爻空亡，自身根基不实，可作凶象候选证据。",
        effects=[
            {"type": "sign", "value": "kaoshi_shi_empty"},
            {"type": "score_delta", "value": -1},
        ],
    )


def _chuxing_shi_ying_both_empty(judgement: dict[str, Any]) -> dict[str, Any]:
    """出行章节：世应皆空，出行不宜。
    原文：世应皆空，动则目前和好；旁爻少合，言其事后睽违。
    """
    return _base_rule(
        judgement,
        rule_id="classic_huangjince_dynamic_chuxing_shi_ying_both_empty",
        priority=46,
        conditions={
            "op": "AND",
            "children": [
                _question_type("chuxing"),
                _line_exists("shi"),
                _line_exists("ying"),
                {"fact_type": "line.is_empty", "subject": "shi", "relation": "is_true"},
                {"fact_type": "line.is_empty", "subject": "ying", "relation": "is_true"},
            ],
        },
        ji_xiong="凶",
        pattern="经典候选：出行世应皆空",
        explanation="《黄金策》云：世应皆空，动则目前和好；旁爻少合，言其事后睽违。出行占中世应双方皆空，内外条件均不具备，可作凶象候选证据。",
        effects=[
            {"type": "sign", "value": "chuxing_shi_ying_both_empty"},
            {"type": "score_delta", "value": -1},
        ],
    )




def _kaoshi_shi_wang(judgement: dict[str, Any]) -> dict[str, Any]:
    """考试章节：世爻旺相，吉象明显。
    原文：若在旺乡，则矜可矜而式可式。
    """
    return _base_rule(
        judgement,
        rule_id="classic_huangjince_dynamic_kaoshi_shi_wang",
        priority=55,
        conditions={
            "op": "AND",
            "children": [
                _question_type("kaoshi"),
                _line_exists("shi"),
                {
                    "op": "OR",
                    "children": [
                        {"fact_type": "line.wangshuai.overall", "subject": "shi", "relation": "eq", "value": "旺"},
                        {"fact_type": "line.wangshuai.overall", "subject": "shi", "relation": "eq", "value": "相"},
                    ],
                },
            ],
        },
        ji_xiong="吉",
        pattern="经典候选：考试世爻旺相",
        explanation="《黄金策》云：若在旺乡，则矜可矜而式可式。考试占中世爻居旺相之地，应试有利，可作吉象候选证据。",
        effects=[
            {"type": "sign", "value": "kaoshi_shi_wang"},
            {"type": "score_delta", "value": 1},
        ],
    )


def _cisong_shi_ying_sheng_he(judgement: dict[str, Any]) -> dict[str, Any]:
    """词讼章节：世应相生相合，和解有望。
    原文：相生相合，终成和好之情。
    """
    return _base_rule(
        judgement,
        rule_id="classic_huangjince_dynamic_cisong_shi_ying_sheng_he",
        priority=56,
        conditions={
            "op": "AND",
            "children": [
                _line_exists("shi"),
                _line_exists("ying"),
                {
                    "op": "OR",
                    "children": [
                        {"fact_type": "relationship.sheng", "subject": "shi", "object": "ying", "relation": "is_true"},
                        {"fact_type": "relationship.sheng", "subject": "ying", "object": "shi", "relation": "is_true"},
                        {"fact_type": "relationship.he", "subject": "shi", "object": "ying", "relation": "is_true"},
                    ],
                },
            ],
        },
        ji_xiong="吉",
        pattern="经典候选：世应相生相合",
        explanation="《黄金策》云：相生相合，终成和好之情。世应相生或相合，词讼和解可期，可作吉象候选证据。",
        effects=[
            {"type": "sign", "value": "cisong_shi_ying_sheng_he"},
            {"type": "score_delta", "value": 1},
        ],
    )


def _shiwu_chuxing_yong_sheng_shi(judgement: dict[str, Any]) -> dict[str, Any]:
    """失物/出行章节：用神生世，吉象。
    原文：人为利名忘却故乡生处，乐家无音信，全凭周易卦中推，要决归期但寻主象。
    """
    return _base_rule(
        judgement,
        rule_id="classic_huangjince_dynamic_shiwu_chuxing_yong_sheng_shi",
        priority=57,
        conditions={
            "op": "AND",
            "children": [
                {
                    "op": "OR",
                    "children": [
                        _question_type("shiwu"),
                        _question_type("chuxing"),
                    ],
                },
                _line_exists("primary_yong"),
                _line_exists("shi"),
                {"fact_type": "relationship.sheng", "subject": "primary_yong", "object": "shi", "relation": "is_true"},
            ],
        },
        ji_xiong="吉",
        pattern="经典候选：失物/出行用神生世",
        explanation="《黄金策》云：要决归期但寻主象。失物或出行占中用神生世，主象有利，失物可寻行人可归，可作吉象候选证据。",
        effects=[
            {"type": "sign", "value": "shiwu_chuxing_yong_sheng_shi"},
            {"type": "score_delta", "value": 1},
        ],
    )




def _bing_ghost_moving(judgement: dict[str, Any]) -> dict[str, Any]:
    """医药病不求医：鬼动卦中，眼下速难取效。
    原文：鬼动卦中，眼下速难取效；
    """
    return _base_rule(
        judgement,
        rule_id="classic_huangjince_dynamic_bing_ghost_moving",
        priority=58,
        conditions={
            "op": "AND",
            "children": [
                _question_type("bing"),
                _line_exists("shi"),
                {"fact_type": "line.is_moving", "subject": "shi", "relation": "is_true"},
                _line_liu_qin("shi", "官鬼"),
            ],
        },
        ji_xiong="凶",
        pattern="经典候选：疾病世爻鬼动",
        explanation="《黄金策》云：鬼动卦中，眼下速难取效。疾病占中世爻临官鬼发动，病势当前难速效，可作凶象候选证据。",
        effects=[
            {"type": "sign", "value": "bing_ghost_moving"},
            {"type": "score_delta", "value": -1},
        ],
    )


def _guan_ke_shi(judgement: dict[str, Any]) -> dict[str, Any]:
    """避乱：最怕官爻克世，则必难回避。
    原文：最怕官爻克世，则必难回避；
    """
    return _base_rule(
        judgement,
        rule_id="classic_huangjince_dynamic_guan_ke_shi",
        priority=59,
        conditions={
            "op": "AND",
            "children": [
                _line_exists("shi"),
                _line_liu_qin("shi", "官鬼"),
                {"fact_type": "relationship.ke", "subject": "shi", "object": "shi", "relation": "is_true"},
            ],
        },
        ji_xiong="凶",
        pattern="经典候选：官鬼克世",
        explanation="《黄金策》云：最怕官爻克世，则必难回避。官鬼爻克世爻，事势逼迫难以回避，可作凶象候选证据。",
        effects=[
            {"type": "sign", "value": "guan_ke_shi"},
            {"type": "score_delta", "value": -1},
        ],
    )


def _shi_empty(judgement: dict[str, Any]) -> dict[str, Any]:
    """身命：世居空位，终身作事无成。
    原文：世居空位，终身作事无成；
    """
    return _base_rule(
        judgement,
        rule_id="classic_huangjince_dynamic_shi_empty",
        priority=60,
        conditions={
            "op": "AND",
            "children": [
                _line_exists("shi"),
                {"fact_type": "line.is_empty", "subject": "shi", "relation": "is_true"},
            ],
        },
        ji_xiong="凶",
        pattern="经典候选：世爻空亡",
        explanation="《黄金策》云：世居空位，终身作事无成。世爻空亡，自身根基不实，可作凶象候选证据。",
        effects=[
            {"type": "sign", "value": "shi_empty"},
            {"type": "score_delta", "value": -1},
        ],
    )


def _cai_ghost_moving_sheng_shi(judgement: dict[str, Any]) -> dict[str, Any]:
    """求财：九流术士，偏宜鬼动生身。
    原文：九流术士，偏宜鬼动生身；
    """
    return _base_rule(
        judgement,
        rule_id="classic_huangjince_dynamic_cai_ghost_moving_sheng_shi",
        priority=61,
        conditions={
            "op": "AND",
            "children": [
                _question_type("cai"),
                _line_exists("shi"),
                {"fact_type": "line.is_moving", "subject": "shi", "relation": "is_true"},
                _line_liu_qin("shi", "官鬼"),
                {"fact_type": "relationship.sheng", "subject": "shi", "object": "shi", "relation": "is_true"},
            ],
        },
        ji_xiong="吉",
        pattern="经典候选：求财鬼动生身",
        explanation="《黄金策》云：九流术士，偏宜鬼动生身。求财占中鬼爻发动而生世爻，偏门得利，可作吉象候选证据。",
        effects=[
            {"type": "sign", "value": "cai_ghost_moving_sheng_shi"},
            {"type": "score_delta", "value": 1},
        ],
    )


def _shiwu_shi_wang(judgement: dict[str, Any]) -> dict[str, Any]:
    """失物：日旺月旺，纵未散而可寻。
    原文：自空化空，皆当置而勿问；日旺月旺，纵未散而可寻。
    """
    return _base_rule(
        judgement,
        rule_id="classic_huangjince_dynamic_shiwu_shi_wang",
        priority=62,
        conditions={
            "op": "AND",
            "children": [
                _question_type("shiwu"),
                _line_exists("shi"),
                {
                    "op": "OR",
                    "children": [
                        {"fact_type": "line.wangshuai.overall", "subject": "shi", "relation": "eq", "value": "旺"},
                        {"fact_type": "line.wangshuai.overall", "subject": "shi", "relation": "eq", "value": "相"},
                    ],
                },
            ],
        },
        ji_xiong="吉",
        pattern="经典候选：失物世爻旺相可寻",
        explanation="《黄金策》云：日旺月旺，纵未散而可寻。失物占中世爻旺相，失物纵未散亦可寻，可作吉象候选证据。",
        effects=[
            {"type": "sign", "value": "shiwu_shi_wang"},
            {"type": "score_delta", "value": 1},
        ],
    )


def _ying_ke_shi(judgement: dict[str, Any]) -> dict[str, Any]:
    """身命：世值凶而应克，愿听鸡鸣。
    原文：世值凶而应克，愿听鸡鸣；
    """
    return _base_rule(
        judgement,
        rule_id="classic_huangjince_dynamic_ying_ke_shi",
        priority=63,
        conditions={
            "op": "AND",
            "children": [
                _line_exists("shi"),
                _line_exists("ying"),
                {"fact_type": "relationship.ke", "subject": "ying", "object": "shi", "relation": "is_true"},
            ],
        },
        ji_xiong="凶",
        pattern="经典候选：应克世",
        explanation="《黄金策》云：世值凶而应克，愿听鸡鸣。应爻克世爻，外部因素压制自身，可作凶象候选证据。",
        effects=[
            {"type": "sign", "value": "ying_ke_shi"},
            {"type": "score_delta", "value": -1},
        ],
    )




def _fu_gui_ju_kong(judgement: dict[str, Any]) -> dict[str, Any]:
    """医药病不求医：福鬼俱空，当不治而自愈。
    原文：福鬼俱空，当不治而自愈；子官皆动，宜内补而外修。
    """
    return _base_rule(
        judgement,
        rule_id="classic_huangjince_dynamic_fu_gui_ju_kong",
        priority=64,
        conditions={
            "op": "AND",
            "children": [
                _question_type("bing"),
                {
                    "op": "OR",
                    "children": [
                        _line_liu_qin("shi", "子孙"),
                        _line_liu_qin("shi", "官鬼"),
                    ],
                },
                {"fact_type": "line.is_empty", "subject": "shi", "relation": "is_true"},
            ],
        },
        ji_xiong="吉",
        pattern="经典候选：医药福鬼俱空自愈",
        explanation="《黄金策》云：福鬼俱空，当不治而自愈。疾病占中福神子孙或官鬼空亡，病势自退，可作吉象候选证据。",
        effects=[
            {"type": "sign", "value": "fu_gui_ju_kong"},
            {"type": "score_delta", "value": 1},
        ],
    )


def _hun_cai_gui_kong(judgement: dict[str, Any]) -> dict[str, Any]:
    """婚姻：如逢财鬼空亡，乃婚姻之大忌。
    原文：如逢财鬼空亡，乃婚姻之大忌；苟遇阴阳得位，实天命之所关。
    """
    return _base_rule(
        judgement,
        rule_id="classic_huangjince_dynamic_hun_cai_gui_kong",
        priority=65,
        conditions={
            "op": "AND",
            "children": [
                _question_type("hun_male"),
                {
                    "op": "OR",
                    "children": [
                        _line_liu_qin("shi", "妻财"),
                        _line_liu_qin("shi", "官鬼"),
                    ],
                },
                {"fact_type": "line.is_empty", "subject": "shi", "relation": "is_true"},
            ],
        },
        ji_xiong="凶",
        pattern="经典候选：婚姻财鬼空亡大忌",
        explanation="《黄金策》云：如逢财鬼空亡，乃婚姻之大忌。婚姻占中财爻或官鬼空亡，大忌之象，可作凶象候选证据。",
        effects=[
            {"type": "sign", "value": "hun_cai_gui_kong"},
            {"type": "score_delta", "value": -1},
        ],
    )


def _cai_hua_zi_sun(judgement: dict[str, Any]) -> dict[str, Any]:
    """产育：财化子孙，分娩即当勿药喜。
    原文：胎临官鬼，怀胎便有采薪忧；财化子孙，分娩即当勿药喜。
    """
    return _base_rule(
        judgement,
        rule_id="classic_huangjince_dynamic_cai_hua_zi_sun",
        priority=66,
        conditions={
            "op": "AND",
            "children": [
                _line_liu_qin("shi", "妻财"),
                {"fact_type": "line.is_moving", "subject": "shi", "relation": "is_true"},
                {"fact_type": "line.bian.liu_qin", "subject": "shi", "relation": "eq", "value": "子孙"},
            ],
        },
        ji_xiong="吉",
        pattern="经典候选：产育财化子孙勿药喜",
        explanation="《黄金策》云：财化子孙，分娩即当勿药喜。财爻动化子孙，分娩吉兆，可作吉象候选证据。",
        effects=[
            {"type": "sign", "value": "cai_hua_zi_sun"},
            {"type": "score_delta", "value": 1},
        ],
    )


def _cai_fu_chi_shi(judgement: dict[str, Any]) -> dict[str, Any]:
    """求财：六畜血财,尤喜福兴持世。
    原文：六畜血财,尤喜福兴持世。
    """
    return _base_rule(
        judgement,
        rule_id="classic_huangjince_dynamic_cai_fu_chi_shi",
        priority=67,
        conditions={
            "op": "AND",
            "children": [
                _question_type("cai"),
                _line_exists("shi"),
                _line_liu_qin("shi", "子孙"),
            ],
        },
        ji_xiong="吉",
        pattern="经典候选：求财福神持世",
        explanation="《黄金策》云：六畜血财,尤喜福兴持世。求财占中子孙爻持世，福神临身得利，可作吉象候选证据。",
        effects=[
            {"type": "sign", "value": "cai_fu_chi_shi"},
            {"type": "score_delta", "value": 1},
        ],
    )


def _fu_hua_ji_yao(judgement: dict[str, Any]) -> dict[str, Any]:
    """医药：福化忌爻，误服杀身之恶剂。
    原文：福化忌爻，误服杀身之恶剂；
    """
    return _base_rule(
        judgement,
        rule_id="classic_huangjince_dynamic_fu_hua_ji_yao",
        priority=68,
        conditions={
            "op": "AND",
            "children": [
                _question_type("bing"),
                _line_liu_qin("shi", "子孙"),
                {"fact_type": "line.is_moving", "subject": "shi", "relation": "is_true"},
                {
                    "op": "OR",
                    "children": [
                        {"fact_type": "line.bian.liu_qin", "subject": "shi", "relation": "eq", "value": "官鬼"},
                        {"fact_type": "line.bian.liu_qin", "subject": "shi", "relation": "eq", "value": "兄弟"},
                    ],
                },
            ],
        },
        ji_xiong="凶",
        pattern="经典候选：医药福化忌爻误服",
        explanation="《黄金策》云：福化忌爻，误服杀身之恶剂。疾病占中子孙爻动化官鬼或兄弟，用药有误之兆，可作凶象候选证据。",
        effects=[
            {"type": "sign", "value": "fu_hua_ji_yao"},
            {"type": "score_delta", "value": -1},
        ],
    )


def _hun_shi_ying_hua_kong(judgement: dict[str, Any]) -> dict[str, Any]:
    """婚姻：世应化空，始成而终悔。
    原文：世应化空，始成而终悔。
    """
    return _base_rule(
        judgement,
        rule_id="classic_huangjince_dynamic_hun_shi_ying_hua_kong",
        priority=69,
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
        pattern="经典候选：婚姻世应化空始成终悔",
        explanation="《黄金策》云：世应化空，始成而终悔。婚姻占中世应皆空，先成后悔之兆，可作凶象候选证据。",
        effects=[
            {"type": "sign", "value": "hun_shi_ying_hua_kong"},
            {"type": "score_delta", "value": -1},
        ],
    )




def _dong_bian_jiao_zheng(judgement: dict[str, Any]) -> dict[str, Any]:
    """总断千金赋: 动为始变为终最怕交争 -> 凶"""
    return _base_rule(
        judgement,
        rule_id="classic_huangjince_dynamic_dong_bian_jiao_zheng",
        priority=70,
        conditions={
            "op": "AND",
            "children": [
                _line_exists("shi"),
                {"fact_type": "line.is_moving", "subject": "shi", "relation": "is_true"},
                {"fact_type": "line.bian.liu_qin", "subject": "shi", "relation": "in", "value": ["官鬼", "兄弟"]},
            ],
        },
        ji_xiong="凶",
        pattern="经典候选: 动变交争世爻化忌",
        explanation="《黄金策》云: 动为始,变为终,最怕交争。世爻动而化忌神(官鬼/兄弟),可作凶象候选证据。",
        effects=[{"type": "sign", "value": "dong_bian_jiao_zheng"}, {"type": "score_delta", "value": -1}],
    )


def _zi_kong_hua_kong(judgement: dict[str, Any]) -> dict[str, Any]:
    """总断千金赋: 自空化空必成凶咎 -> 凶"""
    return _base_rule(
        judgement,
        rule_id="classic_huangjince_dynamic_zi_kong_hua_kong",
        priority=71,
        conditions={
            "op": "AND",
            "children": [
                _line_exists("shi"),
                {"fact_type": "line.is_empty", "subject": "shi", "relation": "is_true"},
                {"fact_type": "line.is_moving", "subject": "shi", "relation": "is_true"},
            ],
        },
        ji_xiong="凶",
        pattern="经典候选: 自空化空必成凶咎",
        explanation="《黄金策》云: 自空化空,必成凶咎。世爻自身空亡又发动,事主落空更兼变动,可作凶象候选证据。",
        effects=[{"type": "sign", "value": "zi_kong_hua_kong"}, {"type": "score_delta", "value": -1}],
    )


def _he_zhu_chong_po(judgement: dict[str, Any]) -> dict[str, Any]:
    """总断千金赋: 如逢合住须冲破以成功 -> 中性"""
    return _base_rule(
        judgement,
        rule_id="classic_huangjince_dynamic_he_zhu_chong_po",
        priority=72,
        conditions={
            "op": "AND",
            "children": [
                _line_exists("shi"),
                _line_exists("ying"),
                {"fact_type": "relationship.he", "subject": "shi", "object": "ying", "relation": "is_true"},
            ],
        },
        ji_xiong="平",
        pattern="经典候选: 合住须冲破",
        explanation="《黄金策》云: 如逢合住,须冲破以成功。世应合住事情纠缠,须外力冲破方能成事,可作平象候选证据。",
        effects=[{"type": "sign", "value": "he_zhu_chong_po"}, {"type": "score_delta", "value": 0}],
    )


def _xiu_qiu_sheng_wang(judgement: dict[str, Any]) -> dict[str, Any]:
    """总断千金赋: 若遇休囚必生旺而成事 -> 吉"""
    return _base_rule(
        judgement,
        rule_id="classic_huangjince_dynamic_xiu_qiu_sheng_wang",
        priority=73,
        conditions={
            "op": "AND",
            "children": [
                _line_exists("shi"),
                {"fact_type": "line.wangshuai.overall", "subject": "shi", "relation": "eq", "value": "休"},
                {"fact_type": "relationship.sheng", "subject": "shi", "object": "shi", "relation": "is_true"},
            ],
        },
        ji_xiong="吉",
        pattern="经典候选: 休囚得生旺而成事",
        explanation="《黄金策》云: 若遇休囚,必生旺而成事。世爻休囚而得生助,则事终可成,可作吉象候选证据。",
        effects=[{"type": "sign", "value": "xiu_qiu_sheng_wang"}, {"type": "score_delta", "value": 1}],
    )


def _hun_liu_he(judgement: dict[str, Any]) -> dict[str, Any]:
    """婚姻: 六合则易而且吉 -> 吉"""
    return _base_rule(
        judgement,
        rule_id="classic_huangjince_dynamic_hun_liu_he",
        priority=74,
        conditions={
            "op": "AND",
            "children": [
                _question_type("hun_male"),
                _line_exists("shi"),
                _line_exists("ying"),
                {"fact_type": "relationship.he", "subject": "shi", "object": "ying", "relation": "is_true"},
            ],
        },
        ji_xiong="吉",
        pattern="经典候选: 婚姻六合则易且吉",
        explanation="《黄金策》云: 六合则易而且吉。婚姻占世应六合,双方和合易成,可作吉象候选证据。",
        effects=[{"type": "sign", "value": "hun_liu_he"}, {"type": "score_delta", "value": 1}],
    )


def _hun_liu_chong(judgement: dict[str, Any]) -> dict[str, Any]:
    """婚姻: 六冲则难而又凶 -> 凶"""
    return _base_rule(
        judgement,
        rule_id="classic_huangjince_dynamic_hun_liu_chong",
        priority=75,
        conditions={
            "op": "AND",
            "children": [
                _question_type("hun_male"),
                _line_exists("shi"),
                _line_exists("ying"),
                {"fact_type": "relationship.chong", "subject": "shi", "object": "ying", "relation": "is_true"},
            ],
        },
        ji_xiong="凶",
        pattern="经典候选: 婚姻六冲难而且凶",
        explanation="《黄金策》云: 六冲则难而又凶。婚姻占世应相冲,双方冲突难成,可作凶象候选证据。",
        effects=[{"type": "sign", "value": "hun_liu_chong"}, {"type": "score_delta", "value": -1}],
    )


def _hun_ri_he_bi_he(judgement: dict[str, Any]) -> dict[str, Any]:
    """婚姻: 如日合而世应比和因人成事 -> 吉"""
    return _base_rule(
        judgement,
        rule_id="classic_huangjince_dynamic_hun_ri_he_bi_he",
        priority=76,
        conditions={
            "op": "AND",
            "children": [
                _question_type("hun_male"),
                _line_exists("shi"),
                _line_exists("ying"),
                {"fact_type": "relationship.he", "subject": "shi", "object": "ying", "relation": "is_true"},
            ],
        },
        ji_xiong="吉",
        pattern="经典候选: 婚姻日合世应比和",
        explanation="《黄金策》云: 如日合而世应比和,因人成事。婚姻占世应相合或比和,可借外力成事,可作吉象候选证据。",
        effects=[{"type": "sign", "value": "hun_ri_he_bi_he"}, {"type": "score_delta", "value": 1}],
    )


def _cisong_shi_wang_ying_shuai(judgement: dict[str, Any]) -> dict[str, Any]:
    """词讼: 应乃对头要见休囚死绝;世为原告宜临帝旺长生 -> 吉(世旺应衰)"""
    return _base_rule(
        judgement,
        rule_id="classic_huangjince_dynamic_cisong_shi_wang_ying_shuai",
        priority=77,
        conditions={
            "op": "AND",
            "children": [
                _line_exists("shi"),
                _line_exists("ying"),
                {
                    "op": "OR",
                    "children": [
                        {"fact_type": "line.wangshuai.overall", "subject": "shi", "relation": "in", "value": ["旺", "相"]},
                    ],
                },
                {
                    "op": "OR",
                    "children": [
                        {"fact_type": "line.wangshuai.overall", "subject": "ying", "relation": "in", "value": ["衰", "休", "囚"]},
                    ],
                },
            ],
        },
        ji_xiong="吉",
        pattern="经典候选: 词讼世旺应衰",
        explanation="《黄金策》云: 应乃对头,要见休囚死绝;世为原告,宜临帝旺长生。词讼占中世旺应衰,原告势强,可作吉象候选证据。",
        effects=[{"type": "sign", "value": "cisong_shi_wang_ying_shuai"}, {"type": "score_delta", "value": 1}],
    )




def _liu_xu_shi_wang_cai_xing(judgement: dict[str, Any]) -> dict[str, Any]:
    """六畜: 或赌或斗皆宜世旺财兴 -> 吉"""
    return _base_rule(
        judgement,
        rule_id="classic_huangjince_dynamic_liu_xu_shi_wang_cai_xing",
        priority=78,
        conditions={
            "op": "AND",
            "children": [
                _line_exists("shi"),
                {
                    "op": "OR",
                    "children": [
                        {"fact_type": "line.wangshuai.overall", "subject": "shi", "relation": "eq", "value": "旺"},
                        {"fact_type": "line.wangshuai.overall", "subject": "shi", "relation": "eq", "value": "相"},
                    ],
                },
            ],
        },
        ji_xiong="吉",
        pattern="经典候选: 六畜世旺财兴",
        explanation="《黄金策》云: 或赌或斗,皆宜世旺财兴。世爻旺相,博弈竞争易胜,可作吉象候选证据。",
        effects=[{"type": "sign", "value": "liu_xu_shi_wang_cai_xing"}, {"type": "score_delta", "value": 1}],
    )


def _cai_dong_xiu_wang_xuan(judgement: dict[str, Any]) -> dict[str, Any]:
    """求名: 财若交重休望青钱中选 -> 凶"""
    return _base_rule(
        judgement,
        rule_id="classic_huangjince_dynamic_cai_dong_xiu_wang_xuan",
        priority=79,
        conditions={
            "op": "AND",
            "children": [
                {"fact_type": "question.type", "relation": "eq", "value": "kaoshi"},
                _line_exists("shi"),
                _line_liu_qin("shi", "妻财"),
                {"fact_type": "line.is_moving", "subject": "shi", "relation": "is_true"},
            ],
        },
        ji_xiong="凶",
        pattern="经典候选: 考试财动休望中选",
        explanation="《黄金策》云: 财若交重,休望青钱中选。考试占财爻发动,不利功名,可作凶象候选证据。",
        effects=[{"type": "sign", "value": "cai_dong_xiu_wang_xuan"}, {"type": "score_delta", "value": -1}],
    )


def _cai_zuo_xiu_xiu_hua_di(judgement: dict[str, Any]) -> dict[str, Any]:
    """求馆: 财作束修不宜化弟 -> 吉"""
    return _base_rule(
        judgement,
        rule_id="classic_huangjince_dynamic_cai_zuo_xiu_xiu_hua_di",
        priority=80,
        conditions={
            "op": "AND",
            "children": [
                _line_exists("shi"),
                _line_liu_qin("shi", "妻财"),
                {"fact_type": "line.bian.liu_qin", "subject": "shi", "relation": "eq", "value": "兄弟"},
            ],
        },
        ji_xiong="凶",
        pattern="经典候选: 束修财化兄弟不利",
        explanation="《黄金策》云: 财作束修,不宜化弟。财爻化兄弟,束修受损,可作凶象候选证据。",
        effects=[{"type": "sign", "value": "cai_zuo_xiu_xiu_hua_di"}, {"type": "score_delta", "value": -1}],
    )


def _chuxing_jian_ju_kong(judgement: dict[str, Any]) -> dict[str, Any]:
    """出行: 两间齐空独行则吉 -> 吉"""
    return _base_rule(
        judgement,
        rule_id="classic_huangjince_dynamic_chuxing_jian_ju_kong",
        priority=81,
        conditions={
            "op": "AND",
            "children": [
                {"fact_type": "question.type", "relation": "eq", "value": "chuxing"},
                _line_exists("shi"),
                {"fact_type": "line.is_empty", "subject": "shi", "relation": "is_true"},
            ],
        },
        ji_xiong="吉",
        pattern="经典候选: 出行间爻皆空独行吉",
        explanation="《黄金策》云: 两间齐空,独行则吉。出行占间爻空亡,独行无碍,可作吉象候选证据。",
        effects=[{"type": "sign", "value": "chuxing_jian_ju_kong"}, {"type": "score_delta", "value": 1}],
    )


def _yong_wang_er_fei(judgement: dict[str, Any]) -> dict[str, Any]:
    """身命: 用旺儿肥终易养主衰儿弱必难为 -> 吉(用旺)"""
    return _base_rule(
        judgement,
        rule_id="classic_huangjince_dynamic_yong_wang_er_fei",
        priority=82,
        conditions={
            "op": "AND",
            "children": [
                _line_exists("primary_yong"),
                {
                    "op": "OR",
                    "children": [
                        {"fact_type": "line.wangshuai.overall", "subject": "primary_yong", "relation": "eq", "value": "旺"},
                        {"fact_type": "line.wangshuai.overall", "subject": "primary_yong", "relation": "eq", "value": "相"},
                    ],
                },
            ],
        },
        ji_xiong="吉",
        pattern="经典候选: 用旺儿肥终易养",
        explanation="《黄金策》云: 用旺儿肥终易养。用神旺相,所问之事根基扎实,可作吉象候选证据。",
        effects=[{"type": "sign", "value": "yong_wang_er_fei"}, {"type": "score_delta", "value": 1}],
    )


def _chuxing_yong_shang_ru_mu(judgement: dict[str, Any]) -> dict[str, Any]:
    """行人: 远行最怕用爻伤尤嫌入墓 -> 凶"""
    return _base_rule(
        judgement,
        rule_id="classic_huangjince_dynamic_chuxing_yong_shang_ru_mu",
        priority=83,
        conditions={
            "op": "AND",
            "children": [
                _line_exists("primary_yong"),
                {
                    "op": "OR",
                    "children": [
                        {"fact_type": "line.wangshuai.overall", "subject": "primary_yong", "relation": "eq", "value": "衰"},
                        {"fact_type": "line.wangshuai.overall", "subject": "primary_yong", "relation": "eq", "value": "休"},
                        {"fact_type": "line.wangshuai.overall", "subject": "primary_yong", "relation": "eq", "value": "囚"},
                        {"fact_type": "line.wangshuai.overall", "subject": "primary_yong", "relation": "eq", "value": "死"},
                    ],
                },
            ],
        },
        ji_xiong="凶",
        pattern="经典候选: 远行用爻伤及入墓",
        explanation="《黄金策》云: 远行最怕用爻伤,尤嫌入墓。用神休囚死绝,出行不利,可作凶象候选证据。",
        effects=[{"type": "sign", "value": "chuxing_yong_shang_ru_mu"}, {"type": "score_delta", "value": -1}],
    )


def _sui_jun_yi_jing(judgement: dict[str, Any]) -> dict[str, Any]:
    """总断千金赋: 最恶者岁君宜静而不宜动 -> 凶(动)"""
    return _base_rule(
        judgement,
        rule_id="classic_huangjince_dynamic_sui_jun_yi_jing",
        priority=84,
        conditions={
            "op": "AND",
            "children": [
                _line_exists("shi"),
                {"fact_type": "line.is_moving", "subject": "shi", "relation": "is_true"},
            ],
        },
        ji_xiong="凶",
        pattern="经典候选: 岁君宜静不宜动",
        explanation="《黄金策》云: 最恶者岁君,宜静而不宜动。世爻发动,宜静反动,可作凶象候选证据。",
        effects=[{"type": "sign", "value": "sui_jun_yi_jing"}, {"type": "score_delta", "value": -1}],
    )


def _jue_feng_sheng(judgement: dict[str, Any]) -> dict[str, Any]:
    """总断千金赋: 绝逢生而事成 -> 吉"""
    return _base_rule(
        judgement,
        rule_id="classic_huangjince_dynamic_jue_feng_sheng",
        priority=85,
        conditions={
            "op": "AND",
            "children": [
                _line_exists("shi"),
                {"fact_type": "line.wangshuai.overall", "subject": "shi", "relation": "eq", "value": "衰"},
                {"fact_type": "relationship.sheng", "subject": "shi", "object": "shi", "relation": "is_true"},
            ],
        },
        ji_xiong="吉",
        pattern="经典候选: 绝处逢生事成",
        explanation="《黄金策》云: 绝逢生而事成。世爻衰绝而得生助,绝处逢生,可作吉象候选证据。",
        effects=[{"type": "sign", "value": "jue_feng_sheng"}, {"type": "score_delta", "value": 1}],
    )


def _qiuguan_cai_dong(judgement: dict[str, Any]) -> dict[str, Any]:
    """求馆: 动象临财,难称意 -> 凶"""
    return _base_rule(
        judgement,
        rule_id="classic_huangjince_dynamic_qiuguan_cai_dong",
        priority=86,
        conditions={
            "op": "AND",
            "children": [
                _question_type("kaoshi"),
                _line_exists("shi"),
                {"fact_type": "line.is_moving", "subject": "shi", "relation": "is_true"},
                _line_liu_qin("shi", "妻财"),
            ],
        },
        ji_xiong="凶",
        pattern="经典候选: 求馆动象临财",
        explanation="《黄金策》云: 动象临财,难称意。求馆占中世爻发动且临妻财,财动妨馆事难成,可作凶象候选证据。",
        effects=[{"type": "sign", "value": "qiuguan_cai_dong"}, {"type": "score_delta", "value": -1}],
    )


def _tianshi_ying_empty(judgement: dict[str, Any]) -> dict[str, Any]:
    """天时: 应乃太虚,逢空而雨晴难拟 -> 凶"""
    return _base_rule(
        judgement,
        rule_id="classic_huangjince_dynamic_tianshi_ying_empty",
        priority=87,
        conditions={
            "op": "AND",
            "children": [
                _line_exists("ying"),
                {"fact_type": "line.is_empty", "subject": "ying", "relation": "is_true"},
            ],
        },
        ji_xiong="凶",
        pattern="经典候选: 天时应空难定",
        explanation="《黄金策》云: 应乃太虚,逢空而雨晴难拟。天时占中应爻空亡,气象无定晴雨难测,可作凶象候选证据。",
        effects=[{"type": "sign", "value": "tianshi_ying_empty"}, {"type": "score_delta", "value": -1}],
    )


def _cai_lai_jiu_wo(judgement: dict[str, Any]) -> dict[str, Any]:
    """求财: 财来就我,终须易 -> 吉"""
    return _base_rule(
        judgement,
        rule_id="classic_huangjince_dynamic_cai_lai_jiu_wo",
        priority=88,
        conditions={
            "op": "AND",
            "children": [
                _question_type("cai"),
                _line_exists("shi"),
                _line_liu_qin("shi", "妻财"),
            ],
        },
        ji_xiong="吉",
        pattern="经典候选: 求财财来就我",
        explanation="《黄金策》云: 财来就我,终须易。求财占中世爻临妻财,财来寻我而非我去寻财,求财易得,可作吉象候选证据。",
        effects=[{"type": "sign", "value": "cai_lai_jiu_wo"}, {"type": "score_delta", "value": 1}],
    )


def _xingren_feng_chong(judgement: dict[str, Any]) -> dict[str, Any]:
    """行人: 近出何妨主象伏,偏利逢冲 -> 吉"""
    return _base_rule(
        judgement,
        rule_id="classic_huangjince_dynamic_xingren_feng_chong",
        priority=89,
        conditions={
            "op": "AND",
            "children": [
                _question_type("chuxing"),
                _line_exists("primary_yong"),
                _line_exists("shi"),
                {"fact_type": "relationship.chong", "subject": "primary_yong", "object": "shi", "relation": "is_true"},
            ],
        },
        ji_xiong="吉",
        pattern="经典候选: 行人主象逢冲",
        explanation="《黄金策》云: 近出何妨主象伏,偏利逢冲。行人占中用神与世爻相冲,冲则动行人可归,可作吉象候选证据。",
        effects=[{"type": "sign", "value": "xingren_feng_chong"}, {"type": "score_delta", "value": 1}],
    )


def _fumu_chi_shi(judgement: dict[str, Any]) -> dict[str, Any]:
    """通用: 父母持世,心劳而蚕必难为 -> 凶"""
    return _base_rule(
        judgement,
        rule_id="classic_huangjince_dynamic_fumu_chi_shi",
        priority=90,
        conditions={
            "op": "AND",
            "children": [
                _line_exists("shi"),
                _line_liu_qin("shi", "父母"),
            ],
        },
        ji_xiong="凶",
        pattern="经典候选: 父母持世辛劳",
        explanation="《黄金策》云: 父母持世,心劳而蚕必难为。父母持世主辛劳费心,所求之事多波折劳苦,可作凶象候选证据。",
        effects=[{"type": "sign", "value": "fumu_chi_shi"}, {"type": "score_delta", "value": -1}],
    )


def _cai_kong_shi(judgement: dict[str, Any]) -> dict[str, Any]:
    """通用: 财若空亡,虽利暂时无远力 -> 凶"""
    return _base_rule(
        judgement,
        rule_id="classic_huangjince_dynamic_cai_kong_shi",
        priority=91,
        conditions={
            "op": "AND",
            "children": [
                _line_exists("shi"),
                _line_liu_qin("shi", "妻财"),
                {"fact_type": "line.is_empty", "subject": "shi", "relation": "is_true"},
            ],
        },
        ji_xiong="凶",
        pattern="经典候选: 财爻空亡利暂",
        explanation="《黄金策》云: 财若空亡,虽利暂时无远力。世爻临妻财而空亡,虽有短期小利却无长远之力,可作凶象候选证据。",
        effects=[{"type": "sign", "value": "cai_kong_shi"}, {"type": "score_delta", "value": -1}],
    )


def _hun_gui_ke_fei_yao(judgement: dict[str, Any]) -> dict[str, Any]:
    """婚姻: 鬼克飞爻,难嫁 -> 凶"""
    return _base_rule(
        judgement,
        rule_id="classic_huangjince_dynamic_hun_gui_ke_fei_yao",
        priority=87,
        conditions={
            "op": "AND",
            "children": [
                _question_type("hun_male"),
                _line_exists("cai"),
                _line_exists("gui"),
                _relationship("ke", "gui", "cai"),
            ],
        },
        ji_xiong="凶",
        pattern="经典候选: 婚姻鬼克飞爻",
        explanation="《黄金策》云: 鬼克飞爻,果信绿窗之难嫁。婚占中官鬼克制财爻,女方处境艰难婚事难成,可作凶象候选证据。",
        effects=[{"type": "sign", "value": "hun_gui_ke_fei_yao"}, {"type": "score_delta", "value": -1}],
    )


def _cisong_fu_dong_guan_hua_fu(judgement: dict[str, Any]) -> dict[str, Any]:
    """词讼: 父动官化福,事将成 -> 吉"""
    return _base_rule(
        judgement,
        rule_id="classic_huangjince_dynamic_cisong_fu_dong_guan_hua_fu",
        priority=88,
        conditions={
            "op": "AND",
            "children": [
                _line_exists("fumu"),
                {"fact_type": "line.is_moving", "subject": "fumu", "relation": "is_true"},
                _line_exists("gui"),
                {"fact_type": "line.is_moving", "subject": "gui", "relation": "is_true"},
                {"fact_type": "line.bian.liu_qin", "subject": "gui", "relation": "eq", "value": "子孙"},
            ],
        },
        ji_xiong="吉",
        pattern="经典候选: 词讼父动官化福",
        explanation="《黄金策》云: 父动而官化福爻,事将成而偶逢兜劝。词讼占中父母发动且官鬼化子孙,状纸已成而有调解之机,可作吉象候选证据。",
        effects=[{"type": "sign", "value": "cisong_fu_dong_guan_hua_fu"}, {"type": "score_delta", "value": 1}],
    )


def _cai_ju_he_fu_shen(judgement: dict[str, Any]) -> dict[str, Any]:
    """求财: 财局合福神,万倍利源 -> 吉"""
    return _base_rule(
        judgement,
        rule_id="classic_huangjince_dynamic_cai_ju_he_fu_shen",
        priority=89,
        conditions={
            "op": "AND",
            "children": [
                _question_type("cai"),
                _line_exists("cai"),
                _line_exists("zi"),
                _relationship("he", "cai", "zi"),
            ],
        },
        ji_xiong="吉",
        pattern="经典候选: 求财财局合福神",
        explanation="《黄金策》云: 财局合福神,万倍利源可取。求财占中财爻与子孙六合,财源广进福神护持,可作吉象候选证据。",
        effects=[{"type": "sign", "value": "cai_ju_he_fu_shen"}, {"type": "score_delta", "value": 1}],
    )


def _cai_xiong_lian_gui_ke(judgement: dict[str, Any]) -> dict[str, Any]:
    """求财: 兄连鬼克,口舌难逃 -> 凶"""
    return _base_rule(
        judgement,
        rule_id="classic_huangjince_dynamic_cai_xiong_lian_gui_ke",
        priority=90,
        conditions={
            "op": "AND",
            "children": [
                _question_type("cai"),
                _line_exists("xiong"),
                _line_exists("gui"),
                _line_exists("shi"),
                _relationship("ke", "gui", "shi"),
            ],
        },
        ji_xiong="凶",
        pattern="经典候选: 求财兄连鬼克",
        explanation="《黄金策》云: 兄连鬼克,纷纷口舌难逃。求财占中兄弟官鬼同现且鬼克世,破财口舌并至,可作凶象候选证据。",
        effects=[{"type": "sign", "value": "cai_xiong_lian_gui_ke"}, {"type": "score_delta", "value": -1}],
    )


def _cai_dong_shen_xing(judgement: dict[str, Any]) -> dict[str, Any]:
    """求财: 财动身兴,脱货宜 -> 吉"""
    return _base_rule(
        judgement,
        rule_id="classic_huangjince_dynamic_cai_dong_shen_xing",
        priority=91,
        conditions={
            "op": "AND",
            "children": [
                _question_type("cai"),
                _line_exists("cai"),
                {"fact_type": "line.is_moving", "subject": "cai", "relation": "is_true"},
                _line_exists("shi"),
                {"fact_type": "line.wangshuai.overall", "subject": "shi", "relation": "in", "value": ["旺", "相"]},
            ],
        },
        ji_xiong="吉",
        pattern="经典候选: 求财财动身兴",
        explanation="《黄金策》云: 脱货者,宜财动而身兴。求财占中财爻发动且世爻旺相,货物流通生意兴隆,可作吉象候选证据。",
        effects=[{"type": "sign", "value": "cai_dong_shen_xing"}, {"type": "score_delta", "value": 1}],
    )


def _qiushi_jing_he_fu_yao(judgement: dict[str, Any]) -> dict[str, Any]:
    """求师: 静合福爻,善诱 -> 吉"""
    return _base_rule(
        judgement,
        rule_id="classic_huangjince_dynamic_qiushi_jing_he_fu_yao",
        priority=92,
        conditions={
            "op": "AND",
            "children": [
                _question_type("kaoshi"),
                _line_exists("fumu"),
                {"fact_type": "line.is_moving", "subject": "fumu", "relation": "is_true", "inverted": True},
                _line_exists("zi"),
                _relationship("he", "fumu", "zi"),
            ],
        },
        ji_xiong="吉",
        pattern="经典候选: 求师静合福爻",
        explanation="《黄金策》云: 静合福爻,喜遇循循之善诱。求师占中父母静爻六合子孙,师长温和善于教导,可作吉象候选证据。",
        effects=[{"type": "sign", "value": "qiushi_jing_he_fu_yao"}, {"type": "score_delta", "value": 1}],
    )


def _hun_yong_sheng_he_shi(judgement: dict[str, Any]) -> dict[str, Any]:
    """婚姻: 用爻生合世爻,必得其力 -> 吉"""
    return _base_rule(
        judgement,
        rule_id="classic_huangjince_dynamic_hun_yong_sheng_he_shi",
        priority=93,
        conditions={
            "op": "AND",
            "children": [
                _question_type("hun_male"),
                _line_exists("primary_yong"),
                _line_exists("shi"),
                {
                    "op": "OR",
                    "children": [
                        _relationship("sheng", "primary_yong", "shi"),
                        _relationship("he", "primary_yong", "shi"),
                    ],
                },
            ],
        },
        ji_xiong="吉",
        pattern="经典候选: 婚姻用神生合世爻",
        explanation="《黄金策》云: 用爻生合世爻,必得其力。婚姻占中主用神生世或合世,对方/事体能助益自身,可作吉象候选证据。未编译克冲身象一侧,避免混合分句扩大判断。",
        effects=[{"type": "sign", "value": "hun_yong_sheng_he_shi"}, {"type": "score_delta", "value": 1}],
    )


def _liuxu_cai_kong_fu_dong(judgement: dict[str, Any]) -> dict[str, Any]:
    """六畜: 财空福动,纵迟钝而可观 -> 吉"""
    return _base_rule(
        judgement,
        rule_id="classic_huangjince_dynamic_liuxu_cai_kong_fu_dong",
        priority=94,
        conditions={
            "op": "AND",
            "children": [
                _line_exists("cai"),
                {"fact_type": "line.is_empty", "subject": "cai", "relation": "is_true"},
                _line_exists("zi"),
                {"fact_type": "line.is_moving", "subject": "zi", "relation": "is_true"},
            ],
        },
        ji_xiong="吉",
        pattern="经典候选: 六畜财空福动",
        explanation="《黄金策》云: 财空福动,纵迟钝而可观。六畜占中财爻空亡而福德子孙发动,虽起势迟缓仍有可观之象,可作吉象候选证据。",
        effects=[{"type": "sign", "value": "liuxu_cai_kong_fu_dong"}, {"type": "score_delta", "value": 1}],
    )


def _shiwu_cai_dong_bu_yi(judgement: dict[str, Any]) -> dict[str, Any]:
    """失物: 失舟车衣服,不宜妻位交重 -> 凶"""
    return _base_rule(
        judgement,
        rule_id="classic_huangjince_dynamic_shiwu_cai_dong_bu_yi",
        priority=95,
        conditions={
            "op": "AND",
            "children": [
                _question_type("shiwu"),
                _line_exists("cai"),
                {"fact_type": "line.is_moving", "subject": "cai", "relation": "is_true"},
            ],
        },
        ji_xiong="凶",
        pattern="经典候选: 失物财爻发动不宜",
        explanation="《黄金策》云: 倘失舟车衣服,不宜妻位交重。失物占中财爻发动,物象不安、转移难寻,可作凶象候选证据。仅编译舟车衣服失物分句,不扩展至亡走兽飞禽。",
        effects=[{"type": "sign", "value": "shiwu_cai_dong_bu_yi"}, {"type": "score_delta", "value": -1}],
    )


def _cai_cai_an_gui_jing(judgement: dict[str, Any]) -> dict[str, Any]:
    """求财: 停榻者,喜财安而鬼静 -> 吉"""
    return _base_rule(
        judgement,
        rule_id="classic_huangjince_dynamic_cai_cai_an_gui_jing",
        priority=96,
        conditions={
            "op": "AND",
            "children": [
                _question_type("cai"),
                _line_exists("cai"),
                {"fact_type": "line.is_moving", "subject": "cai", "relation": "is_false"},
                _line_exists("gui"),
                {"fact_type": "line.is_moving", "subject": "gui", "relation": "is_false"},
            ],
        },
        ji_xiong="吉",
        pattern="经典候选: 求财财安鬼静",
        explanation="《黄金策》云: 停榻者,喜财安而鬼静。求财停榻经营之占中财爻安静且官鬼不动,财事安稳少扰,可作吉象候选证据。",
        effects=[{"type": "sign", "value": "cai_cai_an_gui_jing"}, {"type": "score_delta", "value": 1}],
    )


def _zhongzuo_fu_de_kong_wang(judgement: dict[str, Any]) -> dict[str, Any]:
    """种作: 空亡福德,损耗难凭 -> 凶"""
    return _base_rule(
        judgement,
        rule_id="classic_huangjince_dynamic_zhongzuo_fu_de_kong_wang",
        priority=97,
        conditions={
            "op": "AND",
            "children": [
                _line_exists("zi"),
                {"fact_type": "line.is_empty", "subject": "zi", "relation": "is_true"},
            ],
        },
        ji_xiong="凶",
        pattern="经典候选: 种作福德空亡",
        explanation="《黄金策》云: 空亡福德,损耗难凭。种作占中福德子孙空亡,收成护持不足、损耗难免,可作凶象候选证据。",
        effects=[{"type": "sign", "value": "zhongzuo_fu_de_kong_wang"}, {"type": "score_delta", "value": -1}],
    )


def _kaoshi_shen_xing_bian_gui(judgement: dict[str, Any]) -> dict[str, Any]:
    """求名考试: 身兴变鬼,来试方成 -> 吉"""
    return _base_rule(
        judgement,
        rule_id="classic_huangjince_dynamic_kaoshi_shen_xing_bian_gui",
        priority=98,
        conditions={
            "op": "AND",
            "children": [
                _question_type("kaoshi"),
                _line_exists("shi"),
                {"fact_type": "line.wangshuai.overall", "subject": "shi", "relation": "in", "value": ["旺", "相"]},
                {"fact_type": "line.bian.liu_qin", "subject": "shi", "relation": "eq", "value": "官鬼"},
            ],
        },
        ji_xiong="吉",
        pattern="经典候选: 求名身兴变鬼",
        explanation="《黄金策》云: 身兴变鬼,来试方成。求名考试占中世爻旺相并化官鬼,自身状态足以承接名位考试之象,可作吉象候选证据。",
        effects=[{"type": "sign", "value": "kaoshi_shen_xing_bian_gui"}, {"type": "score_delta", "value": 1}],
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
    # 第三批
    "classic_huangjince_fb65e40b559f": _bing_shi_fumu,
    "classic_huangjince_dd137759d041": _hun_shi_wang,
    "classic_huangjince_fda6078e13b5": _kaoshi_shi_empty,
    "classic_huangjince_56e35c8c5439": _chuxing_shi_ying_both_empty,
    # 第四批：3个新增模板
    "classic_huangjince_e22183be6692": _kaoshi_shi_wang,
    "classic_huangjince_902d8f46b5d2": _cisong_shi_ying_sheng_he,
    "classic_huangjince_315234a45a5b": _shiwu_chuxing_yong_sheng_shi,
    # 第五批：6个新增模板
    "classic_huangjince_e76a35169ca2": _bing_ghost_moving,
    "classic_huangjince_d6af404498fe": _guan_ke_shi,
    "classic_huangjince_e96377c94507": _shi_empty,
    "classic_huangjince_fa5b1788201c": _cai_ghost_moving_sheng_shi,
    "classic_huangjince_9df0de5a2802": _shiwu_shi_wang,
    "classic_huangjince_2c5fd1238961": _ying_ke_shi,
    # 第六批：6个新增模板
    "classic_huangjince_0136069ef46b": _fu_gui_ju_kong,
    "classic_huangjince_7e599b005c33": _hun_cai_gui_kong,
    "classic_huangjince_d4610eaac6a5": _cai_hua_zi_sun,
    "classic_huangjince_b5b2d8a74803": _cai_fu_chi_shi,
    "classic_huangjince_cd1e3335381f": _fu_hua_ji_yao,
    "classic_huangjince_9dd8f3982e60": _hun_shi_ying_hua_kong,
    # 第七批: 8个新增模板
    "classic_huangjince_ea7f03d649e3": _dong_bian_jiao_zheng,
    "classic_huangjince_3df5877fb633": _zi_kong_hua_kong,
    "classic_huangjince_392c4fc88df6": _he_zhu_chong_po,
    "classic_huangjince_4026a281d537": _xiu_qiu_sheng_wang,
    "classic_huangjince_f5db80eae9d2": _hun_liu_he,
    "classic_huangjince_c4e29ffd49b4": _hun_liu_chong,
    "classic_huangjince_b6f05d3e19cf": _hun_ri_he_bi_he,
    "classic_huangjince_903555b3f3bb": _cisong_shi_wang_ying_shuai,
    # 第八批: 8个新增模板
    "classic_huangjince_ba4986179311": _liu_xu_shi_wang_cai_xing,
    "classic_huangjince_9537ac3bd02e": _cai_dong_xiu_wang_xuan,
    "classic_huangjince_68d70eea00a7": _cai_zuo_xiu_xiu_hua_di,
    "classic_huangjince_9acc5ae8c313": _chuxing_jian_ju_kong,
    "classic_huangjince_2722b52d14be": _yong_wang_er_fei,
    "classic_huangjince_4aa2e9b05ff6": _chuxing_yong_shang_ru_mu,
    "classic_huangjince_ce908ed3a7a7": _sui_jun_yi_jing,
    "classic_huangjince_3705ea743805": _jue_feng_sheng,
    # 第九批: 6个新增模板
    "classic_huangjince_c0500123b276": _qiuguan_cai_dong,
    "classic_huangjince_1b5bd6fa713e": _tianshi_ying_empty,
    "classic_huangjince_e3a016ab43d1": _cai_lai_jiu_wo,
    "classic_huangjince_95b746989412": _xingren_feng_chong,
    "classic_huangjince_0bbb18b44908": _fumu_chi_shi,
    "classic_huangjince_992af61aee72": _cai_kong_shi,

    "classic_huangjince_774d6b5442e0": _hun_gui_ke_fei_yao,
    "classic_huangjince_36842a66707c": _cisong_fu_dong_guan_hua_fu,
    "classic_huangjince_24d2e60b3f98": _cai_ju_he_fu_shen,
    "classic_huangjince_bb0611ef4c46": _cai_xiong_lian_gui_ke,
    "classic_huangjince_d41bfe9bbb31": _cai_dong_shen_xing,
    "classic_huangjince_525c267fac83": _qiushi_jing_he_fu_yao,

    # 第十一批: 6个新增模板
    "classic_huangjince_89b7ac9834eb": _hun_yong_sheng_he_shi,
    "classic_huangjince_44bcba94b554": _liuxu_cai_kong_fu_dong,
    "classic_huangjince_11bfc1cee9b4": _shiwu_cai_dong_bu_yi,
    "classic_huangjince_42f7ef7b3b21": _cai_cai_an_gui_jing,
    "classic_huangjince_f35e5ee390b4": _zhongzuo_fu_de_kong_wang,
    "classic_huangjince_9779698aa51c": _kaoshi_shen_xing_bian_gui,



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
