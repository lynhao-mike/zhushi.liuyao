"""
吉凶判断模块 - Ji-Xiong (Auspicious/Inauspicious) Judgment Engine

实现卦局通论(Gua Ju Tong Lun), 判断整卦吉凶模式。
包括动卦吉利卦局、动卦凶兆卦局、静卦判断规则及特例处理。
"""

from .data import (
    DI_ZHI_WU_XING,
    WU_XING_SHENG, WU_XING_KE,
)
from .rules import P0_RULES, RuleContext, RuleEngine


# 用神选择表: 问事类型 -> 用神六亲
YONG_SHEN_TABLE = {
    "cai": "妻财",        # 财运
    "guan": "官鬼",       # 官运/工作
    "hun_male": "妻财",   # 婚姻(男问)
    "hun_female": "官鬼", # 婚姻(女问)
    "bing": "官鬼",       # 疾病(官鬼代表病, 子孙代表药)
    "kaoshi": "父母",     # 考试/文书
    "fumu": "父母",       # 显式取父母爻(长辈/文书/土地等)
    "xiongdi": "兄弟",    # 显式取兄弟爻(兄弟姐妹/同辈)
    "zinv": "子孙",       # 子女
    "xingRen": "官鬼",    # 行人(默认, 实际需看关系)
    "youHuan": "子孙",    # 忧患(子孙为喜神)
    "shiwu": "妻财",      # 失物(默认: 妻财 - 贵重财物之价值属性)
    "shefu": "子孙",      # 射覆/经历还原: 默认取子孙作具象、小物、小动物、身体感受入口
    # 《增删卜易》fixture 中使用的通用问事标签。
    # 这些别名让引擎按案例显式题类取用神, 避免回落到 other=官鬼。
    "hun": "妻财",        # 婚姻/婚配(未区分男女时按财爻主婚财)
    "shengyi": "妻财",    # 生意/经营
    "shengchan": "子孙",  # 生产/子息
    "shouming": "父母",   # 寿元/长辈寿命
    "other": "官鬼",      # 其他(默认)
}

# 忌神六亲 (克用神者)
JI_SHEN_TABLE = {
    "妻财": "兄弟",   # 兄弟克妻财
    "官鬼": "子孙",   # 子孙克官鬼
    "父母": "妻财",   # 妻财克父母
    "子孙": "官鬼",   # 官鬼克子孙
    "兄弟": "官鬼",   # 官鬼克兄弟
}

# 双(多)视角用神配置: 问事类型 -> [(用神六亲, 视角标签), ...]
# 仅在某些问事类型存在多个合理用神选择时启用。
# - 失物: 妻财(贵重财物之价值属性, 主视角) + 父母(物件本相, 辅助视角)
# - 疾病: 官鬼(病势消长) + 子孙(药效医疗)
DUAL_PERSPECTIVE_TABLE = {
    "shiwu": [
        ("妻财", "贵重财物视角(物之价值·主视角)"),
        ("父母", "物件本相视角(物之载体·辅助)"),
    ],
    "bing": [
        ("官鬼", "病情视角(病势消长)"),
        ("子孙", "药效视角(医疗成效)"),
    ],
}


def get_dual_perspectives(question_type):
    """
    获取问事类型的双(多)视角用神配置。

    Args:
        question_type: 问事类型

    Returns:
        list of (yong_shen_liu_qin, perspective_label) tuples
        若该类型未配置多视角, 则返回单元素列表(仅默认视角)
    """
    if question_type in DUAL_PERSPECTIVE_TABLE:
        return list(DUAL_PERSPECTIVE_TABLE[question_type])
    return [(determine_yong_shen(question_type), "默认视角")]


def determine_yong_shen(question_type):
    """
    根据问事类型确定用神六亲。

    Args:
        question_type: 问事类型 (cai/guan/hun_male/hun_female/bing/kaoshi/zinv/xingRen/youHuan/other)

    Returns:
        str: 用神六亲名称
    """
    return YONG_SHEN_TABLE.get(question_type, "官鬼")


