"""
月破真假分析模块 - Yue Po (Month Break) True/False Analysis

判断月破爻是否为真破或假破, 分析矛盾趋势。
"""

from .data import (
    DI_ZHI_WU_XING, LIU_CHONG,
    WU_XING_SHENG, WU_XING_KE,
    JIN_SHEN, TUI_SHEN,
)
from .dongbian import is_hui_tou_sheng, is_hui_tou_ke, is_hua_jin_shen, is_hua_tui_shen


def is_zhen_po(line, hexagram, dongbian_results, wangshuai_results):
    """
    判断月破爻是否为真破。

    假破条件(不为真破):
    1. 动而逢破不为真破 - 动爻遇月破, 因动爻自身有方向
    2. 化破但变爻可回头作用者不为真破 - 变爻对动爻有回头生/克
    3. 化进退又化破者不为真破 - 动化进神/退神优先于化破
    4. 自占自事世爻动而化破不为真破 - 世爻之动趋向变爻, 不以破论

    Args:
        line: YaoLine对象
        hexagram: Hexagram对象
        dongbian_results: 动变分析结果
        wangshuai_results: 旺衰分析结果

    Returns:
        dict: {
            'is_zhen_po': bool,
            'reason': str,
            'condition': str,
        }
    """
    month_zhi = hexagram.gan_zhi["month_zhi"]

    # 检查该爻是否月破
    is_yue_po = (LIU_CHONG.get(month_zhi) == line.di_zhi)

    # 也检查是否化破(动爻变爻被月冲)
    is_hua_po = False
    if line.is_moving and line.bian_di_zhi:
        is_hua_po = (LIU_CHONG.get(month_zhi) == line.bian_di_zhi)

    if not is_yue_po and not is_hua_po:
        return {
            "is_zhen_po": False,
            "reason": "非月破爻",
            "condition": "none",
        }

    # 假破条件1: 动而逢破不为真破
    if is_yue_po and line.is_moving:
        return {
            "is_zhen_po": False,
            "reason": "动而逢破不为真破, 动爻自身有运动方向",
            "condition": "动而逢破",
        }

    # 假破条件2: 化破但变爻可回头作用者不为真破
    if line.is_moving and line.bian_di_zhi:
        has_hui_tou = (is_hui_tou_sheng(line.di_zhi, line.bian_di_zhi) or
                       is_hui_tou_ke(line.di_zhi, line.bian_di_zhi))
        if is_hua_po and has_hui_tou:
            return {
                "is_zhen_po": False,
                "reason": "化破但变爻可回头作用, 动能中转不为真破",
                "condition": "化破有回头作用",
            }

        # 假破条件3: 化进退又化破不为真破
        has_jin_tui = (is_hua_jin_shen(line.di_zhi, line.bian_di_zhi) or
                       is_hua_tui_shen(line.di_zhi, line.bian_di_zhi))
        if is_hua_po and has_jin_tui:
            return {
                "is_zhen_po": False,
                "reason": "化进退神又化破, 进退为真化破为假",
                "condition": "化进退又化破",
            }

    # 假破条件4: 自占自事世爻动而化破不为真破
    if line.is_shi and line.is_moving and is_hua_po:
        return {
            "is_zhen_po": False,
            "reason": "自占自事世爻动而化破, 世爻趋势以变爻六亲论, 不以破论",
            "condition": "世爻动化破",
        }

    # 真破: 静爻遭月破且衰弱
    if is_yue_po and not line.is_moving:
        return {
            "is_zhen_po": True,
            "reason": "静爻遭月破, 为真破",
            "condition": "静爻月破",
        }

    # 其他化破情况(无回头作用, 无进退, 非世爻)
    if is_hua_po:
        return {
            "is_zhen_po": True,
            "reason": "动而化破且无回头作用/进退可解, 为真破",
            "condition": "化破无解",
        }

    return {
        "is_zhen_po": True,
        "reason": "月破且无假破条件, 为真破",
        "condition": "真破",
    }


