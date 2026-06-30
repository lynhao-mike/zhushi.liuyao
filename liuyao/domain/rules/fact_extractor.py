"""Minimal fact extraction for dynamic classic Liuyao rules.

事实抽取器只读取 ``RuleContext`` 已有卦象、旺衰、动变信息, 不新增吉凶
判定逻辑。动态规则层基于这些事实做候选规则匹配。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from liuyao.domain.data import LIU_CHONG, LIU_HE, WU_XING_KE, WU_XING_SHENG


@dataclass(frozen=True)
class ClassicRuleFacts:
    """RuleContext 的轻量事实视图。"""

    context: Any

    def line_for(self, subject: str | int | None) -> Any | None:
        """Resolve a rule subject to a hexagram line."""
        if subject in (None, ""):
            return None
        if subject == "shi":
            return self.context.shi_line
        if subject == "ying":
            return getattr(self.context.hexagram, "ying_line", None)
        if subject in ("primary_yong", "yong"):
            return self.context.primary_yong
        if isinstance(subject, int):
            return self.context.hexagram.lines_by_position.get(subject)
        if isinstance(subject, str) and subject.isdigit():
            return self.context.hexagram.lines_by_position.get(int(subject))
        return None

    def matching_lines(self, subject: str | int | None) -> list[Any]:
        """Return candidate lines for a subject expression."""
        if subject in ("any", "line", "*"):
            return list(self.context.hexagram.lines)
        line = self.line_for(subject)
        return [line] if line is not None else []

    def value_for(self, fact_type: str, subject: str | int | None = None) -> Any:
        """Return a scalar/list value for line or question facts."""
        if fact_type == "question.type":
            return self.context.question_type

        line = self.line_for(subject)
        if not line:
            return None

        if fact_type == "line.exists":
            return True
        if fact_type == "line.role":
            if getattr(line, "is_shi", False):
                return "shi"
            if getattr(line, "is_ying", False):
                return "ying"
            return "line"
        if fact_type == "line.position":
            return line.position
        if fact_type == "line.liu_qin":
            return line.liu_qin
        if fact_type == "line.wu_xing":
            return line.wu_xing
        if fact_type == "line.di_zhi":
            return line.di_zhi
        if fact_type == "line.is_shi":
            return bool(getattr(line, "is_shi", False))
        if fact_type == "line.is_ying":
            return bool(getattr(line, "is_ying", False))
        if fact_type == "line.is_moving":
            return bool(getattr(line, "is_moving", False))
        if fact_type == "line.is_empty":
            return bool(getattr(line, "is_xun_kong", False))

        if fact_type.startswith("line.wangshuai."):
            ws = self.context.wangshuai_of(line)
            key = fact_type.removeprefix("line.wangshuai.")
            return ws.get(key)

        if fact_type.startswith("line.moving."):
            moving = self.context.moving_analyses.get(line.position, {})
            key = fact_type.removeprefix("line.moving.")
            if key == "trend_wang":
                return moving.get("趋旺", [])
            if key == "trend_shuai":
                return moving.get("趋衰", [])
            if key == "is_useless":
                return bool(moving.get("is_useless", False))
            return moving.get(key)

        if fact_type == "line.bian.di_zhi":
            return getattr(line, "bian_di_zhi", None)
        if fact_type == "line.bian.wu_xing":
            return getattr(line, "bian_wu_xing", None)
        if fact_type == "line.bian.liu_qin":
            return getattr(line, "bian_liu_qin", None)

        return None

    def relationship(self, relation: str, subject: str | int | None, object_: str | int | None) -> bool:
        """Evaluate a five-element/branch relationship between two subjects."""
        left = self.line_for(subject)
        right = self.line_for(object_)
        if not left or not right:
            return False
        if relation == "sheng":
            return WU_XING_SHENG.get(left.wu_xing) == right.wu_xing
        if relation == "ke":
            return WU_XING_KE.get(left.wu_xing) == right.wu_xing
        if relation == "he":
            return LIU_HE.get(left.di_zhi, (None, None))[0] == right.di_zhi
        if relation == "chong":
            return LIU_CHONG.get(left.di_zhi) == right.di_zhi
        return False

    def evidence_for_subjects(self, *subjects: str | int | None) -> list[dict[str, Any]]:
        """Build traceable evidence dictionaries for rule output."""
        evidence = []
        seen = set()
        for subject in subjects:
            for line in self.matching_lines(subject):
                if line.position in seen:
                    continue
                seen.add(line.position)
                entry = {
                    "position": line.position,
                    "role": "shi" if line.is_shi else "ying" if line.is_ying else "line",
                    "di_zhi": line.di_zhi,
                    "wu_xing": line.wu_xing,
                    "liu_qin": line.liu_qin,
                    "is_moving": line.is_moving,
                    "is_empty": line.is_xun_kong,
                    "wangshuai": self.context.wangshuai_of(line),
                }
                moving = self.context.moving_analyses.get(line.position)
                if moving:
                    entry["moving"] = moving
                if getattr(line, "bian_di_zhi", None):
                    entry["bian"] = {
                        "di_zhi": line.bian_di_zhi,
                        "wu_xing": line.bian_wu_xing,
                        "liu_qin": line.bian_liu_qin,
                    }
                evidence.append(entry)
        return evidence


def extract_classic_rule_facts(context: Any) -> ClassicRuleFacts:
    """Create a fact view from RuleContext."""
    return ClassicRuleFacts(context)
