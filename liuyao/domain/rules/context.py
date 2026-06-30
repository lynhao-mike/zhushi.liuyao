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
    def is_designated_target_case(self) -> bool:
        """是否属于双核卦象最小落地范围: 特指/嫁接/指定对象成败。"""
        return self.question_type in {
            "kaoshi", "guan", "shengyi", "cai", "hun_male", "hun_female",
            "xingren", "xingren_gui", "other"
        }

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
    def compound_movement(self) -> List[Dict[str, Any]]:
        return self.dongbian_results.get("compound_movement", [])

    def final_compound_movement(self) -> Dict[str, Any]:
        for item in self.compound_movement:
            if item.get("mode") == "san_he" and item.get("valid"):
                return item
        for item in self.compound_movement:
            if item.get("valid"):
                return item
        return {}

    def compound_final_target_position(self) -> int | None:
        item = self.final_compound_movement()
        return item.get("final_target_position") if item else None

    def compound_final_target_kind(self) -> str:
        item = self.final_compound_movement()
        return item.get("final_target_kind", "unknown") if item else "unknown"

    def compound_acts_on_target(self) -> str:
        item = self.final_compound_movement()
        return item.get("acts_on_target", "none") if item else "none"

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

    @property
    def primary_yong_moving(self) -> Dict[str, Any]:
        """用神动变分析结果（常用访问器，减少规则内重复拆包）。"""
        if not self.primary_yong:
            return {}
        return self.moving_analyses.get(self.primary_yong.position, {})

    @property
    def primary_yong_wangshuai(self) -> Dict[str, Any]:
        """用神旺衰分析结果（常用访问器，减少规则内重复拆包）。"""
        if not self.primary_yong:
            return {}
        return self.wangshuai_of(self.primary_yong)

    def yong_interaction(self) -> Dict[str, List[str]]:
        """用神受动爻生克情况（常用访问器，减少规则内重复拆包）。"""
        if not self.primary_yong:
            return {"受生": [], "受克": []}
        return self.dongbian_results.get("interactions", {}).get(
            self.primary_yong.position, {"受生": [], "受克": []}
        )

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

    def special_day_month_combo(self, line: Any) -> Dict[str, Any]:
        """返回最小特殊日月组合分类，供 P0/P1 规则统一消费。"""
        ws = self.wangshuai_of(line)
        month_wang = ws.get("month_wang", [])
        month_shuai = ws.get("month_shuai", [])
        day_wang = ws.get("day_wang", [])
        day_shuai = ws.get("day_shuai", [])

        is_feiyao = "月破" in month_shuai and "日令克" in day_shuai
        is_jingang = bool(month_wang) and bool(day_wang) and (
            any(x in month_wang for x in ("临月令", "月令合", "月令生", "月令扶"))
            and any(x in day_wang for x in ("临日建", "日令合", "日令生", "日令扶", "临日令长生", "临日令帝旺"))
        )
        excludes_month_chong_day_chong = "月破" in month_shuai and "日令克" not in day_shuai
        return {
            "is_feiyao": is_feiyao,
            "is_jingang": is_jingang,
            "excludes_month_chong_day_chong": excludes_month_chong_day_chong,
            "wangshuai": ws,
        }

    def shixiao_context(self, line: Any | None = None) -> Dict[str, Any]:
        """统一时效卦分类：月令时效 / 日令时效 / 终身时效。"""
        target = line or self.primary_yong
        moving = self.primary_yong_moving if target is self.primary_yong else self.moving_analyses.get(getattr(target, "position", 0), {})
        bian_zhi = getattr(target, "bian_di_zhi", None) if target else None
        he_month = LIU_CHONG.get(self.month_zhi)
        line_hits_month = bool(target and getattr(target, "di_zhi", None) == self.month_zhi)
        line_hits_day = bool(target and getattr(target, "di_zhi", None) == self.day_zhi)
        bian_hits_month = bian_zhi == self.month_zhi
        bian_hits_day = bian_zhi == self.day_zhi

        is_month_window = self.question_type in {"guan", "kaoshi", "cai", "shengyi", "bing", "other"}
        is_day_window = self.question_type in {"dangri", "mashang", "jinshi", "chuxing", "xingren", "xingren_gui"}
        is_lifetime = self.question_type in {"zhongshen_gongming", "zhongshen_caifu", "zhongshen_yunshi"}

        return {
            "is_month_shixiao": bool(target and getattr(target, "is_moving", False) and is_month_window and (line_hits_month or bian_hits_month or "化出临日月" in moving.get("趋旺", []))),
            "is_day_shixiao": bool(target and is_day_window and (line_hits_day or bian_hits_day)),
            "is_lifetime_shixiao": is_lifetime,
            "line_hits_month": line_hits_month,
            "line_hits_day": line_hits_day,
            "bian_hits_month": bian_hits_month,
            "bian_hits_day": bian_hits_day,
            "moving": moving,
            "wangshuai": self.wangshuai_of(target) if target else {},
        }

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
