"""
规则结果 - Rule Result
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass(order=True)
class RuleResult:
    """单条规则命中后的统一输出。"""

    priority: int
    matched: bool = field(compare=False, default=False)
    pattern: str = field(compare=False, default="")
    ji_xiong: str = field(compare=False, default="平")
    explanation: str = field(compare=False, default="")
    stop: bool = field(compare=False, default=True)
    rule_id: str = field(compare=False, default="")
    theory_id: str = field(compare=False, default="")
    evidence: List[Dict[str, Any]] = field(compare=False, default_factory=list)

    def to_jixiong(self) -> Dict[str, Any]:
        """转换为既有 jixiong_result 字典格式。"""
        result = {
            "pattern": self.pattern,
            "ji_xiong": self.ji_xiong,
            "explanation": self.explanation,
        }
        if self.rule_id:
            result["rule_id"] = self.rule_id
        if self.theory_id:
            result["theory_id"] = self.theory_id
        if self.evidence:
            result["evidence"] = self.evidence
        return result