def find_yong_shen_lines(hexagram, yong_shen_liu_qin):
    """
    在卦中找到用神爻。

    Args:
        hexagram: Hexagram对象
        yong_shen_liu_qin: 用神六亲 (如 "妻财")

    Returns:
        list: 匹配的爻列表
    """
    indexed = getattr(hexagram, "lines_by_liu_qin", None)
    if indexed is not None:
        return list(indexed.get(yong_shen_liu_qin, []))

    return [line for line in hexagram.lines if line.liu_qin == yong_shen_liu_qin]


def find_shi_line(hexagram):
    """找到世爻"""
    indexed = getattr(hexagram, "shi_line", None)
    if indexed is not None:
        return indexed

    for line in hexagram.lines:
        if line.is_shi:
            return line
    return None


def find_ying_line(hexagram):
    """找到应爻"""
    indexed = getattr(hexagram, "ying_line", None)
    if indexed is not None:
        return indexed

    for line in hexagram.lines:
        if line.is_ying:
            return line
    return None


def _line_has_day_month_support(line_zhi, month_zhi, day_zhi):
    """检查爻是否得日月之一扶助(平相)"""
    line_wx = DI_ZHI_WU_XING[line_zhi]
    month_wx = DI_ZHI_WU_XING[month_zhi]
    day_wx = DI_ZHI_WU_XING[day_zhi]

    # 月扶: 同五行或月生
    month_support = (month_wx == line_wx) or (WU_XING_SHENG[month_wx] == line_wx)
    # 日扶: 同五行或日生
    day_support = (day_wx == line_wx) or (WU_XING_SHENG[day_wx] == line_wx)
    # 临月/临日
    month_lin = (line_zhi == month_zhi)
    day_lin = (line_zhi == day_zhi)

    return month_support or day_support or month_lin or day_lin


