"""
心态卦识别模块 - Xin-Tai-Gua (Mindset Hexagram) Identification

自动识别暗心态卦(表面事卦实为心态卦)与事卦的区别。
使用子孙(relief spirit)和官鬼(worry spirit)作为核心指标。

核心功能:
1. detect_xintai_gua: 检测是否为心态卦
2. analyze_xintai: 心态卦六模型分析
3. is_true_yongshen: 真/假用神判定
4. find_xinnian_yao: 心念爻定位
"""

from typing import Optional, Dict, List

from .data import (
    DI_ZHI_WU_XING, WU_XING_SHENG, WU_XING_KE,
    LIU_CHONG, LIU_HE, NA_JIA,
    HEXAGRAM_BY_NAME, get_liu_qin, get_chang_sheng,
    BINARY_TO_GUA,
)
from .jixiong import find_shi_line, find_ying_line, find_yong_shen_lines
from .fushen import find_fu_shen, get_cang_yao


# 明确心态类问事类型
MINDSET_QUESTION_TYPES = {
    "youHuan": "worry",
    "worry": "worry",
    "doubt": "doubt",
    "hesitation": "hesitation",
    "preference": "preference",
}

# 心态关键词
MINDSET_KEYWORDS = ["忧", "担心", "害怕", "犹豫", "怀疑", "喜厌", "心态"]


def detect_xintai_gua(hexagram, question_type, wangshuai_results, dongbian_results):
    """
    检测是否为心态卦(暗心态卦)。

    Args:
        hexagram: Hexagram对象
        question_type: 问事类型
        wangshuai_results: 旺衰分析结果
        dongbian_results: 动变分析结果

    Returns:
        dict: {is_xintai, confidence, indicators, xintai_type}
    """
    # 明确心态类问事 -> 直接判定
    if question_type in MINDSET_QUESTION_TYPES:
        return {
            "is_xintai": True,
            "confidence": 1.0,
            "indicators": [f"问事类型为心态类({question_type})"],
            "xintai_type": MINDSET_QUESTION_TYPES[question_type],
        }

    # 检查question_type是否以已知心态关键词开头
    for key in MINDSET_QUESTION_TYPES:
        if question_type.startswith(key):
            return {
                "is_xintai": True,
                "confidence": 1.0,
                "indicators": [f"问事类型匹配心态关键词({key})"],
                "xintai_type": MINDSET_QUESTION_TYPES[key],
            }

    # 暗心态卦检测
    confidence = 0.0
    indicators = []

    shi_line = find_shi_line(hexagram)
    ying_line = find_ying_line(hexagram)

    # Indicator 1: 事用神伏藏(hidden)
    # 根据问事类型确定事用神
    from .jixiong import determine_yong_shen
    base_qt = question_type
    if question_type.startswith("te_zhi_"):
        base_qt = question_type[7:]
    elif question_type.startswith("jia_jie_"):
        base_qt = question_type[8:]
    yong_shen_lq = determine_yong_shen(base_qt)
    yong_lines = find_yong_shen_lines(hexagram, yong_shen_lq)

    if not yong_lines:
        # 用神伏藏
        confidence += 0.3
        indicators.append(f"事用神({yong_shen_lq})伏藏不现")
    else:
        # 检查是否为"假用神"(none of 5 true-yongshen criteria)
        all_false = True
        for yl in yong_lines:
            if is_true_yongshen(yl, hexagram, wangshuai_results, dongbian_results):
                all_false = False
                break
        if all_false:
            confidence += 0.2
            indicators.append(f"事用神({yong_shen_lq})为假用神(无动态参与)")

    # Indicator 2: 世爻变出子孙或官鬼
    if shi_line and shi_line.is_moving and shi_line.bian_liu_qin:
        if shi_line.bian_liu_qin == "子孙":
            confidence += 0.25
            indicators.append("世爻动化子孙(趋向安心)")
        elif shi_line.bian_liu_qin == "官鬼":
            confidence += 0.25
            indicators.append("世爻动化官鬼(趋向忧虑)")

    # Indicator 3: 子孙或官鬼独发(独立动爻)
    moving_analyses = dongbian_results.get("moving_analyses", {})
    for line in hexagram.lines:
        if line.is_moving and line.liu_qin in ("子孙", "官鬼"):
            confidence += 0.2
            indicators.append(f"{line.liu_qin}独发(第{line.position}爻动)")
            break  # 只算一次

    # Indicator 4: 世爻或应爻本身为子孙或官鬼
    if shi_line and shi_line.liu_qin in ("子孙", "官鬼"):
        confidence += 0.15
        indicators.append(f"世爻临{shi_line.liu_qin}")
    elif ying_line and ying_line.liu_qin in ("子孙", "官鬼"):
        confidence += 0.15
        indicators.append(f"应爻临{ying_line.liu_qin}")

    # Indicator 5: 六冲卦(支持心态解读)
    if _is_liu_chong_gua(hexagram):
        confidence += 0.1
        indicators.append("六冲卦(冲散忧虑之象)")

    # 确定心态类型
    xintai_type = _determine_xintai_type(hexagram, shi_line, indicators)

    is_xintai = confidence >= 0.5

    return {
        "is_xintai": is_xintai,
        "confidence": min(confidence, 1.0),
        "indicators": indicators,
        "xintai_type": xintai_type if is_xintai else "event",
    }


