# -*- coding: utf-8 -*-
"""《黄金策》动态规则草稿审计队列测试。

审计队列用于人工编译排期，不作为运行时动态规则入口。
"""

from __future__ import annotations

import json
from pathlib import Path

from liuyao.domain.rules.dynamic_rules import get_huangjince_candidate_rules
from scripts.audit_huangjince_dynamic_rule_drafts import build_audit_report, build_compile_queue

ROOT = Path(__file__).resolve().parents[1]
DRAFTS_PATH = ROOT / "data" / "huangjince_dynamic_rule_drafts.jsonl"
AUDIT_PATH = ROOT / "data" / "huangjince_dynamic_rule_draft_audit.json"
QUEUE_PATH = ROOT / "data" / "huangjince_dynamic_rule_compile_queue.jsonl"
CANDIDATE_RULES_PATH = ROOT / "data" / "huangjince_candidate_rules.jsonl"


def _jsonl(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as file:
        return [json.loads(line) for line in file if line.strip()]


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_huangjince_dynamic_rule_audit_outputs_exist_and_are_isolated():
    assert AUDIT_PATH.exists()
    assert QUEUE_PATH.exists()
    assert CANDIDATE_RULES_PATH.exists()

    audit = _json(AUDIT_PATH)
    queue = _jsonl(QUEUE_PATH)
    candidate_rules = _jsonl(CANDIDATE_RULES_PATH)

    assert audit["runtime_isolation"]["candidate_rules_path"] == "data/huangjince_candidate_rules.jsonl"
    assert "data/huangjince_dynamic_rule_compile_queue.jsonl" in audit["runtime_isolation"]["audit_outputs"]
    assert len(candidate_rules) == 13
    assert len(queue) == audit["queue_size"]
    assert all(item["runtime_isolation"]["default_loader"] == "not_loaded" for item in queue)


def test_huangjince_dynamic_rule_audit_statistics_match_drafts():
    drafts = _jsonl(DRAFTS_PATH)
    audit = _json(AUDIT_PATH)

    compiled = [draft for draft in drafts if draft.get("compiled_rule_id")]
    manual = [draft for draft in drafts if not draft.get("compiled_rule_id")]

    assert audit["total_drafts"] == len(drafts)
    assert audit["compiled_drafts"] == len(compiled) == 13
    assert audit["manual_compile_drafts"] == len(manual)
    assert audit["by_compilability"]["auto_compilable"] == 13
    assert audit["by_compilability"]["not_compilable"] == len(manual)


def test_huangjince_dynamic_rule_compile_queue_is_deterministic_against_drafts():
    drafts = _jsonl(DRAFTS_PATH)
    saved_queue = _jsonl(QUEUE_PATH)
    rebuilt_queue = build_compile_queue(drafts)

    assert rebuilt_queue == saved_queue
    assert len(saved_queue) >= 200
    assert all(item["queue_id"].startswith("compile_queue_classic_huangjince_") for item in saved_queue)
    assert all(not item["draft_id"].startswith("classic_huangjince_dynamic_") for item in saved_queue)


def test_huangjince_dynamic_rule_compile_queue_is_ranked_and_traceable():
    queue = _jsonl(QUEUE_PATH)
    scores = [item["compile_priority_score"] for item in queue]

    assert scores == sorted(scores, reverse=True)
    first = queue[0]
    assert first["source"] == "huangjince"
    assert first["source_file"].startswith("docs/reference/huangjince/")
    assert first["line_start"] >= 1
    assert first["source_text"]
    assert first["suggested_fact_targets"]
    assert "人工拆分条件 AST" in first["suggested_next_step"]
    assert any("现有事实抽取器" in reason for reason in first["compile_priority_reasons"])


def test_huangjince_dynamic_rule_audit_report_is_deterministic_against_queue():
    drafts = _jsonl(DRAFTS_PATH)
    queue = _jsonl(QUEUE_PATH)
    saved_audit = _json(AUDIT_PATH)
    rebuilt_audit = build_audit_report(drafts, queue)

    assert rebuilt_audit == saved_audit


def test_huangjince_dynamic_rule_compile_queue_does_not_change_default_runtime_rules():
    get_huangjince_candidate_rules.cache_clear()
    rules = get_huangjince_candidate_rules()
    queue_ids = {item["queue_id"] for item in _jsonl(QUEUE_PATH)}

    assert len(rules) == 13
    assert all(rule.rule_id not in queue_ids for rule in rules)
    assert all(not rule.rule_id.startswith("compile_queue_") for rule in rules)
