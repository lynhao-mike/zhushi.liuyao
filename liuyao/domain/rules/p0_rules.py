"""
P0 吉凶规则

本模块优先承接 KNOWN_MISMATCH 中明确的 B 类高优先级缺口:
- 废爻型(月破+日克)
- 月令时效卦
- 三合局优先
- 世/用自变回头克等内力终局
- 用神动化回头生救

注意: 部分《增删卜易》fixture 的 ``yao_types`` 尚标 FIXME, 当前规则只采用
引擎已经构造出的卦象事实进行保守判定, 不用案例编号硬编码结论。
"""

from liuyao.domain.data import DI_ZHI_WU_XING, LIU_CHONG, LIU_HE, SAN_HE, WU_XING_KE, WU_XING_SHENG

from .result import RuleResult


class BaseRule:
    rule_id = "base"
    theory_id = ""
    priority = 0

    def result(self, pattern, ji_xiong, explanation, evidence=None, stop=True):
        return RuleResult(
            matched=True,
            priority=self.priority,
            pattern=pattern,
            ji_xiong=ji_xiong,
            explanation=explanation,
            stop=stop,
            rule_id=self.rule_id,
            theory_id=self.theory_id,
            evidence=evidence or [],
        )


def _has_riyue_support(line_zhi, month_zhi, day_zhi):
    """日月双支均对爻有扶助或六合, 用于识别旺相式金刚型。"""
    line_wx = DI_ZHI_WU_XING[line_zhi]

    def supports(zhi):
        wx = DI_ZHI_WU_XING[zhi]
        return (
            wx == line_wx
            or WU_XING_SHENG.get(wx) == line_wx
            or LIU_HE.get(zhi, (None, None))[0] == line_zhi
        )

    return supports(month_zhi) and supports(day_zhi)


class FeiYaoRiyueRule(BaseRule):
    """废爻型: 月破 + 日克, 高优先级定衰败。"""

    rule_id = "P0_FEI_YAO_RIYUE"
    theory_id = "特殊日月组合_废爻型"
    priority = 1000

    def evaluate(self, ctx):
        line = ctx.primary_yong
        if not line:
            return None
        ws = ctx.wangshuai_of(line)
        if "月破" in ws.get("month_shuai", []) and "日令克" in ws.get("day_shuai", []):
            return self.result(
                "废爻型(月破日克)",
                "凶",
                f"用神{line.di_zhi}{line.wu_xing}月破又受日令克, 属废爻型; 普通动生难以救起, 凶",
                evidence=[{"position": line.position, "month_shuai": ws.get("month_shuai", []), "day_shuai": ws.get("day_shuai", [])}],
            )
        return None


class YueLingShixiaoRule(BaseRule):
    """月令时效卦: 动爻临月/化出月令或合月, 短事不以普通回头克直接断凶。"""

    rule_id = "P0_YUE_LING_SHIXIAO"
    theory_id = "时效卦_月令时效"
    priority = 950

    def evaluate(self, ctx):
        line = ctx.primary_yong
        if not line or not line.is_moving:
            return None
        moving = ctx.moving_analyses.get(line.position, {})
        bian_zhi = getattr(line, "bian_di_zhi", None)
        he_month = LIU_HE.get(ctx.month_zhi, (None, None))[0]
        line_hits_month = line.di_zhi == ctx.month_zhi
        bian_hits_month = bian_zhi == ctx.month_zhi or bian_zhi == he_month
        # P0 阶段只落地《增删》例9这类“世用合一且用神自发动”的月令时效卦。
        # 若放宽到所有临月动爻, 会误伤例11等“忌神/月建入动克用”的既有基线。
        is_shi_yong_self_moving = bool(getattr(line, "is_shi", False))
        if is_shi_yong_self_moving and (
            line_hits_month or bian_hits_month or "化出临日月" in moving.get("趋旺", [])
        ):
            return self.result(
                "月令时效卦",
                "吉",
                f"世用{line.di_zhi}发动并临月/化出月令气, 属月令时效卦; 短期事不按普通受克衰败断, 以得令为吉",
                evidence=[{"position": line.position, "ben_zhi": line.di_zhi, "bian_zhi": bian_zhi, "month_zhi": ctx.month_zhi}],
            )
        return None