def analyze_xintai(hexagram, wangshuai_results, dongbian_results):
    """
    心态卦分析 - 六模型判断。

    Args:
        hexagram: Hexagram对象
        wangshuai_results: 旺衰分析结果
        dongbian_results: 动变分析结果

    Returns:
        dict: {verdict, explanation, details}
    """
    shi_line = find_shi_line(hexagram)
    if not shi_line:
        return {"verdict": "无法判断", "explanation": "未找到世爻", "details": []}

    shi_wx = DI_ZHI_WU_XING[shi_line.di_zhi]
    details = []
    verdict = None
    explanation = ""

    moving_analyses = dongbian_results.get("moving_analyses", {})
    interactions = dongbian_results.get("interactions", {})
    useful_moving = dongbian_results.get("useful_moving", [])

    # Model 1: 动爻作用于世爻
    model1_result = _model1_targeting_shi(
        hexagram, shi_line, shi_wx, moving_analyses, interactions, useful_moving
    )
    if model1_result:
        details.append(model1_result)
        if not verdict:
            verdict = model1_result["verdict"]
            explanation = model1_result["explanation"]

    # Model 2: 世爻动变
    model2_result = _model2_shi_changes(hexagram, shi_line, shi_wx, moving_analyses)
    if model2_result:
        details.append(model2_result)
        if not verdict:
            verdict = model2_result["verdict"]
            explanation = model2_result["explanation"]

    # Model 3: 独发无关世爻
    model3_result = _model3_independent_moving(
        hexagram, shi_line, shi_wx, moving_analyses, useful_moving
    )
    if model3_result:
        details.append(model3_result)
        if not verdict:
            verdict = model3_result["verdict"]
            explanation = model3_result["explanation"]

    # Model 4: 多爻动 - 子孙克官鬼
    model4_result = _model4_multiple_dynamics(hexagram, moving_analyses, useful_moving)
    if model4_result:
        details.append(model4_result)
        if not verdict:
            verdict = model4_result["verdict"]
            explanation = model4_result["explanation"]

    # Model 5: 静卦
    has_moving = any(l.is_moving for l in hexagram.lines)
    if not has_moving:
        model5_result = _model5_static(hexagram, shi_line, wangshuai_results)
        if model5_result:
            details.append(model5_result)
            if not verdict:
                verdict = model5_result["verdict"]
                explanation = model5_result["explanation"]

    # Model 6: 旬空特殊
    model6_result = _model6_xunkong(hexagram)
    if model6_result:
        details.append(model6_result)
        if not verdict:
            verdict = model6_result["verdict"]
            explanation = model6_result["explanation"]

    if not verdict:
        verdict = "平"
        explanation = "卦象平和, 无明显心态指向"

    return {"verdict": verdict, "explanation": explanation, "details": details}


