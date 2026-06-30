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


class FeiYaoRiyueRule(BaseRule):
    """废爻型: 月破 + 日克, 高优先级定衰败。"""

    rule_id = "P0_FEI_YAO_RIYUE"
    theory_id = "特殊日月组合_废爻型"
    priority = 1000

    def evaluate(self, ctx):
        line = ctx.primary_yong
        if not line:
            return None
        combo = ctx.special_day_month_combo(line)
        if combo["is_feiyao"]:
            ws = combo["wangshuai"]
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
        shixiao = ctx.shixiao_context(line)
        # P0 阶段仍保守: 只落地“世用合一且用神自发动”的月令时效卦。
        is_shi_yong_self_moving = bool(getattr(line, "is_shi", False))
        if is_shi_yong_self_moving and shixiao["is_month_shixiao"]:
            return self.result(
                "月令时效卦",
                "吉",
                f"世用{line.di_zhi}发动并临月/化出月令气, 属月令时效卦; 短期事不按普通受克衰败断, 以得令为吉",
                evidence=[{"position": line.position, "ben_zhi": line.di_zhi, "bian_zhi": getattr(line, 'bian_di_zhi', None), "month_zhi": ctx.month_zhi, "shixiao": shixiao}],
            )
        return None


class RiLingShixiaoRule(BaseRule):
    """日令时效卦: 当日/短期内完结之事, 用神临日或化出日令时, 不按普通受克直断。"""

    rule_id = "P0_RI_LING_SHIXIAO"
    theory_id = "时效卦_日令时效"
    priority = 945

    def evaluate(self, ctx):
        line = ctx.primary_yong
        if not line:
            return None
        shixiao = ctx.shixiao_context(line)
        if not shixiao["is_day_shixiao"]:
            return None
        return self.result(
            "日令时效卦",
            "吉",
            f"用神{line.di_zhi}临日令或化出日令, 属日令时效卦; 当日/短期内以日为司令, 不按普通受克衰败直断",
            evidence=[{
                "position": line.position,
                "ben_zhi": line.di_zhi,
                "bian_zhi": getattr(line, "bian_di_zhi", None),
                "day_zhi": ctx.day_zhi,
                "question_type": ctx.question_type,
                "shixiao": shixiao,
            }],
        )


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

        moving_lines = list(getattr(ctx.hexagram, "moving_lines", []))
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


class CompoundMovementFinalTargetRule(BaseRule):
    """复合之动最终目标爻规则: 只消费统一结构，不在规则层重复拼链。"""

    rule_id = "P0_COMPOUND_MOVEMENT_FINAL_TARGET"
    theory_id = "复合之动_最终目标爻"
    priority = 890

    def evaluate(self, ctx):
        item = ctx.final_compound_movement()
        if not item:
            return None
        if item.get("mode") == "san_he":
            return None
        if len(item.get("path", [])) < 3:
            return None  # ponytail: 只吃真正二跳复合动，避免误伤普通单爻/回头生案例; 升级: 当反馈样本中出现三跳复合动误杀案例时放宽至 >=2
        if ctx.shixiao_context().get("is_day_shixiao") or ctx.shixiao_context().get("is_month_shixiao"):
            return None
        if ctx.primary_yong_moving.get("趋衰"):
            return None
        combo = ctx.special_day_month_combo(ctx.primary_yong) if ctx.primary_yong else {}
        if combo.get("is_feiyao") or combo.get("is_jingang"):
            return None

        acts = ctx.compound_acts_on_target()
        target_kind = ctx.compound_final_target_kind()
        if acts == "sheng":
            if target_kind in {"shi", "shi_yong"}:
                return self.result(
                    "复合动生世",
                    "吉",
                    f"复合动路径{item.get('path')}聚力后生世爻, 按复合之动整体论吉",
                    evidence=[item],
                )
            if target_kind == "yong":
                return self.result(
                    "复合动生用",
                    "吉",
                    f"复合动路径{item.get('path')}聚力后生用神, 按复合之动整体论吉",
                    evidence=[item],
                )
        if acts == "block":
            if target_kind == "yong":
                return self.result(
                    "复合动阻断用神",
                    "凶",
                    f"复合动路径{item.get('path')}整体阻断用神, 按复合之动整体论凶",
                    evidence=[item],
                )
        return None