def judge_dong_gua(hexagram, yong_shen_liu_qin, wangshuai_results, dongbian_results,
                   question_type, patterns_results=None):
    """
    动卦吉凶判断。

    吉利卦局:
    1. 世用受生局: 自占, 用神与世爻重叠, 受动爻生
    2. 用神生世局: 用神为有用动爻, 且生世
    3. 用旺世兴局: 用神旺 + 世至少得日月之一

    凶兆卦局:
    1. 用神衰败局: 用神整体衰
    2. 世爻受伤局: 世受有用动爻克, 或世动化衰
    3. 世用受克局: 用=世, 受克
    4. 用旺世衰局: 用旺但世无日月扶
    5. 用神克世局: 用神动克世

    Returns:
        dict: {"pattern": 卦局名, "ji_xiong": "吉"/"凶"/"平", "explanation": 说明}
    """
    month_zhi = hexagram.gan_zhi["month_zhi"]
    day_zhi = hexagram.gan_zhi["day_zhi"]

    shi_line = find_shi_line(hexagram)
    yong_lines = find_yong_shen_lines(hexagram, yong_shen_liu_qin)

    if not shi_line or not yong_lines:
        return {
            "pattern": "无法判断",
            "ji_xiong": "平",
            "explanation": "未找到用神或世爻",
        }

    # 获取世爻旺衰
    shi_ws = wangshuai_results[shi_line.position - 1]
    shi_has_support = _line_has_day_month_support(shi_line.di_zhi, month_zhi, day_zhi)

    # 获取用神旺衰 (取最旺的一个)
    yong_ws_list = []
    for yl in yong_lines:
        yong_ws_list.append(wangshuai_results[yl.position - 1])

    # 选择主用神: 优先动爻, 其次旺爻
    primary_yong = yong_lines[0]
    primary_yong_ws = yong_ws_list[0]
    for i, yl in enumerate(yong_lines):
        if yl.is_moving:
            primary_yong = yl
            primary_yong_ws = yong_ws_list[i]
            break
        if yong_ws_list[i]["overall"] == "旺":
            primary_yong = yl
            primary_yong_ws = yong_ws_list[i]

    yong_is_wang = primary_yong_ws["overall"] == "旺"
    yong_is_shuai = primary_yong_ws["overall"] == "衰"

    # 用神是否就是世爻
    yong_is_shi = any(yl.position == shi_line.position for yl in yong_lines)

    # 获取动爻交互
    interactions = dongbian_results.get("interactions", {})
    moving_analyses = dongbian_results.get("moving_analyses", {})
    useful_moving = dongbian_results.get("useful_moving", [])

    # 世爻受生/受克情况
    shi_interaction = interactions.get(shi_line.position, {"受生": [], "受克": []})

    # 用神爻受生/受克情况
    yong_interaction = interactions.get(primary_yong.position, {"受生": [], "受克": []})

    # =========================================================================
    # P0 规则管线: 特殊日月组合 / 三合局 / 内力终局 / 动兆优先
    # =========================================================================
    rule_context = RuleContext(
        hexagram=hexagram,
        yong_shen_liu_qin=yong_shen_liu_qin,
        wangshuai_results=wangshuai_results,
        dongbian_results=dongbian_results,
        question_type=question_type,
        patterns_results=patterns_results or {},
        shi_line=shi_line,
        primary_yong=primary_yong,
        yong_lines=yong_lines,
        month_zhi=month_zhi,
        day_zhi=day_zhi,
    )
    rule_result = RuleEngine(P0_RULES).evaluate(rule_context)
    if rule_result:
        return rule_result.to_jixiong()

    # =========================================================================
    # 特例检查 (优先于一般规则)
    # =========================================================================
    special = _check_special_cases(
        hexagram, yong_shen_liu_qin, shi_line, primary_yong,
        wangshuai_results, dongbian_results, question_type,
        month_zhi, day_zhi
    )
    if special:
        return special

    # =========================================================================
    # 按照传统理论优先级判断:
    # 世用受克局 -> 世爻受伤局 -> 世用受生局 -> 用神生世局 ->
    # 用旺世衰局 -> 用神克世局 -> 用旺世兴局 -> 用神衰败局
    # =========================================================================

    yong_wx = DI_ZHI_WU_XING[primary_yong.di_zhi]
    shi_wx = DI_ZHI_WU_XING[shi_line.di_zhi]

    # 1. 世用受克局: 用神与世重叠, 受动爻克 (最严重, 优先判断)
    if yong_is_shi and shi_interaction["受克"]:
        return {
            "pattern": "世用受克局",
            "ji_xiong": "凶",
            "explanation": f"用神持世, 受动爻克({', '.join(shi_interaction['受克'])}), 凶",
        }

    # 2. 世爻受伤局: 世受有用动爻克, 或世动化衰
    shi_hurt = False
    shi_hurt_result = None
    if shi_interaction["受克"]:
        shi_hurt = True
        shi_hurt_result = {
            "pattern": "世爻受伤局",
            "ji_xiong": "凶",
            "explanation": f"世爻受动爻克({', '.join(shi_interaction['受克'])}), 凶",
        }
    elif shi_line.is_moving and shi_line.position in moving_analyses:
        shi_dong = moving_analyses[shi_line.position]
        if shi_dong["趋衰"]:
            shi_hurt = True
            shi_hurt_result = {
                "pattern": "世爻受伤局",
                "ji_xiong": "凶",
                "explanation": f"世爻动化{','.join(shi_dong['趋衰'])}, 凶",
            }

    # If world is hurt, it overrides auspicious patterns (用旺世兴 etc.)
    if shi_hurt:
        return shi_hurt_result

    # 3. 世用受生局: 用神与世重叠, 受有用动爻生
    if yong_is_shi and shi_interaction["受生"]:
        return {
            "pattern": "世用受生局",
            "ji_xiong": "吉",
            "explanation": f"用神持世, 受动爻生({', '.join(shi_interaction['受生'])}), 大吉",
        }

    # 4. 用神生世局: 用神为有用动爻且生世
    if primary_yong.is_moving and primary_yong.position in useful_moving:
        if WU_XING_SHENG[yong_wx] == shi_wx:
            return {
                "pattern": "用神生世局",
                "ji_xiong": "吉",
                "explanation": f"用神{primary_yong.di_zhi}{yong_wx}动而生世爻{shi_line.di_zhi}{shi_wx}, 吉",
            }

    # 5. 用旺世衰局
    if yong_is_wang and not shi_has_support:
        return {
            "pattern": "用旺世衰局",
            "ji_xiong": "凶",
            "explanation": "用神旺但世爻无日月扶助, 事可成但于己不利",
        }

    # 6. 用神克世局
    if primary_yong.is_moving and primary_yong.position in useful_moving:
        if WU_XING_KE[yong_wx] == shi_wx:
            return {
                "pattern": "用神克世局",
                "ji_xiong": "凶",
                "explanation": f"用神{primary_yong.di_zhi}{yong_wx}动克世爻{shi_line.di_zhi}{shi_wx}, 凶",
            }

    # 7. 用旺世兴局
    if yong_is_wang and shi_has_support:
        return {
            "pattern": "用旺世兴局",
            "ji_xiong": "吉",
            "explanation": f"用神旺相, 世爻得日月扶助, 吉",
        }

    # 8. 动兆临日月: 用神发动且变出临日/月, 以动兆得令优先于静态衰败。
    primary_moving = moving_analyses.get(primary_yong.position, {})
    if primary_yong.is_moving and "化出临日月" in primary_moving.get("趋旺", []):
        return {
            "pattern": "用神动化临日月",
            "ji_xiong": "吉",
            "explanation": f"用神{primary_yong.di_zhi}{yong_wx}发动, 变出临日月, 动兆得令为吉",
        }

    # 9. 用神衰败局
    if yong_is_shuai:
        return {
            "pattern": "用神衰败局",
            "ji_xiong": "凶",
            "explanation": f"用神{primary_yong.di_zhi}{yong_wx}衰弱({primary_yong_ws['details']}), 凶",
        }

    # 无明显吉凶模式
    return {
        "pattern": "平局",
        "ji_xiong": "平",
        "explanation": "卦局平和, 无明显吉凶倾向",
    }


