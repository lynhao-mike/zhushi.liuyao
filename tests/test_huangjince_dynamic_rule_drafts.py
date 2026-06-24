# -*- coding: utf-8 -*-
"""《黄金策》动态规则草稿脚手架测试。

草稿库用于全量规则化审计，不作为默认运行时规则入口。
"""

from __future__ import annotations

import json
from pathlib import Path

from liuyao.domain.rules.classic_rule_schema import validate_classic_rules
from liuyao.domain.rules.dynamic_rules import DynamicClassicRule, get_huangjince_candidate_rules
from scripts.build_huangjince_dynamic_rule_drafts import build_drafts

ROOT = Path(__file__).resolve().parents[1]
DRAFTS_PATH = ROOT / "data" / "huangjince_dynamic_rule_drafts.jsonl"
CANDIDATE_RULES_PATH = ROOT / "data" / "huangjince_candidate_rules.jsonl"
CLASSIC_JUDGEMENTS_PATH = ROOT / "data" / "classic_judgements.jsonl"


def _jsonl(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as file:
        return [json.loads(line) for line in file if line.strip()]


def test_huangjince_dynamic_rule_drafts_exist_and_cover_classic_judgements():
    assert DRAFTS_PATH.exists()
    drafts = _jsonl(DRAFTS_PATH)
    judgements = _jsonl(CLASSIC_JUDGEMENTS_PATH)

    assert len(drafts) == len(judgements)
    assert len(drafts) >= 200
    assert {draft["classic_judgement_id"] for draft in drafts} == {item["id"] for item in judgements}


def test_huangjince_dynamic_rule_drafts_are_schema_safe_and_auditable():
    drafts = _jsonl(DRAFTS_PATH)
    issues = validate_classic_rules(drafts)

    assert issues == []
    assert all(draft["id"].startswith("draft_classic_huangjince_") for draft in drafts)
    assert all(draft["draft_status"] == "draft_only" for draft in drafts)
    assert all(draft["execution_tier"] == "candidate_only" for draft in drafts)
    assert all(draft["safety"]["allow_override"] is False for draft in drafts)
    assert all(draft["safety"]["p0_safe"] is True for draft in drafts)
    assert all("默认运行时不加载" in draft["safety"]["notes"] for draft in drafts)


def test_huangjince_dynamic_rule_drafts_preserve_reviewed_candidate_mapping():
    drafts = _jsonl(DRAFTS_PATH)
    reviewed_rules = _jsonl(CANDIDATE_RULES_PATH)
    compiled_drafts = [draft for draft in drafts if draft["compilability"] == "auto_compilable"]

    assert len(compiled_drafts) == len(reviewed_rules)
    assert {draft["compiled_rule_id"] for draft in compiled_drafts} == {rule["id"] for rule in reviewed_rules}
    for draft in compiled_drafts:
        assert draft["draft_status"] == "draft_only"
        assert draft["id"].startswith("draft_")
        assert draft["compiled_rule_id"] != draft["id"]


def test_build_huangjince_dynamic_rule_drafts_is_deterministic_against_fixture_data():
    built = build_drafts(CLASSIC_JUDGEMENTS_PATH, CANDIDATE_RULES_PATH)
    saved = _jsonl(DRAFTS_PATH)

    assert built == saved


def test_draft_only_records_do_not_enter_default_dynamic_rule_loader():
    get_huangjince_candidate_rules.cache_clear()
    rules = get_huangjince_candidate_rules()

    assert len(rules) == 13
    assert all(not rule.rule_id.startswith("draft_") for rule in rules)


def test_draft_only_records_do_not_evaluate_even_when_loaded_directly():
    draft = next(item for item in _jsonl(DRAFTS_PATH) if item.get("compiled_rule_id"))
    rule = DynamicClassicRule(draft)

    assert rule.evaluate(context=None) is None