class KeShiChongBreaksGangjingRule(BaseRule):
    """克中带冲突破金刚型: 特殊日月组合不忌外克, 但冲克合一可突破。"""

    rule_id = "P1_KESHICHONG_BREAKS_GANGJING"
    theory_id = "特殊日月组合_克中带冲突破"
    priority = 870  # 略低于纯金刚型(875), 高于内重外轻(850)

    def evaluate(self, ctx):
        if not ctx.shi_line or ctx.question_type == "shouming":
            return None
        shi_wx = DI_ZHI_WU_XING[ctx.shi_line.di_zhi]
        for line in getattr(ctx.hexagram, "moving_lines", ()):
            # 条件: 动爻五行克世爻 且 地支冲世爻 = 克中带冲
            if WU_XING_KE.get(line.wu_xing) != shi_wx:
                continue
            if LIU_CHONG.get(line.di_zhi) != ctx.shi_line.di_zhi:
                continue
            return self.result(
                "忌神动克冲世爻",
                "凶",
                f"动爻{line.di_zhi}{line.wu_xing}克中带冲世爻{ctx.shi_line.di_zhi}{shi_wx}, "
                f"冲克合一可突破特殊日月组合保护, 世爻受重创, 凶",
                evidence=[{
                    "position": line.position,
                    "ben_zhi": line.di_zhi,
                    "ben_wx": line.wu_xing,
                    "shi_position": ctx.shi_line.position,
                    "shi_zhi": ctx.shi_line.di_zhi,
                    "shi_wx": shi_wx,
                    "ke": True,
                    "chong": True,
                }],
            )
        return None


class JingangMovingKeShiRule(BaseRule):
    """金刚型动爻虽化回头克, 吉凶层面仍可克世。"""

    rule_id = "P0_JINGANG_MOVING_KE_SHI"
    theory_id = "特殊日月组合_金刚型"
    priority = 875

    def evaluate(self, ctx):
        if not ctx.shi_line or ctx.question_type == "shouming":
            return None
        shi_wx = DI_ZHI_WU_XING[ctx.shi_line.di_zhi]
        for line in getattr(ctx.hexagram, "moving_lines", ()):
            combo = ctx.special_day_month_combo(line)
            if not combo["is_jingang"]:
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
                    "combo": combo,
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
            # 用神直接用新访问器；世爻仍用 moving_analyses（非 primary_yong）
            moving = ctx.primary_yong_moving if label == "用神" else ctx.moving_analyses.get(line.position)
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
    priority = 745  # ponytail: P1规则统一低于所有P0规则(最低775)，修复命名与数值不自洽; 升级: P0/P1 优先级体系整体重构时归一化为连续区间

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


class ZaizhanSimplifiedRule(BaseRule):
    """再占卦简化分析: 信息粗放, 动爻变废/化绝/化破等细化信息不应作为终局定性。"""

    rule_id = "P1_ZAIZHAN_SIMPLIFIED"
    theory_id = "再占卦_粗放分析"
    priority = 760  # 低于内重外轻(850), 高于普通P1

    def evaluate(self, ctx):
        if ctx.question_type != "zaizhan":
            return None
        if not ctx.primary_yong or not ctx.shi_line:
            return None
        for line in getattr(ctx.hexagram, "moving_lines", ()):
            moving = ctx.moving_analyses.get(line.position, {})
            if moving.get("is_useless"):
                return self.result(
                    "再占卦(动爻变废不作用终局)",
                    "平",
                    f"再占卦第{line.position}爻虽化{moving.get('useless_reason','')}, "
                    f"但再占卦信息粗放, 此类细化细节不直接作为终局定性, 综合前后卦判断",
                )
        return None