def analyze_maodun_qushi(hexagram, dongbian_results, wangshuai_results):
    """
    矛盾趋势分析 - 当动爻存在相互矛盾的旺衰因素时的辨别原则。

    三大原则:
    1. 动能轨迹终点原则 - 变爻是动能的终点, 回头作用优先
    2. 重动轻静/重内轻外 - 卦内动变因素(内因)重于日月造成的旺衰(外因)
    3. 世爻之变原则 - 世爻之动不存在有用无用概念, 世爻趋势必须重视

    例: 爻动而化月建的同时又是动而化绝, 化月建是外因, 化绝是内因,
    内重于外, 则化月建为假, 化绝衰败无用才真。

    Args:
        hexagram: Hexagram对象
        dongbian_results: 动变分析结果
        wangshuai_results: 旺衰分析结果

    Returns:
        list[dict]: 矛盾趋势分析结果
    """
    moving_analyses = dongbian_results.get("moving_analyses", {})
    month_zhi = hexagram.gan_zhi["month_zhi"]
    day_zhi = hexagram.gan_zhi["day_zhi"]
    results = []

    for pos, ma in moving_analyses.items():
        line = hexagram.lines[pos - 1]
        contradictions = []

        has_wang = len(ma.get("趋旺", [])) > 0
        has_shuai = len(ma.get("趋衰", [])) > 0

        if not (has_wang and has_shuai):
            continue

        # 原则1: 动能轨迹终点 - 回头生/克优先于化日月
        wang_reasons = ma.get("趋旺", [])
        shuai_reasons = ma.get("趋衰", [])

        # 检查是否有内因(回头生/克/进退/绝)
        internal_wang = [r for r in wang_reasons
                         if r in ("回头生", "化进神")]
        internal_shuai = [r for r in shuai_reasons
                          if r in ("回头克", "化退神", "化绝", "化破")]
        # 检查是否有外因(化出临日月)
        external_wang = [r for r in wang_reasons
                         if r in ("化出临日月",)]

        principle_applied = None
        conclusion = None

        # 原则3: 世爻之变 - 世爻动变回头生克同时化破, 生克为真化破为假
        if line.is_shi:
            if internal_wang and "化破" in shuai_reasons:
                principle_applied = "世爻之变原则"
                conclusion = "世爻回头生/进神为真, 化破为假"
            elif internal_shuai and external_wang:
                principle_applied = "世爻之变原则"
                conclusion = "世爻内因趋衰为真, 外因趋旺为假"
            elif internal_wang and internal_shuai:
                principle_applied = "世爻之变原则"
                conclusion = "世爻动变矛盾, 需结合具体情况判断"
            else:
                principle_applied = "世爻之变原则"
                conclusion = "世爻之动必须重视, 趋势以变爻六亲定位"

        # 原则2: 重动轻静/重内轻外
        elif internal_wang and external_wang:
            # 不太可能, 但如果内外都旺不算矛盾
            pass
        elif internal_shuai and external_wang:
            principle_applied = "重动轻静/重内轻外"
            conclusion = f"内因({', '.join(internal_shuai)})重于外因({', '.join(external_wang)}), 趋衰为真"
        elif internal_wang and "化破" in shuai_reasons:
            # 原则1: 回头生/进神 vs 化破
            principle_applied = "动能轨迹终点原则"
            conclusion = f"回头作用/进退({', '.join(internal_wang)})优先, 化破为假"

        if principle_applied:
            results.append({
                "position": pos,
                "di_zhi": line.di_zhi,
                "bian_zhi": ma.get("bian_zhi", ""),
                "wang_reasons": wang_reasons,
                "shuai_reasons": shuai_reasons,
                "principle": principle_applied,
                "conclusion": conclusion,
                "is_shi": line.is_shi,
            })

    return results


def analyze_yuepo(hexagram, dongbian_results, wangshuai_results):
    """
    月破真假综合分析入口。

    Args:
        hexagram: Hexagram对象
        dongbian_results: 动变分析结果
        wangshuai_results: 旺衰分析结果

    Returns:
        dict: 综合月破分析结果
    """
    month_zhi = hexagram.gan_zhi["month_zhi"]

    # 找出所有月破相关爻
    po_analyses = []
    for line in hexagram.lines:
        # 检查爻本身月破
        is_yue_po = (LIU_CHONG.get(month_zhi) == line.di_zhi)
        # 检查变爻月破
        is_bian_yue_po = False
        if line.is_moving and line.bian_di_zhi:
            is_bian_yue_po = (LIU_CHONG.get(month_zhi) == line.bian_di_zhi)

        if is_yue_po or is_bian_yue_po:
            result = is_zhen_po(line, hexagram, dongbian_results,
                                wangshuai_results)
            po_analyses.append({
                "position": line.position,
                "di_zhi": line.di_zhi,
                "bian_zhi": line.bian_di_zhi,
                "is_yue_po": is_yue_po,
                "is_bian_yue_po": is_bian_yue_po,
                "analysis": result,
            })

    # 矛盾趋势分析
    maodun = analyze_maodun_qushi(hexagram, dongbian_results, wangshuai_results)

    return {
        "po_analyses": po_analyses,
        "maodun_qushi": maodun,
        "has_po": len(po_analyses) > 0,
    }