class SanHeJuPriorityRule(BaseRule):
    """三合局优先于单爻分析。"""

    rule_id = "P0_SAN_HE_JU_PRIORITY"
    theory_id = "三合局优先"
    priority = 900

    def evaluate(self, ctx):
        if not ctx.primary_yong:
            return None
        yong_wx = DI_ZHI_WU_XING[ctx.primary_yong.di_zhi]
        shi_wx = DI_ZHI_WU_XING[ctx.shi_line.di_zhi] if ctx.shi_line else ""
        for ju in self._candidate_ju(ctx):
            ju_wx = ju.get("wu_xing")
            if not ju_wx:
                continue
            if WU_XING_KE.get(ju_wx) == yong_wx:
                return self.result(
                    "三合局克用神",
                    "凶",
                    f"动爻会成三合{ju_wx}局, 合局整体克用神{ctx.primary_yong.di_zhi}{yong_wx}; 三合局优先于单爻, 凶",
                    evidence=[ju],
                )
            # P0 阶段只把“合局生世”作为可覆盖单爻克害的吉断终局。
            # “生用神”在出行/行人等事类中可能只是细节或应期信息, 不能泛化为吉凶终局,
            # 否则会把例23这类既有基线误判为吉。
            if shi_wx and WU_XING_SHENG.get(ju_wx) == shi_wx:
                return self.result(
                    "三合局生世",
                    "吉",
                    f"动爻会成三合{ju_wx}局, 合局整体生世爻{ctx.shi_line.di_zhi}{shi_wx}; 三合局优先于单爻, 吉",
                    evidence=[ju],
                )
        return None

    def _candidate_ju(self, ctx):
        """返回完整动爻三合局, 并补充“动爻+变爻”形成的三合局。"""
        candidates = list(ctx.san_he_ju or [])
        seen = {(ju.get("wu_xing"), tuple(sorted(ju.get("members", [])))) for ju in candidates}

        moving_lines = [line for line in ctx.hexagram.lines if line.is_moving]
        if len(moving_lines) < 2:
            return candidates

        zhi_positions = {}
        for line in moving_lines:
            zhi_positions.setdefault(line.di_zhi, set()).add(line.position)
            bian_zhi = getattr(line, "bian_di_zhi", None)
            if bian_zhi:
                zhi_positions.setdefault(bian_zhi, set()).add(line.position)

        for wx, members in SAN_HE.items():
            if not all(member in zhi_positions for member in members):
                continue
            positions = sorted({pos for member in members for pos in zhi_positions[member]})
            if len(positions) < 2:
                continue
            key = (wx, tuple(sorted(members)))
            if key in seen:
                continue
            candidates.append({
                "wu_xing": wx,
                "members": list(members),
                "positions": positions,
                "source": "moving_and_transformed_lines",
            })
            seen.add(key)
        return candidates


class JingangMovingKeShiRule(BaseRule):
    """金刚型动爻虽化回头克, 吉凶层面仍可克世。"""

    rule_id = "P0_JINGANG_MOVING_KE_SHI"
    theory_id = "特殊日月组合_金刚型"
    priority = 875

    def evaluate(self, ctx):
        if not ctx.shi_line or ctx.question_type == "shouming":
            return None
        shi_wx = DI_ZHI_WU_XING[ctx.shi_line.di_zhi]
        for line in ctx.hexagram.lines:
            if not line.is_moving:
                continue
            if not _has_riyue_support(line.di_zhi, ctx.month_zhi, ctx.day_zhi):
                continue
            if WU_XING_KE.get(line.wu_xing) != shi_wx:
                continue
            return self.result(
                "金刚型忌神动克世",
                "凶",
                f"动爻{line.di_zhi}{line.wu_xing}得月日双扶成金刚型, 虽化回头克亦不废其吉凶作用, 动克世爻{ctx.shi_line.di_zhi}{shi_wx}, 凶",
                evidence=[{
                    "position": line.position,
                    "ben_zhi": line.di_zhi,
                    "bian_zhi": getattr(line, "bian_di_zhi", None),
                    "shi_position": ctx.shi_line.position,
                    "shi_zhi": ctx.shi_line.di_zhi,
                    "month_zhi": ctx.month_zhi,
                    "day_zhi": ctx.day_zhi,
                }],
            )
        return None


class SelfChangeTerminalRule(BaseRule):
    """世爻/用神自身发动化衰, 内力终局优先。"""

    rule_id = "P0_SELF_CHANGE_TERMINAL"
    theory_id = "内重外轻"
    priority = 850

    def evaluate(self, ctx):
        for label, line in (("用神", ctx.primary_yong), ("世爻", ctx.shi_line)):
            if not line:
                continue
            moving = ctx.moving_analyses.get(line.position)
            if moving and moving.get("趋衰"):
                return self.result(
                    "内力动化衰败",
                    "凶",
                    f"{label}{line.di_zhi}自身发动化{','.join(moving['趋衰'])}, 内力终点主导吉凶, 凶",
                    evidence=[{"position": line.position, "moving": moving}],
                )
        return None


