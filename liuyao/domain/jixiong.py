"""
吉凶判断模块 - Ji-Xiong (Auspicious/Inauspicious) Judgment Engine

实现卦局通论(Gua Ju Tong Lun), 判断整卦吉凶模式。
包括动卦吉利卦局、动卦凶兆卦局、静卦判断规则及特例处理。
"""

from .data import (
    DI_ZHI_WU_XING,
    WU_XING_KE,
    WU_XING_SHENG,
)
from .rules import P0_RULES, RuleContext, RuleEngine
from .rules.dynamic_rules import evaluate_dynamic_classic_rules

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
    "zhongshen_gongming": "官鬼",  # 终身功名
    "zhongshen_caifu": "妻财",     # 终身财福
    "zhongshen_yunshi": "官鬼",    # 终身运势(默认看功名/压力轴)
    "xingren": "官鬼",      # 占行人出行(看行人身份)
    "xingren_gui": "父母",  # 占行人回归(默认取父母为用神)
    "dangri": "妻财",       # 当日财务/结帐类短占，默认看财爻
    "zaizhan": "官鬼",      # 再占卦(粗放分析, 跳过细化细节)
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
# 仅表示该占类支持多个合理用神选择, 不等于默认必须启用双视角。
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


# 默认自动启用双视角的占类。
# 其他支持双视角的占类可通过 CLI/API 显式开启。
DEFAULT_DUAL_PERSPECTIVE_TYPES = {"shiwu"}


def should_use_dual_by_default(question_type):
    """判断占类是否应默认自动启用双视角。"""
    return question_type in DEFAULT_DUAL_PERSPECTIVE_TYPES



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
    动卦吉凶判断: 统一由 P0_RULES 管线处理。

    所有卦局模式（废爻型、时效卦、三合局、内力终局、反馈特例、
    用旺世兴等）均已迁移为 BaseRule 子类，按 priority 排序执行。

    Returns:
        dict: {"pattern": 卦局名, "ji_xiong": "吉"/"凶"/"平", "explanation": 说明}
    """
    month_zhi = hexagram.gan_zhi["month_zhi"]
    day_zhi = hexagram.gan_zhi["day_zhi"]

    shi_line = find_shi_line(hexagram)
    yong_lines = find_yong_shen_lines(hexagram, yong_shen_liu_qin)

    has_transformed_yong = any(
        getattr(line, "bian_liu_qin", None) == yong_shen_liu_qin
        for line in getattr(hexagram, "moving_lines", ())
    )
    if not shi_line or (not yong_lines and not has_transformed_yong):
        return {
            "pattern": "无法判断",
            "ji_xiong": "平",
            "explanation": "未找到用神或世爻",
        }

    # 选择主用神: 优先动爻, 其次旺爻；变爻用神场景允许本卦无主用神。
    primary_yong = yong_lines[0] if yong_lines else None
    for yl in yong_lines:
        if yl.is_moving:
            primary_yong = yl
            break
        if wangshuai_results[yl.position - 1]["overall"] == "旺":
            primary_yong = yl
            break

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
        return _attach_classic_rule_candidates(rule_result.to_jixiong(), rule_context)

    return _attach_classic_rule_candidates({
        "pattern": "平局",
        "ji_xiong": "平",
        "explanation": "卦局平和, 无明显吉凶倾向",
    }, rule_context)


def _attach_classic_rule_candidates(result, rule_context):
    """附加《黄金策》动态候选规则证据, 不改变既有吉凶主判。"""
    if not result:
        return result
    candidates = evaluate_dynamic_classic_rules(rule_context)
    if not candidates:
        return result
    enriched = dict(result)
    enriched["classic_rule_candidates"] = [candidate.to_jixiong() for candidate in candidates]
    return enriched


# _check_special_cases 已迁移至 p0_rules.py:
# ShoumingDongYouQiRule, InnerForceDeclineRule, CaiKeShiSpecialRule,
# ShiwuKeShiSpecialRule, BingZiSunKeShiRule, XingRenKeShiRule,
# YouHuanZiSunKeShiRule


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
        wangshuai_results[primary_yong.position - 1]
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
                "explanation": "用神生世但用神无日月扶, 力量不足",
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
            "explanation": "用神衰弱, 所求难成",
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
    has_moving = bool(getattr(hexagram, "moving_lines", None))

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
