"""Schema helpers for reviewed/candidate classic Liuyao dynamic rules.

本模块只校验《黄金策》候选规则的结构化形态, 不把古籍断语直接升级为
P0/P1 终局规则。候选规则必须先满足可编译 schema, 再由动态规则层以
``stop=False`` 的方式输出证据, 避免污染既有吉凶主判。
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

ALLOWED_SOURCES = {"huangjince"}
ALLOWED_REVIEW_STATUS = {"candidate", "reviewed", "approved", "rejected"}
ALLOWED_COMPILABILITY = {"auto_compilable", "needs_fact_extractor", "not_compilable"}
ALLOWED_EXECUTION_TIERS = {"candidate_only", "reviewed_evidence", "core_candidate"}
ALLOWED_EFFECT_TYPES = {"sign", "score_delta", "delay", "block"}
ALLOWED_JI_XIONG = {"吉", "凶", "平"}
ALLOWED_CONDITION_OPS = {"AND", "OR", "NOT"}
ALLOWED_RELATIONS = {
    "eq",
    "neq",
    "in",
    "contains",
    "is_true",
    "is_false",
    "sheng",
    "ke",
    "he",
    "chong",
}
ALLOWED_FACT_TYPES = {
    "question.type",
    "line.exists",
    "line.role",
    "line.position",
    "line.liu_qin",
    "line.wu_xing",
    "line.di_zhi",
    "line.is_shi",
    "line.is_ying",
    "line.is_moving",
    "line.is_empty",
    "line.wangshuai.overall",
    "line.wangshuai.month_wang",
    "line.wangshuai.month_shuai",
    "line.wangshuai.day_wang",
    "line.wangshuai.day_shuai",
    "line.moving.trend_wang",
    "line.moving.trend_shuai",
    "line.moving.is_useless",
    "line.bian.di_zhi",
    "line.bian.wu_xing",
    "line.bian.liu_qin",
    "relationship.sheng",
    "relationship.ke",
    "relationship.he",
    "relationship.chong",
}

REQUIRED_RULE_FIELDS = {
    "id",
    "source",
    "source_text",
    "source_file",
    "line_start",
    "line_end",
    "section",
    "review_status",
    "compilability",
    "execution_tier",
    "priority",
    "conditions",
    "conclusion",
    "effects",
    "safety",
}

REQUIRED_CONCLUSION_FIELDS = {"ji_xiong", "pattern", "explanation"}
REQUIRED_SAFETY_FIELDS = {"allow_override", "p0_safe", "notes"}


@dataclass(frozen=True)
class ValidationIssue:
    """候选规则 schema 校验问题。"""

    path: str
    message: str


def validate_classic_rule(rule: dict[str, Any]) -> list[ValidationIssue]:
    """Validate one dynamic classic rule record."""
    issues: list[ValidationIssue] = []
    missing = sorted(REQUIRED_RULE_FIELDS - set(rule))
    for field in missing:
        issues.append(ValidationIssue(field, "missing required field"))
    if missing:
        return issues

    _require_non_empty_string(rule, "id", issues)
    _require_non_empty_string(rule, "source_text", issues)
    _require_non_empty_string(rule, "source_file", issues)
    _require_non_empty_string(rule, "section", issues)
    _require_int(rule, "line_start", issues, minimum=1)
    _require_int(rule, "line_end", issues, minimum=1)
    _require_int(rule, "priority", issues, minimum=1)

    if rule.get("source") not in ALLOWED_SOURCES:
        issues.append(ValidationIssue("source", "only huangjince candidate rules are allowed"))
    if rule.get("review_status") not in ALLOWED_REVIEW_STATUS:
        issues.append(ValidationIssue("review_status", "invalid review status"))
    if rule.get("compilability") not in ALLOWED_COMPILABILITY:
        issues.append(ValidationIssue("compilability", "invalid compilability"))
    if rule.get("execution_tier") not in ALLOWED_EXECUTION_TIERS:
        issues.append(ValidationIssue("execution_tier", "invalid execution tier"))

    if rule.get("compilability") == "not_compilable" and rule.get("execution_tier") != "candidate_only":
        issues.append(ValidationIssue("execution_tier", "not_compilable rules must remain candidate_only"))

    _validate_condition_node(rule.get("conditions"), "conditions", issues)
    _validate_conclusion(rule.get("conclusion"), issues)
    _validate_effects(rule.get("effects"), issues)
    _validate_safety(rule.get("safety"), issues)
    return issues


def validate_classic_rules(rules: Iterable[dict[str, Any]]) -> list[ValidationIssue]:
    """Validate multiple classic rule records."""
    issues: list[ValidationIssue] = []
    seen_ids: set[str] = set()
    for index, rule in enumerate(rules):
        rule_id = rule.get("id")
        if isinstance(rule_id, str):
            if rule_id in seen_ids:
                issues.append(ValidationIssue(f"rules[{index}].id", "duplicate rule id"))
            seen_ids.add(rule_id)
        for issue in validate_classic_rule(rule):
            issues.append(ValidationIssue(f"rules[{index}].{issue.path}", issue.message))
    return issues


def assert_valid_classic_rule(rule: dict[str, Any]) -> None:
    """Raise ValueError when a classic rule does not satisfy schema."""
    issues = validate_classic_rule(rule)
    if issues:
        formatted = "; ".join(f"{issue.path}: {issue.message}" for issue in issues)
        raise ValueError(f"invalid classic rule: {formatted}")


def _require_non_empty_string(rule: dict[str, Any], field: str, issues: list[ValidationIssue]) -> None:
    value = rule.get(field)
    if not isinstance(value, str) or not value.strip():
        issues.append(ValidationIssue(field, "must be a non-empty string"))


def _require_int(rule: dict[str, Any], field: str, issues: list[ValidationIssue], *, minimum: int | None = None) -> None:
    value = rule.get(field)
    if not isinstance(value, int):
        issues.append(ValidationIssue(field, "must be an integer"))
        return
    if minimum is not None and value < minimum:
        issues.append(ValidationIssue(field, f"must be >= {minimum}"))


def _validate_condition_node(node: Any, path: str, issues: list[ValidationIssue]) -> None:
    if not isinstance(node, dict):
        issues.append(ValidationIssue(path, "condition node must be an object"))
        return

    op = node.get("op")
    if op in ALLOWED_CONDITION_OPS:
        children = node.get("children")
        if not isinstance(children, list) or not children:
            issues.append(ValidationIssue(f"{path}.children", "operator node requires non-empty children"))
            return
        if op == "NOT" and len(children) != 1:
            issues.append(ValidationIssue(f"{path}.children", "NOT operator requires exactly one child"))
        for index, child in enumerate(children):
            _validate_condition_node(child, f"{path}.children[{index}]", issues)
        return

    fact_type = node.get("fact_type")
    if fact_type not in ALLOWED_FACT_TYPES:
        issues.append(ValidationIssue(f"{path}.fact_type", "invalid or missing fact type"))
    relation = node.get("relation")
    if relation not in ALLOWED_RELATIONS:
        issues.append(ValidationIssue(f"{path}.relation", "invalid or missing relation"))
    if "value" not in node and relation not in {"is_true", "is_false"}:
        issues.append(ValidationIssue(f"{path}.value", "missing value for relation"))


def _validate_conclusion(conclusion: Any, issues: list[ValidationIssue]) -> None:
    if not isinstance(conclusion, dict):
        issues.append(ValidationIssue("conclusion", "must be an object"))
        return
    missing = sorted(REQUIRED_CONCLUSION_FIELDS - set(conclusion))
    for field in missing:
        issues.append(ValidationIssue(f"conclusion.{field}", "missing required field"))
    if conclusion.get("ji_xiong") not in ALLOWED_JI_XIONG:
        issues.append(ValidationIssue("conclusion.ji_xiong", "invalid ji_xiong"))
    for field in ("pattern", "explanation"):
        value = conclusion.get(field)
        if not isinstance(value, str) or not value.strip():
            issues.append(ValidationIssue(f"conclusion.{field}", "must be a non-empty string"))


def _validate_effects(effects: Any, issues: list[ValidationIssue]) -> None:
    if not isinstance(effects, list) or not effects:
        issues.append(ValidationIssue("effects", "must be a non-empty list"))
        return
    for index, effect in enumerate(effects):
        if not isinstance(effect, dict):
            issues.append(ValidationIssue(f"effects[{index}]", "must be an object"))
            continue
        if effect.get("type") not in ALLOWED_EFFECT_TYPES:
            issues.append(ValidationIssue(f"effects[{index}].type", "invalid effect type"))
        if "value" not in effect:
            issues.append(ValidationIssue(f"effects[{index}].value", "missing effect value"))


def _validate_safety(safety: Any, issues: list[ValidationIssue]) -> None:
    if not isinstance(safety, dict):
        issues.append(ValidationIssue("safety", "must be an object"))
        return
    missing = sorted(REQUIRED_SAFETY_FIELDS - set(safety))
    for field in missing:
        issues.append(ValidationIssue(f"safety.{field}", "missing required field"))
    if safety.get("allow_override") is not False:
        issues.append(ValidationIssue("safety.allow_override", "candidate classic rules must not override core judgement"))
    if safety.get("p0_safe") is not True:
        issues.append(ValidationIssue("safety.p0_safe", "candidate classic rules must be marked p0_safe"))