def is_true_yongshen(line, hexagram, wangshuai_results, dongbian_results):
    """
    判断某爻是否为真用神(5条标准, 满足任一即为真)。

    Args:
        line: YaoLine对象
        hexagram: Hexagram对象
        wangshuai_results: 旺衰分析结果
        dongbian_results: 动变分析结果

    Returns:
        bool: True=真用神, False=假用神
    """
    shi_line = find_shi_line(hexagram)
    interactions = dongbian_results.get("interactions", {})
    month_zhi = hexagram.gan_zhi["month_zhi"]
    day_zhi = hexagram.gan_zhi["day_zhi"]

    # (1) 有动爻作用于它(受生或受克)
    line_inter = interactions.get(line.position, {"受生": [], "受克": []})
    if line_inter["受生"] or line_inter["受克"]:
        return True

    # (2) 自身为动爻且作用于世爻(生或克世)
    if line.is_moving and shi_line:
        line_wx = DI_ZHI_WU_XING[line.di_zhi]
        shi_wx = DI_ZHI_WU_XING[shi_line.di_zhi]
        if WU_XING_SHENG[line_wx] == shi_wx or WU_XING_KE[line_wx] == shi_wx:
            return True

    # (3) 持世或持应
    if line.is_shi or line.is_ying:
        return True

    # (4) 与日月相关(临日、临月、合日、合月)
    if line.di_zhi == month_zhi or line.di_zhi == day_zhi:
        return True
    # 六合日月
    if line.di_zhi in LIU_HE:
        he_zhi = LIU_HE[line.di_zhi][0]
        if he_zhi == month_zhi or he_zhi == day_zhi:
            return True

    # (5) 旬空或入墓
    if line.is_xun_kong:
        return True
    line_wx = DI_ZHI_WU_XING[line.di_zhi]
    stage = get_chang_sheng(line_wx, line.di_zhi)
    if stage == "墓":
        return True

    return False


def find_xinnian_yao(hexagram):
    """
    查找心念爻(xin-nian-yao) - 4步优先级。

    Args:
        hexagram: Hexagram对象

    Returns:
        dict or None: {position, di_zhi, wu_xing, liu_qin} 或 None
    """
    shi_line = find_shi_line(hexagram)
    if not shi_line:
        return None

    shi_pos = shi_line.position
    palace_wu_xing = hexagram.palace_wu_xing

    # Step 1: 世爻不动时, 查变卦对位爻
    if not shi_line.is_moving:
        bian_line_info = _get_bian_gua_line_at(hexagram, shi_pos)
        if bian_line_info and bian_line_info["di_zhi"] != shi_line.di_zhi:
            return bian_line_info

    # Step 2: 世爻动(或step1对位同), 查世爻藏爻
    if shi_line.is_moving or True:  # fallthrough from step 1
        cang_yao = get_cang_yao(hexagram)
        cang_at_shi = cang_yao[shi_pos - 1]
        if cang_at_shi["di_zhi"] != shi_line.di_zhi:
            return {
                "position": cang_at_shi["position"],
                "di_zhi": cang_at_shi["di_zhi"],
                "wu_xing": cang_at_shi["wu_xing"],
                "liu_qin": cang_at_shi["liu_qin"],
            }

    # Step 3: 君爻(第5爻)静且六亲不同于世
    jun_pos = 5
    jun_line = hexagram.lines[jun_pos - 1]
    if not jun_line.is_moving and jun_line.liu_qin != shi_line.liu_qin:
        return {
            "position": jun_line.position,
            "di_zhi": jun_line.di_zhi,
            "wu_xing": jun_line.wu_xing,
            "liu_qin": jun_line.liu_qin,
        }

    # Step 4: 君爻动, 查君爻藏爻
    if jun_line.is_moving:
        cang_yao = get_cang_yao(hexagram)
        cang_at_jun = cang_yao[jun_pos - 1]
        if cang_at_jun["di_zhi"] != shi_line.di_zhi:
            return {
                "position": cang_at_jun["position"],
                "di_zhi": cang_at_jun["di_zhi"],
                "wu_xing": cang_at_jun["wu_xing"],
                "liu_qin": cang_at_jun["liu_qin"],
            }

    return None


# ============================================================================
# 内部辅助函数
# ============================================================================

def _is_liu_chong_gua(hexagram):
    """判断是否为六冲卦(本卦上下卦互冲)。"""
    # 六冲卦: 内卦与外卦各爻位对冲
    for i in range(3):
        inner_zhi = hexagram.lines[i].di_zhi
        outer_zhi = hexagram.lines[i + 3].di_zhi
        if LIU_CHONG.get(inner_zhi) != outer_zhi:
            return False
    return True


def _determine_xintai_type(hexagram, shi_line, indicators):
    """根据指标确定心态类型。"""
    has_worry = any("官鬼" in ind for ind in indicators)
    has_relief = any("子孙" in ind for ind in indicators)

    if has_worry and has_relief:
        return "hesitation"
    elif has_worry:
        return "worry"
    elif has_relief:
        return "worry"  # 有子孙动通常是担心某事故寻求安心
    return "worry"