class ShortTermNoJinTuiRule(BaseRule):
    """短近事占无化进化退: 问短事(数日内), 化进化退不应用作吉凶终局定性。"""

    rule_id = "P1_SHORT_TERM_NO_JIN_TUI"
    theory_id = "短占无进退_化进退不作终局"
    priority = 765  # 高于普通P1, 低于P0终局

    def evaluate(self, ctx):
        if not ctx.shi_line or not ctx.primary_yong:
            return None
        # 仅对短占触发(数日内见分晓的事)
        if ctx.question_type not in ("jinshi","dangri","mashang"):
            return None
        for line in getattr(ctx.hexagram, "moving_lines", ()):
            ma = ctx.moving_analyses.get(line.position, {})
            if "化退神" in ma.get("趋衰", []):
                return self.result(
                    "短占化退神(假退)",
                    "平",
                    f"占短事第{line.position}爻{line.di_zhi}化退神; 短占无进退, 化退在此只表过程不表终局",
                )
        return None


class LifetimeShixiaoRule(BaseRule):
    """终身时效卦: 明确终身问事中，持世六亲上升为吉凶核心。"""

    rule_id = "P1_LIFETIME_SHIXIAO"
    theory_id = "终身时效卦_持世主导"
    priority = 755  # 低于P0硬规则，高于普通P1卦意规则

    def evaluate(self, ctx):
        shixiao = ctx.shixiao_context()
        if not shixiao["is_lifetime_shixiao"]:
            return None
        if not ctx.shi_line:
            return None

        shi = ctx.shi_line
        if ctx.question_type == "zhongshen_gongming":
            if shi.liu_qin == "官鬼":
                return self._lifetime_result(ctx, shi, "吉", "官鬼持世", "问终身功名, 官鬼持世为最终有功名之象")
            if shi.liu_qin in ("子孙", "兄弟"):
                return self._lifetime_result(ctx, shi, "凶", f"{shi.liu_qin}持世", "问终身功名, 子孙/兄弟持世主最终与功名无缘或受官运拖累")

        if ctx.question_type == "zhongshen_caifu":
            if shi.liu_qin == "妻财":
                return self._lifetime_result(ctx, shi, "吉", "妻财持世", "问终身财福, 妻财持世为终身有财福着落之象")
            if shi.liu_qin == "兄弟":
                return self._lifetime_result(ctx, shi, "凶", "兄弟持世", "问终身财福, 兄弟持世主财福被耗, 长期不利")

        if ctx.question_type == "zhongshen_yunshi" and ctx.wangshuai_of(shi).get("overall") == "衰":
            return self._lifetime_result(ctx, shi, "凶", "世爻衰败", "问终身运势, 世爻为命根, 衰败则长期不利")
        return None

    def _lifetime_result(self, ctx, shi, ji_xiong, pattern, explanation):
        return self.result(
            f"终身时效卦({pattern})",
            ji_xiong,
            f"{explanation}; 持世信息在终身卦中由细节上升为吉凶核心。",
            evidence=[{
                "shi_position": shi.position,
                "shi_liu_qin": shi.liu_qin,
                "shi_zhi": shi.di_zhi,
                "question_type": ctx.question_type,
                "wangshuai": ctx.wangshuai_of(shi),
            }],
        )