def _check_special_cases(hexagram, yong_shen_liu_qin, shi_line, primary_yong,
                         wangshuai_results, dongbian_results, question_type,
                         month_zhi, day_zhi):
    """
    检查特例情况。

    特例:
    - 求财: 财克世(有日月扶)为吉
    - 疾病医药: 子孙克世为吉(药到病除)
    - 行人: 用神克世为吉(人快回)
    - 忧患心态: 子孙克世为吉(忧除)
    """
    yong_wx = DI_ZHI_WU_XING[primary_yong.di_zhi]
    shi_wx = DI_ZHI_WU_XING[shi_line.di_zhi]
    shi_has_support = _line_has_day_month_support(shi_line.di_zhi, month_zhi, day_zhi)
    useful_moving = dongbian_results.get("useful_moving", [])
    moving_analyses = dongbian_results.get("moving_analyses", {})

    # 占寿元与一般求事不同: 用神、元神、忌神发动皆主气数有期。
    # 先落定为凶, 避免因找不到默认官鬼用神或普通用旺规则误判为平/吉。
    if question_type == "shouming" and moving_analyses:
        return {
            "pattern": "占寿元动则有期",
            "ji_xiong": "凶",
            "explanation": "寿元卦不喜动, 卦中发动主气数有期, 凶",
        }

    # 用神/世爻自身发动化衰, 属内力终局, 优先按凶断。
    for line in (primary_yong, shi_line):
        moving = moving_analyses.get(line.position)
        if moving and moving.get("趋衰"):
            return {
                "pattern": "内力动化衰败",
                "ji_xiong": "凶",
                "explanation": f"{'用神' if line is primary_yong else '世爻'}{line.di_zhi}自发动化{','.join(moving['趋衰'])}, 内力主导为凶",
            }

    # 用神动克世的情况
    yong_ke_shi = (primary_yong.is_moving and
                   primary_yong.position in useful_moving and
                   WU_XING_KE[yong_wx] == shi_wx)

    if not yong_ke_shi:
        return None

    # 求财: 财克世, 世有日月扶 -> 吉
    if question_type == "cai" and yong_shen_liu_qin == "妻财":
        if shi_has_support:
            return {
                "pattern": "求财特例(财克世有扶)",
                "ji_xiong": "吉",
                "explanation": "求财卦, 妻财克世但世有日月扶助, 财来就我, 吉",
            }

    # 失物: 用神动克世, 世有日月扶 -> 吉(短期可寻回)
    # 据《知识点总结》: "用神发动克旺相世爻可视为成事之兆,
    # 如占短期失物、短期工作、短期考试等等"
    if question_type == "shiwu" and shi_has_support:
        return {
            "pattern": "失物特例(用克世)",
            "ji_xiong": "吉",
            "explanation": f"失物卦, 用神{primary_yong.di_zhi}动克世但世有日月扶, 短期可寻回",
        }

    # 疾病: 子孙克世 -> 吉(药效)
    if question_type == "bing":
        # 疾病时子孙代表药, 用神是官鬼(代表病)
        # 但如果子孙动克世, 是药到病除
        zi_sun_lines = [l for l in hexagram.lines if l.liu_qin == "子孙"]
        for zs in zi_sun_lines:
            zs_wx = DI_ZHI_WU_XING[zs.di_zhi]
            if zs.is_moving and WU_XING_KE[zs_wx] == shi_wx:
                return {
                    "pattern": "疾病特例(子孙克世)",
                    "ji_xiong": "吉",
                    "explanation": "疾病卦, 子孙(药神)动克世, 药到病除, 吉",
                }

    # 行人: 用神克世 -> 吉(人快回)
    if question_type == "xingRen":
        return {
            "pattern": "行人特例(用克世)",
            "ji_xiong": "吉",
            "explanation": "行人卦, 用神克世, 人即将归来, 吉",
        }

    # 忧患: 子孙克世 -> 吉
    if question_type == "youHuan":
        zi_sun_lines = [l for l in hexagram.lines if l.liu_qin == "子孙"]
        for zs in zi_sun_lines:
            zs_wx = DI_ZHI_WU_XING[zs.di_zhi]
            if zs.is_moving and WU_XING_KE[zs_wx] == shi_wx:
                return {
                    "pattern": "忧患特例(子孙克世)",
                    "ji_xiong": "吉",
                    "explanation": "忧患卦, 子孙(喜神)克世, 忧患可解, 吉",
                }

    return None