def _get_bian_gua_line_at(hexagram, pos):
    """获取变卦在指定位置的纳甲信息。"""
    bian_name = hexagram.bian_gua_name
    if not bian_name or bian_name not in HEXAGRAM_BY_NAME:
        return None

    bian_info = HEXAGRAM_BY_NAME[bian_name]
    bian_upper = bian_info["upper"]
    bian_lower = bian_info["lower"]

    # 获取变卦纳甲
    if pos <= 3:
        na_jia_info = NA_JIA[bian_lower]
        di_zhi = na_jia_info[1][pos - 1]
    else:
        na_jia_info = NA_JIA[bian_upper]
        di_zhi = na_jia_info[2][pos - 4]

    wu_xing = DI_ZHI_WU_XING[di_zhi]
    liu_qin = get_liu_qin(hexagram.palace_wu_xing, wu_xing)

    return {
        "position": pos,
        "di_zhi": di_zhi,
        "wu_xing": wu_xing,
        "liu_qin": liu_qin,
    }


def _model1_targeting_shi(hexagram, shi_line, shi_wx, moving_analyses,
                          interactions, useful_moving):
    """Model 1: 动爻作用于世爻。"""
    shi_inter = interactions.get(shi_line.position, {"受生": [], "受克": []})

    # 子孙动生世 -> 放心
    for line in hexagram.lines:
        if not line.is_moving or line.position == shi_line.position:
            continue
        if line.liu_qin != "子孙":
            continue
        if line.position not in useful_moving:
            continue
        line_wx = DI_ZHI_WU_XING[line.di_zhi]
        if WU_XING_SHENG[line_wx] == shi_wx:
            return {
                "model": "Model1",
                "verdict": "放心",
                "explanation": f"子孙(第{line.position}爻)动生世爻, 安心之象",
            }

    # 官鬼动生世 -> 有忧无实患
    for line in hexagram.lines:
        if not line.is_moving or line.position == shi_line.position:
            continue
        if line.liu_qin != "官鬼":
            continue
        if line.position not in useful_moving:
            continue
        line_wx = DI_ZHI_WU_XING[line.di_zhi]
        if WU_XING_SHENG[line_wx] == shi_wx:
            return {
                "model": "Model1",
                "verdict": "有忧无实患",
                "explanation": f"官鬼(第{line.position}爻)动生世爻, 忧虑存在但无实际危害",
            }

    # 子孙持世受动克 -> 忧患成真
    if shi_line.liu_qin == "子孙" and shi_inter["受克"]:
        return {
            "model": "Model1",
            "verdict": "忧患成真",
            "explanation": f"子孙持世受动爻克({', '.join(shi_inter['受克'])}), 忧患成真",
        }

    # 官鬼动克世 -> 大凶
    for line in hexagram.lines:
        if not line.is_moving or line.position == shi_line.position:
            continue
        if line.liu_qin != "官鬼":
            continue
        if line.position not in useful_moving:
            continue
        line_wx = DI_ZHI_WU_XING[line.di_zhi]
        if WU_XING_KE[line_wx] == shi_wx:
            return {
                "model": "Model1",
                "verdict": "大凶",
                "explanation": f"官鬼(第{line.position}爻)动克世爻, 实际危险",
            }

    return None


def _model2_shi_changes(hexagram, shi_line, shi_wx, moving_analyses):
    """Model 2: 世爻动变。"""
    if not shi_line.is_moving or not shi_line.bian_liu_qin:
        return None

    shi_analysis = moving_analyses.get(shi_line.position, {})
    has_hui_tou_sheng = "回头生" in shi_analysis.get("趋旺", [])
    has_hui_tou_ke = "回头克" in shi_analysis.get("趋衰", [])

    if shi_line.bian_liu_qin == "子孙":
        if has_hui_tou_sheng:
            return {
                "model": "Model2",
                "verdict": "放心",
                "explanation": "世爻动化子孙且回头生, 双重安心之象",
            }
        return {
            "model": "Model2",
            "verdict": "放心",
            "explanation": "世爻动化子孙, 趋向安心",
        }

    if shi_line.bian_liu_qin == "官鬼":
        if has_hui_tou_ke:
            return {
                "model": "Model2",
                "verdict": "大凶",
                "explanation": "世爻动化官鬼且回头克, 大凶之象",
            }
        return {
            "model": "Model2",
            "verdict": "有忧",
            "explanation": "世爻动化官鬼, 趋向忧虑",
        }

    return None