class TravelerReturnRule(BaseRule):
    """占行人归期: 用神化退神=行人归来, 用神化进神=行人外出。"""

    rule_id = "P1_TRAVELER_RETURN"
    theory_id = "行人占_化进化退定归来"
    priority = 730  # ponytail: P1 规则, 低于终身时效卦(755), 避免覆盖P0终局逻辑; 升级: 优先级体系重构时合并为统一的跨域优先级分配表

    def evaluate(self, ctx):
        if ctx.question_type not in ("xingren", "xingren_gui"):
            return None
        line = ctx.primary_yong
        if not line or not line.is_moving:
            return None
        moving = ctx.primary_yong_moving
        cui_tui = moving.get("趋衰", [])
        is_hua_tui = "化退神" in cui_tui
        is_hua_jin = "化进神" in moving.get("趋旺", [])
        if is_hua_tui:
            if ctx.question_type == "xingren_gui":
                return self._return_result(ctx, line, "化退", "行人归来(化退神=近我方)")
        if is_hua_jin:
            if ctx.question_type == "xingren":
                return self._return_result(ctx, line, "化进", "行人外出能行(化进神=离我方)")
        return None

    def _return_result(self, ctx, line, change_type, explanation):
        return self.result(
            f"行人{change_type}神",
            "吉",
            f"问行人, 用神{line.di_zhi}{line.wu_xing}发动化{change_type}神; "
            f"{explanation}。行人占中化进化退非旺衰信号, 而是往来方向信号。",
            evidence=[{
                "position": line.position,
                "ben_zhi": line.di_zhi,
                "ben_liu_qin": line.liu_qin,
                "bian_zhi": getattr(line, "bian_di_zhi", None),
                "change_type": change_type,
                "question_type": ctx.question_type,
            }],
        )


class YongJiMutualTransformRule(BaseRule):
    """用忌互化: 子鬼/父子/财鬼互化的窄规则。"""

    rule_id = "P1_YONG_JI_MUTUAL_TRANSFORM"
    theory_id = "卦意分析法_用忌互化"
    priority = 735  # 低于投资财化鬼专用规则，避免覆盖反馈样本

    # ponytail: 只覆盖问事语境明确的三类互化，不泛化到所有动化; 升级: 新增问事类型且出现对应互化模式未命中时扩展 SCENARIOS 元组
    SCENARIOS = (
        (("shengchan", "zinv"), "子孙", "官鬼", "子鬼互化", "问孕育/子女遇子孙与官鬼互化, 主子息受鬼气牵缠, 凶"),
        (("kaoshi", "fumu", "zinv"), "父母", "子孙", "父子互化", "问孩子/文书遇父母与子孙互化, 主子孙有麻烦或文书反复废弃, 凶"),
        (("cai", "shengyi"), "妻财", "官鬼", "财鬼互化", "问财遇妻财与官鬼互化, 主因财招祸、财中藏忧, 凶"),
    )

    def evaluate(self, ctx):
        for line in getattr(ctx.hexagram, "moving_lines", ()):
            if not getattr(line, "bian_liu_qin", None):
                continue
            for qtypes, a, b, pattern, explanation in self.SCENARIOS:
                if ctx.question_type not in qtypes:
                    continue
                if {line.liu_qin, line.bian_liu_qin} != {a, b}:
                    continue
                return self.result(
                    pattern,
                    "凶",
                    f"第{line.position}爻{line.liu_qin}{line.di_zhi}发动化{line.bian_liu_qin}{getattr(line, 'bian_di_zhi', '')}, {explanation}",
                    evidence=[{
                        "position": line.position,
                        "ben_liu_qin": line.liu_qin,
                        "ben_zhi": line.di_zhi,
                        "bian_liu_qin": line.bian_liu_qin,
                        "bian_zhi": getattr(line, "bian_di_zhi", None),
                        "question_type": ctx.question_type,
                    }],
                )
        return None