def judge_jing_gua(hexagram, yong_shen_liu_qin, wangshuai_results, question_type):
    """
    静卦吉凶判断 (无动爻时)。

    三步判断:
    1. 用忌持世: 用神持世 = 吉(除非无根逢破); 忌神持世 = 凶(有特例)
    2. 用神生克世: 用生世 = 吉; 用克世 = 凶
    3. 用旺世兴: 各自独立分析旺衰

    Returns:
        dict: {"pattern": 卦局名, "ji_xiong": "吉"/"凶"/"平", "explanation": 说明}
    """
    month_zhi = hexagram.gan_zhi["month_zhi"]
    day_zhi = hexagram.gan_zhi["day_zhi"]

    shi_line = find_shi_line(hexagram)
    yong_lines = find_yong_shen_lines(hexagram, yong_shen_liu_qin)
    ji_shen_liu_qin = JI_SHEN_TABLE.get(yong_shen_liu_qin, "")

    if not shi_line or not yong_lines:
        return {
            "pattern": "无法判断",
            "ji_xiong": "平",
            "explanation": "未找到用神或世爻",
        }

    # Step 1: 检查用忌持世
    shi_liu_qin = shi_line.liu_qin
    shi_ws = wangshuai_results[shi_line.position - 1]
    shi_has_support = _line_has_day_month_support(shi_line.di_zhi, month_zhi, day_zhi)

    # 用神持世
    if shi_liu_qin == yong_shen_liu_qin:
        # 检查是否无根(月破)
        is_yue_po = "月破" in shi_ws.get("month_shuai", [])
        if is_yue_po:
            return {
                "pattern": "用神持世逢月破",
                "ji_xiong": "凶",
                "explanation": "用神持世但逢月破, 无根之象, 凶",
            }
        return {
            "pattern": "用神持世",
            "ji_xiong": "吉",
            "explanation": "用神持世, 所求之事与己关系密切, 吉",
        }

    # 忌神持世
    if shi_liu_qin == ji_shen_liu_qin:
        # 检查特例
        if question_type in ("cai", "xingRen", "youHuan"):
            return {
                "pattern": f"忌神持世({question_type}特例)",
                "ji_xiong": "平",
                "explanation": f"忌神持世, 但{question_type}类有特例, 需结合具体分析",
            }
        if question_type == "bing":
            return {
                "pattern": "忌神持世(疾病特例)",
                "ji_xiong": "吉",
                "explanation": "疾病卦忌神(子孙)持世, 子孙为药神, 吉",
            }
        return {
            "pattern": "忌神持世",
            "ji_xiong": "凶",
            "explanation": "忌神持世, 所求之事受阻, 凶",
        }

    # Step 2: 用神与世的生克关系
    primary_yong = yong_lines[0]
    for yl in yong_lines:
        yws = wangshuai_results[yl.position - 1]
        if yws["overall"] == "旺":
            primary_yong = yl
            break

    yong_wx = DI_ZHI_WU_XING[primary_yong.di_zhi]
    shi_wx = DI_ZHI_WU_XING[shi_line.di_zhi]

    # 用生世
    if WU_XING_SHENG[yong_wx] == shi_wx:
        yong_ws = wangshuai_results[primary_yong.position - 1]
        yong_has_support = _line_has_day_month_support(primary_yong.di_zhi, month_zhi, day_zhi)
        if yong_has_support:
            return {
                "pattern": "静卦用生世(有力)",
                "ji_xiong": "吉",
                "explanation": f"用神{primary_yong.di_zhi}生世爻{shi_line.di_zhi}, 且用神得日月扶, 吉",
            }
        else:
            return {
                "pattern": "静卦用生世(力弱)",
                "ji_xiong": "平",
                "explanation": f"用神生世但用神无日月扶, 力量不足",
            }

    # 用克世
    if WU_XING_KE[yong_wx] == shi_wx:
        # 特例
        if question_type == "cai" and shi_has_support:
            return {
                "pattern": "静卦用克世(求财特例)",
                "ji_xiong": "吉",
                "explanation": "求财卦, 财克世但世有日月扶, 财来就我",
            }
        return {
            "pattern": "静卦用克世",
            "ji_xiong": "凶",
            "explanation": f"用神{primary_yong.di_zhi}克世爻{shi_line.di_zhi}, 凶",
        }

    # Step 3: 用旺世兴
    primary_yong_ws = wangshuai_results[primary_yong.position - 1]
    yong_is_wang = primary_yong_ws["overall"] == "旺"

    if yong_is_wang and shi_has_support:
        return {
            "pattern": "静卦用旺世兴",
            "ji_xiong": "吉",
            "explanation": "用神旺相, 世爻得扶, 吉",
        }
    elif yong_is_wang and not shi_has_support:
        return {
            "pattern": "静卦用旺世衰",
            "ji_xiong": "凶",
            "explanation": "用神旺但世衰无扶, 事可成但于己不利",
        }
    elif not yong_is_wang:
        return {
            "pattern": "静卦用衰",
            "ji_xiong": "凶",
            "explanation": f"用神衰弱, 所求难成",
        }

    return {
        "pattern": "静卦平局",
        "ji_xiong": "平",
        "explanation": "静卦无明显吉凶",
    }


def judge_jixiong(hexagram, yong_shen_liu_qin, wangshuai_results, dongbian_results,
                  question_type, patterns_results=None):
    """
    综合吉凶判断入口。

    根据是否有动爻选择动卦或静卦判断逻辑。

    Returns:
        dict: {"pattern": 卦局名, "ji_xiong": "吉"/"凶"/"平", "explanation": 说明}
    """
    # 判断是否有动爻
    has_moving = any(line.is_moving for line in hexagram.lines)

    if has_moving:
        return judge_dong_gua(
            hexagram, yong_shen_liu_qin,
            wangshuai_results, dongbian_results, question_type,
            patterns_results=patterns_results,
        )
    else:
        return judge_jing_gua(
            hexagram, yong_shen_liu_qin,
            wangshuai_results, question_type
        )