def _model3_independent_moving(hexagram, shi_line, shi_wx, moving_analyses,
                               useful_moving):
    """Model 3: 独发不作用于世爻。"""
    for line in hexagram.lines:
        if not line.is_moving or line.position == shi_line.position:
            continue
        # 检查是否作用于世爻
        line_wx = DI_ZHI_WU_XING[line.di_zhi]
        targets_shi = (WU_XING_SHENG[line_wx] == shi_wx or
                       WU_XING_KE[line_wx] == shi_wx)
        if targets_shi:
            continue

        analysis = moving_analyses.get(line.position, {})
        is_useless = analysis.get("is_useless", False)

        if line.liu_qin == "官鬼" and is_useless:
            return {
                "model": "Model3",
                "verdict": "放心",
                "explanation": f"官鬼(第{line.position}爻)独发但化为无用, 忧虑消散",
            }
        if line.liu_qin == "子孙" and is_useless:
            return {
                "model": "Model3",
                "verdict": "忧患",
                "explanation": f"子孙(第{line.position}爻)独发但化为无用, 希望落空",
            }

    return None


def _model4_multiple_dynamics(hexagram, moving_analyses, useful_moving):
    """Model 4: 子孙克动态官鬼。"""
    # 找动态子孙和动态官鬼
    moving_zisun = []
    moving_guangui = []
    for line in hexagram.lines:
        if not line.is_moving:
            continue
        if line.liu_qin == "子孙" and line.position in useful_moving:
            moving_zisun.append(line)
        if line.liu_qin == "官鬼":
            moving_guangui.append(line)

    for zs in moving_zisun:
        zs_wx = DI_ZHI_WU_XING[zs.di_zhi]
        for gg in moving_guangui:
            gg_wx = DI_ZHI_WU_XING[gg.di_zhi]
            if WU_XING_KE[zs_wx] == gg_wx:
                return {
                    "model": "Model4",
                    "verdict": "忧患可解",
                    "explanation": f"子孙(第{zs.position}爻)克动态官鬼(第{gg.position}爻), 忧患可解",
                }

    return None


def _model5_static(hexagram, shi_line, wangshuai_results):
    """Model 5: 静卦判断。"""
    ying_line = find_ying_line(hexagram)
    month_zhi = hexagram.gan_zhi["month_zhi"]

    # 子孙持世 -> 放心; 官鬼持世 -> 有忧
    if shi_line.liu_qin == "子孙":
        # 检查月破(feng-po)反转
        shi_ws = wangshuai_results[shi_line.position - 1]
        is_yue_po = LIU_CHONG.get(month_zhi) == shi_line.di_zhi
        if is_yue_po:
            return {
                "model": "Model5",
                "verdict": "有忧",
                "explanation": "子孙持世但逢月破(丰破反转), 安心不实",
            }
        return {
            "model": "Model5",
            "verdict": "放心",
            "explanation": "静卦子孙持世, 安心之象",
        }

    if shi_line.liu_qin == "官鬼":
        is_yue_po = LIU_CHONG.get(month_zhi) == shi_line.di_zhi
        if is_yue_po:
            return {
                "model": "Model5",
                "verdict": "放心",
                "explanation": "官鬼持世但逢月破(丰破反转), 忧虑无力",
            }
        return {
            "model": "Model5",
            "verdict": "有忧",
            "explanation": "静卦官鬼持世, 忧虑之象",
        }

    # 非子孙/官鬼持世, 查应爻
    if ying_line:
        if ying_line.liu_qin == "子孙":
            return {
                "model": "Model5",
                "verdict": "放心",
                "explanation": "静卦子孙临应爻, 外来安慰",
            }
        if ying_line.liu_qin == "官鬼":
            return {
                "model": "Model5",
                "verdict": "有忧",
                "explanation": "静卦官鬼临应爻, 外来忧虑",
            }

    return None


def _model6_xunkong(hexagram):
    """Model 6: 旬空特殊规则。"""
    for line in hexagram.lines:
        if not line.is_xun_kong:
            continue
        if line.liu_qin == "子孙":
            return {
                "model": "Model6",
                "verdict": "短期忧虑持续",
                "explanation": f"子孙(第{line.position}爻)旬空, 短期内忧虑难以消解",
            }
        if line.liu_qin == "官鬼":
            return {
                "model": "Model6",
                "verdict": "短期安全",
                "explanation": f"官鬼(第{line.position}爻)旬空, 短期内危险未显",
            }

    return None