class InvestmentWealthTurnsGhostRiskRule(BaseRule):
    """投资求财: 世财发动化官鬼, 财旺不直接作可投吉断。"""

    rule_id = "P1_INVESTMENT_WEALTH_TURNS_GHOST_RISK"
    theory_id = "反馈迭代_投资风控_财动化鬼"
    priority = 845

    def evaluate(self, ctx):
        if ctx.question_type not in ("cai", "shengyi"):
            return None
        if ctx.yong_shen_liu_qin != "妻财" or not ctx.shi_line:
            return None
        line = ctx.shi_line
        if not line.is_moving or line.liu_qin != "妻财" or getattr(line, "bian_liu_qin", None) != "官鬼":
            return None

        risk_signals = ["世财发动化官鬼"]
        for other in ctx.yong_lines:
            if other.position == line.position:
                continue
            if LIU_CHONG.get(other.di_zhi) == line.di_zhi:
                risk_signals.append("财爻相冲")
                break
        if getattr(ctx.hexagram, "ben_gua_type", "") == "游魂":
            risk_signals.append("游魂卦心态反复")

        explanation = (
            f"投资求财卦中第{line.position}爻世财{line.di_zhi}{line.wu_xing}发动化官鬼"
            f"{getattr(line, 'bian_di_zhi', '')}, 财旺代表看见机会, 但财化鬼主风险、压力与亏损隐患; "
            "不宜把用旺世兴直接断为可重仓获利, 应以风控和避险为先"
        )
        evidence = [{
            "position": line.position,
            "ben_zhi": line.di_zhi,
            "ben_wu_xing": line.wu_xing,
            "bian_zhi": getattr(line, "bian_di_zhi", None),
            "bian_liu_qin": getattr(line, "bian_liu_qin", None),
            "shi_position": line.position,
            "shi_zhi": line.di_zhi,
            "risk_signals": risk_signals,
            "decision_path": "investment_risk_control",
            "counter_signals": ["财旺持世只代表机会与入场意愿, 不等于稳健获利"],
        }]
        return self.result(
            "财动化鬼风控",
            "凶",
            explanation,
            evidence=evidence,
        )


class CompetitiveSelectionOpponentFailsRule(BaseRule):
    """短期差额选拔: 间爻竞争者发动化衰, 竞争者自败则世可胜出。"""

    rule_id = "P1_COMPETITIVE_SELECTION_OPPONENT_FAILS"
    theory_id = "反馈迭代_竞争选拔_竞争者自败"
    priority = 840

    def evaluate(self, ctx):
        if not ctx.is_competitive_selection or not ctx.shi_line:
            return None
        candidates = ctx.competitive_opponent_candidates()
        if not candidates:
            return None

        candidate = candidates[0]
        decline = "、".join(candidate.get("decline_reasons", []))
        role = "、".join(candidate.get("role_reasons", []))
        explanation = (
            f"{ctx.question_type}属于短期竞争/差额选拔类占问, "
            f"第{candidate['position']}爻{candidate['ben_zhi']}{candidate['ben_wu_xing']}"
            f"位居世应之间, 可作竞争者/阻隔之象; "
            f"其发动化{candidate.get('bian_zhi') or ''}, 见{decline}, 竞争者自败; "
            f"世爻{candidate['shi_zhi']}虽受压力, 但因对手失势而有脱颖而出之机, 吉"
        )
        evidence = [{
            **candidate,
            "selection_context": ctx.question_type,
            "pattern_basis": role,
            "decision_path": "competitive_selection_review",
            "confidence": "medium_high",
            "counter_signals": ["世爻受月令克体现压力/难度, 不作终局凶断"],
        }]
        return self.result(
            "竞争者化破",
            "吉",
            explanation,
            evidence=evidence,
        )


class HuiTouShengRescueRule(BaseRule):
    """用神动化回头生, 动兆主导。"""

    rule_id = "P0_HUI_TOU_SHENG_RESCUE"
    theory_id = "动兆胜日月"
    priority = 800

    def evaluate(self, ctx):
        line = ctx.primary_yong
        if not line or not line.is_moving:
            return None
        moving = ctx.moving_analyses.get(line.position, {})
        if "回头生" in moving.get("趋旺", []):
            return self.result(
                "用神动化回头生",
                "吉",
                f"用神{line.di_zhi}{line.wu_xing}发动化回头生, 动兆为主, 可胜普通日月克, 吉",
                evidence=[{"position": line.position, "moving": moving}],
            )
        return None


