"""
规则上下文 - Rule Context

集中承载吉凶规则所需的基础事实, 避免继续把高优先级规则堆叠到
``jixiong.judge_dong_gua`` 的线性 if/else 中。
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from liuyao.domain.data import DI_ZHI_WU_XING, LIU_CHONG


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
    def is_competitive_selection(self) -> bool:
        """是否属于短期竞争/差额选拔类占问。"""
        explicit = self.patterns_results.get("competitive_selection") if self.patterns_results else None
        if explicit is not None:
            return bool(explicit)
        return self.question_type == "kaoshi"

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

    @property
    def intervening_positions(self) -> List[int]:
        """世应之间的间爻位置。"""
        ying_line = getattr(self.hexagram, "ying_line", None)
        if not self.shi_line or not ying_line:
            return []
        low, high = sorted((self.shi_line.position, ying_line.position))
        return [pos for pos in range(low + 1, high)]

    def wangshuai_of(self, line: Any) -> Dict[str, Any]:
        return self.wangshuai_results[line.position - 1]

    def moving_decline_reasons(self, line: Any) -> List[str]:
        """返回动爻失势原因, 兼容动变自身衰败与变爻被日月冲破。"""
        moving = self.moving_analyses.get(line.position, {})
        reasons = list(moving.get("趋衰", []))
        bian_zhi = getattr(line, "bian_di_zhi", None)
        if bian_zhi:
            if LIU_CHONG.get(self.day_zhi) == bian_zhi:
                reasons.append("变爻逢日冲破")
            if LIU_CHONG.get(self.month_zhi) == bian_zhi:
                reasons.append("变爻逢月冲破")
        return list(dict.fromkeys(reasons))

    def competitive_opponent_candidates(self) -> List[Dict[str, Any]]:
        """识别短期竞争卦中可能代表竞争者且发动失势的间爻。"""
        if not self.is_competitive_selection or not self.shi_line:
            return []

        candidates = []
        shi_wx = DI_ZHI_WU_XING.get(self.shi_line.di_zhi)
        for line in self.hexagram.lines:
            if not line.is_moving:
                continue
            if line.position not in self.intervening_positions:
                continue
            decline_reasons = self.moving_decline_reasons(line)
            if not decline_reasons:
                continue

            role_reasons = []
            if line.liu_qin == self.shi_line.liu_qin:
                role_reasons.append("与世爻六亲同类相争")
            if line.wu_xing == shi_wx:
                role_reasons.append("与世爻五行同类相争")
            if LIU_CHONG.get(line.di_zhi) == self.shi_line.di_zhi:
                role_reasons.append("与世爻地支相冲")
            if line.position in self.intervening_positions:
                role_reasons.append("位于世应之间的间爻")
            if not role_reasons:
                continue

            candidates.append({
                "role": "competitor",
                "position": line.position,
                "ben_zhi": line.di_zhi,
                "ben_wu_xing": line.wu_xing,
                "liu_qin": line.liu_qin,
                "bian_zhi": getattr(line, "bian_di_zhi", None),
                "bian_wu_xing": getattr(line, "bian_wu_xing", None),
                "bian_liu_qin": getattr(line, "bian_liu_qin", None),
                "shi_position": self.shi_line.position,
                "shi_zhi": self.shi_line.di_zhi,
                "decline_reasons": decline_reasons,
                "role_reasons": role_reasons,
                "moving": self.moving_analyses.get(line.position, {}),
            })
        return candidates
