"""Dynamic adapter for structured classic Liuyao candidate rules."""

from __future__ import annotations

import json
from collections.abc import Iterable
from functools import lru_cache
from pathlib import Path
from typing import Any

from .classic_rule_schema import assert_valid_classic_rule
from .fact_extractor import ClassicRuleFacts, extract_classic_rule_facts
from .result import RuleResult

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_HUANGJINCE_RULES_PATH = ROOT / "data" / "huangjince_candidate_rules.jsonl"


class DynamicClassicRule:
    """Executable wrapper for one reviewed/candidate classic rule."""

    def __init__(self, record: dict[str, Any]):
        assert_valid_classic_rule(record)
        self.record = record
        self.rule_id = record["id"]
        self.theory_id = f"classic:{record['source']}:{record['section']}"
        self.priority = int(record.get("priority", 1))
        self.question_types = _extract_required_question_types(record["conditions"])

    def evaluate(self, context: Any, facts: ClassicRuleFacts | None = None) -> RuleResult | None:
        """Evaluate a candidate classic rule without overriding core judgement."""
        if self.record.get("draft_status") == "draft_only":
            return None
        if self.record.get("review_status") == "rejected":
            return None
        if self.record.get("compilability") == "not_compilable":
            return None

        if facts is None:
            facts = extract_classic_rule_facts(context)
        if not evaluate_condition(self.record["conditions"], facts):
            return None

        conclusion = self.record["conclusion"]
        evidence_subjects = _collect_condition_subjects(self.record["conditions"])
        evidence = facts.evidence_for_subjects(*evidence_subjects)
        evidence.append({
            "source": self.record["source"],
            "source_text": self.record["source_text"],
            "source_file": self.record["source_file"],
            "line_start": self.record["line_start"],
            "line_end": self.record["line_end"],
            "review_status": self.record["review_status"],
            "execution_tier": self.record["execution_tier"],
            "effects": self.record["effects"],
            "safety": self.record["safety"],
        })

        return RuleResult(
            matched=True,
            priority=self.priority,
            pattern=conclusion["pattern"],
            ji_xiong=conclusion["ji_xiong"],
            explanation=conclusion["explanation"],
            stop=False,
            rule_id=self.rule_id,
            theory_id=self.theory_id,
            evidence=evidence,
        )


def evaluate_condition(node: dict[str, Any], facts: ClassicRuleFacts) -> bool:
    """Evaluate a JSON condition AST against extracted facts."""
    op = node.get("op")
    if op == "AND":
        return all(evaluate_condition(child, facts) for child in node.get("children", []))
    if op == "OR":
        return any(evaluate_condition(child, facts) for child in node.get("children", []))
    if op == "NOT":
        children = node.get("children", [])
        return len(children) == 1 and not evaluate_condition(children[0], facts)

    fact_type = node["fact_type"]
    relation = node["relation"]
    subject = node.get("subject")
    object_ = node.get("object")

    if fact_type.startswith("relationship."):
        relationship = fact_type.removeprefix("relationship.")
        return facts.relationship(relationship, subject, object_)

    actual = facts.value_for(fact_type, subject)
    expected = node.get("value")
    return _compare(actual, relation, expected)


def load_dynamic_classic_rule_records(path: Path | None = None) -> list[dict[str, Any]]:
    """Load structured classic rule records from JSONL."""
    data_path = path or DEFAULT_HUANGJINCE_RULES_PATH
    records: list[dict[str, Any]] = []
    with data_path.open("r", encoding="utf-8") as file:
        for line in file:
            if line.strip():
                records.append(json.loads(line))
    return records


@lru_cache(maxsize=1)
def get_huangjince_candidate_rules() -> tuple[DynamicClassicRule, ...]:
    """Return compiled candidate-only 《黄金策》 dynamic rules."""
    return tuple(DynamicClassicRule(record) for record in load_dynamic_classic_rule_records())


@lru_cache(maxsize=1)
def get_sorted_huangjince_candidate_rules() -> tuple[DynamicClassicRule, ...]:
    """Return default dynamic rules sorted by priority once per process."""
    return tuple(sorted(
        get_huangjince_candidate_rules(),
        key=lambda item: item.priority,
        reverse=True,
    ))


@lru_cache(maxsize=32)
def get_huangjince_candidate_rules_for_question(question_type: str | None) -> tuple[DynamicClassicRule, ...]:
    """Return sorted dynamic rules that can apply to the given question type."""
    rules = get_sorted_huangjince_candidate_rules()
    if not question_type:
        return rules
    return tuple(
        rule for rule in rules
        if not rule.question_types or question_type in rule.question_types
    )


def evaluate_dynamic_classic_rules(context: Any, rules: Iterable[DynamicClassicRule] | None = None) -> list[RuleResult]:
    """Evaluate dynamic classic rules and return all non-terminal matches."""
    rule_set = (
        tuple(sorted(rules, key=lambda item: item.priority, reverse=True))
        if rules is not None
        else get_huangjince_candidate_rules_for_question(getattr(context, "question_type", None))
    )
    facts = extract_classic_rule_facts(context)
    results = []
    for rule in rule_set:
        result = rule.evaluate(context, facts)
        if result and result.matched:
            results.append(result)
    return results


def best_dynamic_classic_rule(context: Any, rules: Iterable[DynamicClassicRule] | None = None) -> RuleResult | None:
    """Return the highest priority matching dynamic classic rule."""
    results = evaluate_dynamic_classic_rules(context, rules)
    if not results:
        return None
    return results[0]


def _compare(actual: Any, relation: str, expected: Any) -> bool:
    if relation == "eq":
        return actual == expected
    if relation == "neq":
        return actual != expected
    if relation == "in":
        return actual in expected if isinstance(expected, list | tuple | set) else False
    if relation == "contains":
        if isinstance(actual, list | tuple | set):
            return expected in actual
        if isinstance(actual, str):
            return str(expected) in actual
        return False
    if relation == "is_true":
        return actual is True
    if relation == "is_false":
        return actual is False
    return False


def _extract_required_question_types(node: dict[str, Any]) -> frozenset[str]:
    if node.get("op") != "AND":
        return frozenset()

    for child in node.get("children", []):
        direct = _question_type_values(child)
        if direct:
            return frozenset(direct)
    return frozenset()


def _question_type_values(node: dict[str, Any]) -> set[str]:
    if node.get("op") == "OR":
        values: set[str] = set()
        for child in node.get("children", []):
            child_values = _question_type_values(child)
            if not child_values:
                return set()
            values.update(child_values)
        return values

    if (
        node.get("fact_type") == "question.type"
        and node.get("relation") == "eq"
        and isinstance(node.get("value"), str)
    ):
        return {node["value"]}
    return set()


def _collect_condition_subjects(node: dict[str, Any]) -> list[str | int | None]:
    subjects: list[str | int | None] = []
    if node.get("op") in {"AND", "OR", "NOT"}:
        for child in node.get("children", []):
            subjects.extend(_collect_condition_subjects(child))
        return _dedupe_subjects(subjects)
    subjects.append(node.get("subject"))
    if node.get("object") is not None:
        subjects.append(node.get("object"))
    return _dedupe_subjects(subjects)


def _dedupe_subjects(subjects: list[str | int | None]) -> list[str | int | None]:
    result: list[str | int | None] = []
    seen = set()
    for subject in subjects:
        marker = str(subject)
        if marker in seen:
            continue
        seen.add(marker)
        result.append(subject)
    return result
