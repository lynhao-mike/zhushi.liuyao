"""
吉凶判断模块 - Ji-Xiong (Auspicious/Inauspicious) Judgment Engine

实现卦局通论(Gua Ju Tong Lun), 判断整卦吉凶模式。
包括动卦吉利卦局、动卦凶兆卦局、静卦判断规则及特例处理。
"""

from .data import (
    DI_ZHI_WU_XING,
    WU_XING_SHENG, WU_XING_KE,
)


# 用神选择表: 问事类型 -> 用神六亲
YONG_SHEN_TABLE = {
    "cai": "妻财",        # 财运
    "guan": "官鬼",       # 官运/工作
    "hun_male": "妻财",   # 婚姻(男问)
    "hun_female": "官鬼", # 婚姻(女问)
    "bing": "官鬼",       # 疾病(官鬼代表病, 子孙代表药)
    "kaoshi": "父母",     # 考试/文书
    "zinv": "子孙",       # 子女
    "xingRen": "官鬼",    # 行人(默认, 实际需看关系)
    "youHuan": "子孙",    # 忧患(子孙为喜神)
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
    results = []
    for line in hexagram.lines:
        if line.liu_qin == yong_shen_liu_qin:
            results.append(line)
    return results


def find_shi_line(hexagram):
    """找到世爻"""
    for line in hexagram.lines:
        if line.is_shi:
            return line
    return None


def find_ying_line(hexagram):
    """找到应爻"""
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


def judge_dong_gua(hexagram, yong_shen_liu_qin, wangshuai_results, dongbian_results, question_type, liandong_results=None):
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

    三合局优先于单爻判断。

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

    # 三合局优先于单爻判断
    if liandong_results and liandong_results.get("san_he_jixiong"):
        san_he_results = liandong_results["san_he_jixiong"]
        for shr in san_he_results:
            if shr["ji_xiong"] != "平":
                return {
                    "pattern": shr["pattern"],
                    "ji_xiong": shr["ji_xiong"],
                    "explanation": shr["explanation"],
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

    # 8. 用神衰败局
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


def judge_jing_gua(hexagram, yong_shen_liu_qin, wangshuai_results, question_type, dongbian_results=None):
    """
    静卦吉凶判断 (无动爻时)。

    三步判断:
    1. 用忌持世:
       - 用神持世 + 无根 = 短期吉长期凶
       - 用神持世 + 逢破 = 即凶
       - 忌神持世 + 逢破 特例: 求财/疾病/行人/忧患 = 吉
       - 忌神持世 normal = 凶
    2. 用神生克世:
       - 用生世 + 用得日月扶 = 吉
       - 用生世 + 用衰无扶 = 平
       - 用克世 = 凶 (求财+世有扶=吉, 行人=吉)
    3. 用旺世兴: 各自独立分析旺衰
    4. 暗动:
       - 长期问题: 只有用神/元神/忌神暗动影响吉凶
       - 短期问题: 所有暗动可参与判断
    5. 静卦急兆: 暗动或用神带日月

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
        # 检查是否逢月破
        is_yue_po = "月破" in shi_ws.get("month_shuai", [])
        if is_yue_po:
            return {
                "pattern": "用神持世逢月破",
                "ji_xiong": "凶",
                "explanation": "用神持世但逢月破, 即刻凶象",
            }
        # 检查是否无根(日月都不扶)
        has_month_support = any(r in ("临月令", "月令生", "月令扶", "月令合")
                                for r in shi_ws.get("month_wang", []))
        has_day_support = any(r in ("临日建", "日令生", "日令扶", "日令合")
                              for r in shi_ws.get("day_wang", []))
        if not has_month_support and not has_day_support:
            return {
                "pattern": "用神持世无根",
                "ji_xiong": "平",
                "explanation": "用神持世但无根(日月皆不扶), 短期尚可长期凶",
            }
        return {
            "pattern": "用神持世",
            "ji_xiong": "吉",
            "explanation": "用神持世, 所求之事与己关系密切, 吉",
        }

    # 忌神持世
    if shi_liu_qin == ji_shen_liu_qin:
        # 检查是否逢月破
        is_yue_po = "月破" in shi_ws.get("month_shuai", [])
        if is_yue_po:
            # 4个特例: 求财/疾病/行人/忧患 = 吉
            exception_types = ("cai", "bing", "xingRen", "youHuan")
            if question_type in exception_types:
                return {
                    "pattern": f"忌神持世逢破({question_type}特例吉)",
                    "ji_xiong": "吉",
                    "explanation": f"忌神持世逢月破, {question_type}类为特例, 反为吉",
                }
            return {
                "pattern": "忌神持世逢破",
                "ji_xiong": "凶",
                "explanation": "忌神持世逢月破, 大凶",
            }
        # 非逢破的忌神持世特例检查
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
        # 特例: 求财 + 世有扶
        if question_type == "cai" and shi_has_support:
            return {
                "pattern": "静卦用克世(求财特例)",
                "ji_xiong": "吉",
                "explanation": "求财卦, 财克世但世有日月扶, 财来就我",
            }
        # 特例: 行人
        if question_type == "xingRen":
            return {
                "pattern": "静卦用克世(行人特例)",
                "ji_xiong": "吉",
                "explanation": "行人卦, 用神克世, 人即将归来, 吉",
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
        # Step 4: 检查暗动(静卦中的暗动)
        if dongbian_results:
            an_dong = dongbian_results.get("an_dong", [])
            an_dong_effect = _check_jing_gua_andong(
                an_dong, hexagram, yong_shen_liu_qin, ji_shen_liu_qin,
                shi_line, question_type
            )
            if an_dong_effect:
                return an_dong_effect

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


def _check_jing_gua_andong(an_dong, hexagram, yong_shen_liu_qin, ji_shen_liu_qin,
                            shi_line, question_type):
    """
    检查静卦中暗动对吉凶的影响。

    长期问题: 只有用神/元神/忌神暗动影响吉凶。
    短期问题: 所有暗动可参与判断。
    急兆: 暗动或用神带日月。
    """
    if not an_dong:
        return None

    # 元神六亲(生用神者)
    # 六亲生克: 父母生兄弟, 兄弟生子孙, 子孙生妻财, 妻财生官鬼, 官鬼生父母
    YUAN_SHEN_TABLE = {
        "父母": "官鬼",
        "兄弟": "父母",
        "子孙": "兄弟",
        "妻财": "子孙",
        "官鬼": "妻财",
    }

    yuan_shen_liu_qin = YUAN_SHEN_TABLE.get(yong_shen_liu_qin, "")

    # 短期问题类型
    short_term_types = ("bing", "xingRen", "youHuan")
    is_short_term = question_type in short_term_types

    shi_wx = DI_ZHI_WU_XING[shi_line.di_zhi]

    # 检查暗动中是否有关键六亲
    for ad in an_dong:
        if ad.get("type") != "暗动":
            continue
        pos = ad["position"]
        line = hexagram.lines[pos - 1]
        line_liu_qin = line.liu_qin

        # 长期问题: 只关注用神/元神/忌神暗动
        if not is_short_term:
            if line_liu_qin not in (yong_shen_liu_qin, yuan_shen_liu_qin, ji_shen_liu_qin):
                continue

        # 暗动的爻对世爻的作用
        line_wx = DI_ZHI_WU_XING[line.di_zhi]

        if line_liu_qin == yong_shen_liu_qin:
            # 用神暗动生世
            if WU_XING_SHENG[line_wx] == shi_wx:
                return {
                    "pattern": "静卦用神暗动生世(急兆吉)",
                    "ji_xiong": "吉",
                    "explanation": f"静卦中用神{line.di_zhi}暗动生世, 急兆, 吉",
                }
        elif line_liu_qin == ji_shen_liu_qin:
            # 忌神暗动克世
            if WU_XING_KE[line_wx] == shi_wx:
                return {
                    "pattern": "静卦忌神暗动克世(急兆凶)",
                    "ji_xiong": "凶",
                    "explanation": f"静卦中忌神{line.di_zhi}暗动克世, 急兆, 凶",
                }

    return None


def judge_jixiong(hexagram, yong_shen_liu_qin, wangshuai_results, dongbian_results, question_type, liandong_results=None, shiyao_analysis=None, liuchong_liuhe_results=None):
    """
    综合吉凶判断入口。

    根据是否有动爻选择动卦或静卦判断逻辑。

    Returns:
        dict: {"pattern": 卦局名, "ji_xiong": "吉"/"凶"/"平", "explanation": 说明}
    """
    # 判断是否有动爻
    has_moving = any(line.is_moving for line in hexagram.lines)

    if has_moving:
        result = judge_dong_gua(
            hexagram, yong_shen_liu_qin,
            wangshuai_results, dongbian_results, question_type,
            liandong_results=liandong_results
        )
    else:
        result = judge_jing_gua(
            hexagram, yong_shen_liu_qin,
            wangshuai_results, question_type,
            dongbian_results=dongbian_results
        )

    # Wire shiyao_rules: if shi-yao's hua_po_is_false, and the shiyao
    # effective_trend contradicts the verdict, apply override
    if shiyao_analysis and shiyao_analysis.get("hua_po_is_false"):
        effective_trend = shiyao_analysis.get("effective_trend", "")
        # Only override if shiyao gives a clear signal different from current
        if effective_trend == "吉" and result["ji_xiong"] == "凶":
            result = {
                "pattern": result["pattern"] + "(世爻化破不论破覆盖)",
                "ji_xiong": "平",
                "explanation": (
                    result["explanation"] +
                    "; 但世爻化破不论破, 变爻六亲趋吉, 减轻凶象"
                ),
            }
        elif effective_trend == "凶" and result["ji_xiong"] == "吉":
            result = {
                "pattern": result["pattern"] + "(世爻化破不论破覆盖)",
                "ji_xiong": "平",
                "explanation": (
                    result["explanation"] +
                    "; 但世爻化破不论破, 变爻六亲趋凶, 减轻吉象"
                ),
            }

    # Wire liuchong_liuhe: six-clash context can intensify凶 verdicts
    if liuchong_liuhe_results:
        liu_chong = liuchong_liuhe_results.get("liu_chong", {})
        chong_he_huhua = liuchong_liuhe_results.get("chong_he_huhua", {})
        # 六冲变六冲: 败事概率大于成事
        if liu_chong.get("is_liu_chong"):
            chong_type = liu_chong.get("type", "")
            if chong_type == "both":
                if result["ji_xiong"] == "平":
                    result["ji_xiong"] = "凶"
                    result["explanation"] += "; 六冲变六冲, 败事概率大于成事"

    return result
