"""
规则上下文 - Rule Context

集中承载吉凶规则所需的基础事实, 避免继续把高优先级规则堆叠到
``jixiong.judge_dong_gua`` 的线性 if/else 中。
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class RuleContext:
    """吉凶规则评估上下文。"""

    hexagram: Any
    yong_shen_liu_qin: str
    wangshuai_results: List[Dict[str, Any]]
    dongbian_results: Dict[str, Any]
    question_type: str
    patterns_results: Dict[str, Any] = field(default_factory=dict)
    shi_line: Optional[Any] = None
    primary_yong: Optional[Any] = None
    yong_lines: List[Any] = field(default_factory=list)
    month_zhi: str = ""
    day_zhi: str = ""

    @property
    def moving_analyses(self) -> Dict[int, Dict[str, Any]]:
        return self.dongbian_results.get("moving_analyses", {})

    @property
    def useful_moving(self) -> List[int]:
        return self.dongbian_results.get("useful_moving", [])

    @property
    def san_he_ju(self) -> List[Dict[str, Any]]:
        return self.dongbian_results.get("san_he_ju", [])

    @property
    def san_ban(self) -> List[Dict[str, Any]]:
        return self.patterns_results.get("san_ban", []) if self.patterns_results else []

    def wangshuai_of(self, line: Any) -> Dict[str, Any]:
        return self.wangshuai_results[line.position - 1]