class DayMonthKeMovingRescueRule(BaseRule):
    """日月皆克用神时, 用神自身有效发动可救。"""

    rule_id = "P0_DAY_MONTH_KE_MOVING_RESCUE"
    theory_id = "动兆胜日月"
    priority = 825

    def evaluate(self, ctx):
        line = ctx.primary_yong
        if not line or not line.is_moving:
            return None
        moving = ctx.moving_analyses.get(line.position, {})
        if moving.get("趋衰") or moving.get("is_useless"):
            return None
        ws = ctx.wangshuai_of(line)
        day_month_both_ke = "月令克" in ws.get("month_shuai", []) and "日令克" in ws.get("day_shuai", [])
        if day_month_both_ke:
            return self.result(
                "用神动兆胜日月克",
                "吉",
                f"用神{line.di_zhi}{line.wu_xing}虽受月日同克, 但自身发动且未化衰, 动兆主导吉凶, 吉",
                evidence=[{"position": line.position, "wangshuai": ws, "moving": moving}],
            )
        return None


class MovingKeYongRule(BaseRule):
    """有用动爻克用神, 可覆盖普通用旺世兴。"""

    rule_id = "P0_MOVING_KE_YONG"
    theory_id = "真绊假绊"
    priority = 775

    def evaluate(self, ctx):
        line = ctx.primary_yong
        if not line:
            return None
        interaction = ctx.dongbian_results.get("interactions", {}).get(line.position, {"受生": [], "受克": []})
        if interaction.get("受克"):
            return self.result(
                "忌神动克用神",
                "凶",
                f"用神{line.di_zhi}{line.wu_xing}受有用动爻克({', '.join(interaction['受克'])}), 吉凶层面照常论克, 凶",
                evidence=[{"position": line.position, "interaction": interaction}],
            )
        return None


class TransformedYongMediatorRule(BaseRule):
    """变爻为用神, 通过动爻为媒间接生世。"""

    rule_id = "P0_TRANSFORMED_YONG_MEDIATOR"
    theory_id = "变爻用神"
    priority = 760

    def evaluate(self, ctx):
        if not ctx.shi_line:
            return None
        shi_wx = DI_ZHI_WU_XING[ctx.shi_line.di_zhi]
        for line in ctx.hexagram.lines:
            if not line.is_moving or not getattr(line, "bian_liu_qin", None):
                continue
            if line.bian_liu_qin != ctx.yong_shen_liu_qin:
                continue
            bian_wx = line.bian_wu_xing or DI_ZHI_WU_XING.get(line.bian_di_zhi)
            if not bian_wx:
                continue
            # 落地两类已经原书核实的窄规则:
            #   例2: 变爻用神(寅木) -> 生动爻媒介(巳火) -> 生世爻(未土)
            #   例41: 世爻自身动化用神回头生, 变爻用神为中转站, 假化散不废
            # 不泛化为任意"动化用神"均吉, 避免覆盖鬼用互化/世化忌等凶格。
            is_shi_self_huitou_sheng = line.position == ctx.shi_line.position and WU_XING_SHENG.get(bian_wx) == shi_wx
            is_mediator_chain = WU_XING_SHENG.get(bian_wx) == line.wu_xing and WU_XING_SHENG.get(line.wu_xing) == shi_wx
            if not (is_shi_self_huitou_sheng or is_mediator_chain):
                continue
            if is_shi_self_huitou_sheng:
                explanation = (
                    f"世爻{line.di_zhi}{line.wu_xing}发动化出用神{line.bian_di_zhi}{bian_wx}回头生, "
                    "变爻用神为回头生能量中转站, 即使逢破散亦不废其吉凶作用, 用神生世, 吉"
                )
            else:
                explanation = (
                    f"动爻{line.di_zhi}{line.wu_xing}化出用神{line.bian_di_zhi}{bian_wx}, "
                    f"变爻用神先生动爻为媒, 动爻再生世爻{ctx.shi_line.di_zhi}{shi_wx}, 用神生世, 吉"
                )
            return self.result(
                "变爻用神生世",
                "吉",
                explanation,
                evidence=[{
                    "position": line.position,
                    "ben_zhi": line.di_zhi,
                    "ben_wu_xing": line.wu_xing,
                    "bian_zhi": line.bian_di_zhi,
                    "bian_wu_xing": bian_wx,
                    "shi_position": ctx.shi_line.position,
                    "shi_zhi": ctx.shi_line.di_zhi,
                }],
            )
        return None


P0_RULES = [
    FeiYaoRiyueRule(),
    YueLingShixiaoRule(),
    SanHeJuPriorityRule(),
    JingangMovingKeShiRule(),
    SelfChangeTerminalRule(),
    InvestmentWealthTurnsGhostRiskRule(),
    CompetitiveSelectionOpponentFailsRule(),
    DayMonthKeMovingRescueRule(),
    HuiTouShengRescueRule(),
    MovingKeYongRule(),
    TransformedYongMediatorRule(),
]
