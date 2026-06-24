# -*- coding: utf-8 -*-
"""《黄金策》候选规则自动保守编译测试。"""

from __future__ import annotations

import json
from pathlib import Path

from liuyao.domain.rules.classic_rule_schema import validate_classic_rules
from scripts.auto_compile_huangjince_candidate_rules import build_auto_compiled_rules, merge_candidate_rules

ROOT = Path(__file__).resolve().parents[1]
CLASSIC_JUDGEMENTS_PATH = ROOT / "data" / "classic_judgements.jsonl"
CANDIDATE_RULES_PATH = ROOT / "data" / "huangjince_candidate_rules.jsonl"

AUTO_COMPILED_RULE_IDS = {
    "classic_huangjince_dynamic_primary_yong_moving_decline",
    "classic_huangjince_dynamic_shi_ying_empty_he",
    "classic_huangjince_dynamic_chuxing_ying_ke_shi",
    "classic_huangjince_dynamic_chuxing_ying_empty",
    "classic_huangjince_dynamic_hun_shi_ying_relationships",
    "classic_huangjince_dynamic_hun_shi_ying_he",
    "classic_huangjince_dynamic_hun_ying_moving_or_empty",
    "classic_huangjince_dynamic_hun_shi_ying_both_empty",
    "classic_huangjince_dynamic_bing_shi_ghost",
    "classic_huangjince_dynamic_chuxing_shi_empty",
}


def _jsonl(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as file:
        return [json.loads(line) for line in file if line.strip()]


def test_auto_compile_builds_known_conservative_templates():
    judgements = _jsonl(CLASSIC_JUDGEMENTS_PATH)

    generated = build_auto_compiled_rules(judgements)

    assert len(generated) == 10
    assert {rule["id"] for rule in generated} == AUTO_COMPILED_RULE_IDS
    assert validate_classic_rules(generated) == []
    assert all(rule["execution_tier"] == "candidate_only" for rule in generated)
    assert all(rule["safety"]["allow_override"] is False for rule in generated)
    assert all(rule["safety"]["p0_safe"] is True for rule in generated)
    assert all("仅编译现有事实抽取器可表达的部分" in rule["safety"]["notes"] for rule in generated)


def test_auto_compile_merge_is_deterministic_and_idempotent():
    judgements = _jsonl(CLASSIC_JUDGEMENTS_PATH)
    candidate_rules = _jsonl(CANDIDATE_RULES_PATH)
    generated = build_auto_compiled_rules(judgements)

    merged_once = merge_candidate_rules(candidate_rules, generated)
    merged_twice = merge_candidate_rules(merged_once, generated)

    assert merged_once == merged_twice
    assert len(merged_once) == 13
    assert validate_classic_rules(merged_once) == []
    assert {rule["id"] for rule in generated}.issubset({rule["id"] for rule in merged_once})
    assert [rule["id"] for rule in merged_once[:3]] == [rule["id"] for rule in candidate_rules[:3]]