class YuanShenDuFaBianFeiRule(BaseRule):
    """元神独发变废定凶: 卦中唯一能动生用神的动爻, 自化回头克/化绝则事败。"""

    rule_id = "P1_YUANSHEN_DUFA_BIANFEI"
    theory_id = "反馈迭代_元神独发变废定凶"
    priority = 830

    def evaluate(self, ctx):
        if not ctx.primary_yong or not ctx.shi_line:
            return None
        if ctx.shixiao_context().get("is_day_shixiao"):
            return None  # ponytail: 日令时效卦由日令司令, 不让元神独发变废覆盖当日成败; 升级: 月令时效卦确认需同样保护时合并 check 条件
        movings = list(getattr(ctx.hexagram, "moving_lines", ()))
        if len(movings) != 1:
            return None
        line = movings[0]
        yong_wx = DI_ZHI_WU_XING[ctx.primary_yong.di_zhi]
        if WU_XING_SHENG.get(line.wu_xing) != yong_wx:
            return None
        moving = ctx.moving_analyses.get(line.position, {})
        trend = moving.get("趋衰", [])
        is_hk = "回头克" in trend
        is_hj = "化绝" in trend
        if not (is_hk or is_hj):
            return None
        cause = "回头克" if is_hk else "化绝"
        return self.result(
            f"元神独发变废({cause})",
            "凶",
            f"第{line.position}爻{line.liu_qin}{line.di_zhi}独发化{cause}, "
            f"为唯一能生用神{ctx.primary_yong.di_zhi}{yong_wx}的元神, 源头断绝, 事必败",
            evidence=[{
                "yong_position": ctx.primary_yong.position,
                "yong_zhi": ctx.primary_yong.di_zhi,
                "yong_wx": yong_wx,
                "yong_liu_qin": ctx.primary_yong.liu_qin,
                "yuan_position": line.position,
                "yuan_zhi": line.di_zhi,
                "yuan_wx": line.wu_xing,
                "yuan_liu_qin": line.liu_qin,
                "trend": cause,
            }],
        )


