"""
规则引擎 - Rule Engine

按优先级执行规则。第一条 ``matched=True`` 且 ``stop=True`` 的规则终止评估。
"""

from typing import Iterable, Optional

from .result import RuleResult


class RuleEngine:
    """轻量规则引擎。"""

    def __init__(self, rules: Iterable[object]):
        self.rules = sorted(rules, key=lambda rule: getattr(rule, "priority", 0), reverse=True)

    def evaluate(self, context) -> Optional[RuleResult]:
        """执行规则集, 返回最高优先级命中结果。"""
        best = None
        for rule in self.rules:
            result = rule.evaluate(context)
            if not result or not result.matched:
                continue
            if result.stop:
                return result
            if best is None or result.priority > best.priority:
                best = result
        return best