class ExternalOmenBrokenObjectRule(BaseRule):
    """破损外应: 父母白虎旺相主长辈/身体伤灾, 财不现或空亡主破财。"""

    rule_id = "PARENT_BAIHU_WANG_INJURY_AND_FUCAI_XUNKONG_LOSS"
    theory_id = "反馈迭代_破损外应_父母白虎财伏空"
    priority = 842

    def evaluate(self, ctx):
        if ctx.question_type != "external_omen":
            return None

        parent_baihu = None
        for line in getattr(ctx.hexagram, "lines_by_liu_qin", {}).get("父母", ()):
            if line.liu_shen != "白虎":
                continue
            ws = ctx.wangshuai_of(line)
            if ws.get("overall") == "旺" or line.di_zhi == ctx.month_zhi:
                parent_baihu = (line, ws)
                break
        if not parent_baihu:
            return None

        line, ws = parent_baihu
        wealth_lines = list(getattr(ctx.hexagram, "lines_by_liu_qin", {}).get("妻财", ()))
        wealth_signals = []
        for wealth in wealth_lines:
            if wealth.is_xun_kong:
                wealth_signals.append("财爻旬空")
            if LIU_CHONG.get(ctx.month_zhi) == wealth.di_zhi:
                wealth_signals.append("财爻逢月冲")
            if LIU_CHONG.get(ctx.day_zhi) == wealth.di_zhi:
                wealth_signals.append("财爻逢日冲")
        if not wealth_lines:
            wealth_signals.append("财爻不现/藏伏")

        if not wealth_signals:
            # 本规则的反馈场景要求“伤灾 + 破财”双信号并见，避免泛化所有外应。
            return None

        moving_ghost_signal = None
        if ctx.shi_line and ctx.shi_line.is_moving and getattr(ctx.shi_line, "bian_liu_qin", None) == "官鬼":
            moving_ghost_signal = "世爻动化官鬼"

        explanation = (
            f"破损外应类占问, 不机械取触发者为用神; 第{line.position}爻父母{line.di_zhi}{line.wu_xing}"
            f"临白虎且旺相, 主长辈、身体、骨伤血光; "
            f"同时见{','.join(dict.fromkeys(wealth_signals))}, 主钱财落空或投资破耗。"
        )
        evidence = [{
            "position": line.position,
            "ben_zhi": line.di_zhi,
            "ben_wu_xing": line.wu_xing,
            "liu_qin": line.liu_qin,
            "liu_shen": line.liu_shen,
            "wangshuai": ws,
            "shi_position": getattr(ctx.shi_line, "position", None),
            "shi_zhi": getattr(ctx.shi_line, "di_zhi", None),
            "wealth_signals": list(dict.fromkeys(wealth_signals)),
            "omen_signals": [signal for signal in ["破损外应", "父母临白虎旺相", moving_ghost_signal] if signal],
            "decision_path": "external_omen_broken_object_review",
            "counter_signals": ["事件触发者不等于应事承受者", "子孙持世动化鬼只作引线, 不覆盖父母白虎与财空信号"],
        }]
        return self.result(
            "父母白虎旺相主长辈伤灾，财伏旬空主破财",
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
            f"世爻{candidate['shi_zhi']}虽受压力, 但因对手失势而有脱颖而出的机会, 吉"
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


class DualCoreDesignatedTargetRule(BaseRule):
    """双核卦象最小规则: 用神可成, 但应爻/指定对象不承接该成局时, 不得直断该特指定向成立。"""

    rule_id = "P1_DUAL_CORE_DESIGNATED_TARGET"
    theory_id = "双核卦象_特指定向最小干预"
    priority = 820

    def evaluate(self, ctx):
        if ctx.question_type not in {"hun_male", "hun_female", "xingren", "xingren_gui"}:
            return None
        if not ctx.is_designated_target_case or not ctx.shi_line:
            return None
        ying = getattr(ctx.hexagram, "ying_line", None)
        if not ying:
            return None
        if not getattr(ying, "is_moving", False):
            return None
        if not ctx.primary_yong:
            return None

        # ponytail: 只做最小双核保护——当应爻自发动且不承接世/用的生合时，不允许把普通成局直接等同于"指定对象成"; 升级: 指定对象占类新增反馈样本且出现误判时放宽生合检测范围至六合
        ying_wx = ying.wu_xing
        shi_wx = ctx.shi_line.wu_xing
        yong_wx = ctx.primary_yong.wu_xing
        links_shi = WU_XING_SHENG.get(ying_wx) == shi_wx or WU_XING_SHENG.get(shi_wx) == ying_wx
        links_yong = WU_XING_SHENG.get(ying_wx) == yong_wx or WU_XING_SHENG.get(yong_wx) == ying_wx
        if links_shi or links_yong:
            return None

        return self.result(
            "双核卦象(指定对象未承局)",
            "平",
            f"应爻第{ying.position}爻{ying.di_zhi}{ying_wx}自发动, 但未与世爻{ctx.shi_line.di_zhi}{shi_wx}或用神{ctx.primary_yong.di_zhi}{yong_wx}形成生合承接; 普通成局不可直接等同于指定对象成立, 需保留分歧",
            evidence=[{
                "ying_position": ying.position,
                "ying_zhi": ying.di_zhi,
                "ying_wu_xing": ying_wx,
                "shi_position": ctx.shi_line.position,
                "shi_zhi": ctx.shi_line.di_zhi,
                "yong_position": ctx.primary_yong.position,
                "yong_zhi": ctx.primary_yong.di_zhi,
                "decision_path": "dual_core_designated_target_minimal_guard",
                "counter_signals": ["普通用旺/用神生世只说明事情可成, 不等于指定对象可成"],
            }],
            stop=False,
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
        moving = ctx.primary_yong_moving  # ponytail: 使用新访问器; 升级: 访问器接口稳定后删除注释
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
        compound = ctx.final_compound_movement()
        if compound and compound.get("valid") and ctx.compound_acts_on_target() == "sheng":
            return None  # ponytail: 复合动已形成有效生世/生用时，让路给复合动规则; 升级: 复合动规则新增判断维度时同步更新此处的让路条件
        interaction = ctx.yong_interaction()  # ponytail: 使用新访问器; 升级: 访问器接口稳定后删除注释
        if interaction.get("受克"):
            return self.result(
                "忌神动克用神",
                "凶",
                f"用神{line.di_zhi}{line.wu_xing}受有用动爻克({', '.join(interaction['受克'])}), 吉凶层面照常论克, 凶",
                evidence=[{"position": line.position, "interaction": interaction}],
            )
        return None


class ZhenBanRule(BaseRule):
    """真绊: 全卦/半卦化绊, 或明确时段出行遇绊, 吉凶层面按有动如无。"""

    rule_id = "P0_ZHEN_BAN"
    theory_id = "真绊假绊"
    priority = 905

    def evaluate(self, ctx):
        san_ban = list(ctx.san_ban or [])
        if not san_ban:
            return None

        moving_lines = list(getattr(ctx.hexagram, "moving_lines", ()))
        moving_positions = [line.position for line in moving_lines]
        moving_count = len(moving_positions)
        hua_ban_positions = {ban["positions"][0] for ban in san_ban if ban.get("ban_type") == "化绊" and ban.get("positions")}
        moving_position_set = set(moving_positions)
        structure_zhen_ban = False
        if moving_count >= 3:
            inner_positions = {1, 2, 3}
            outer_positions = {4, 5, 6}
            structure_zhen_ban = (
                (inner_positions <= moving_position_set and inner_positions <= hua_ban_positions) or
                (outer_positions <= moving_position_set and outer_positions <= hua_ban_positions) or
                (len(moving_position_set) == 6 and moving_position_set <= hua_ban_positions)
            )

        timed_travel_zhen_ban = ctx.question_type in ("xingren", "xingren_gui", "chuxing", "dangri")

        if not (structure_zhen_ban or timed_travel_zhen_ban):
            return None

        reasons = []
        if structure_zhen_ban:
            if {1, 2, 3} <= moving_position_set and {1, 2, 3} <= hua_ban_positions:
                reasons.append("内卦三爻全动化绊")
            if {4, 5, 6} <= moving_position_set and {4, 5, 6} <= hua_ban_positions:
                reasons.append("外卦三爻全动化绊")
            if len(moving_position_set) == 6 and moving_position_set <= hua_ban_positions:
                reasons.append("六爻全动化绊")
        if timed_travel_zhen_ban:
            reasons.append("明确时段出行/行人占遇绊")

        return self.result(
            "真绊",
            "凶",
            f"卦中出现真绊({'; '.join(reasons)}), 动爻有动如无, 计划期限内难以如愿, 凶",
            evidence=[{
                "san_ban": san_ban,
                "moving_positions": moving_positions,
                "hua_ban_positions": sorted(hua_ban_positions),
                "reasons": reasons,
                "question_type": ctx.question_type,
            }],
            stop=True,
        )


class TransformedYongMediatorRule(BaseRule):
    """变爻为用神, 通过动爻为媒间接生世。"""

    rule_id = "P0_TRANSFORMED_YONG_MEDIATOR"
    theory_id = "变爻用神"
    priority = 760

    def evaluate(self, ctx):
        if not ctx.shi_line:
            return None
        shi_wx = DI_ZHI_WU_XING[ctx.shi_line.di_zhi]
        for line in getattr(ctx.hexagram, "moving_lines", ()):
            if not getattr(line, "bian_liu_qin", None):
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
    RiLingShixiaoRule(),
    SanHeJuPriorityRule(),
    CompoundMovementFinalTargetRule(),
    ZhenBanRule(),
    KeShiChongBreaksGangjingRule(),
    JingangMovingKeShiRule(),
    SelfChangeTerminalRule(),
    LifetimeShixiaoRule(),
    InvestmentWealthTurnsGhostRiskRule(),
    ExternalOmenBrokenObjectRule(),
    CompetitiveSelectionOpponentFailsRule(),
    DualCoreDesignatedTargetRule(),
    DayMonthKeMovingRescueRule(),
    HuiTouShengRescueRule(),
    MovingKeYongRule(),
    TransformedYongMediatorRule(),
    ZaizhanSimplifiedRule(),
    ShortTermNoJinTuiRule(),
    TravelerReturnRule(),
    YuanShenDuFaBianFeiRule(),
    YongJiMutualTransformRule(),
]
