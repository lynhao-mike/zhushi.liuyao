"""
世爻特殊规则模块 - Shi-Yao Special Rules

实现世爻动变时的特殊规则, 这些规则优先于一般动变分析。
"""

from .data import (
    DI_ZHI_WU_XING, LIU_CHONG,
)
from .jixiong import JI_SHEN_TABLE
from .dongbian import is_hua_po


def analyze_shiyao_dongbian(hexagram, shi_line, dongbian_results,
                            wangshuai_results, yong_shen_liu_qin,
                            month_zhi=None, day_zhi=None):
    """
    分析世爻动变的特殊规则。

    Rules:
    1. 世爻化破不论破: 世爻化破始终为假破, 关注变爻六亲
    2. 世爻化出六亲定性优先于化日月定性
    3. 世爻动变忌神/化鬼为真, 化日建月建为假
    4. 世爻动变用神/化子孙为真, 化日破月破为假

    Args:
        hexagram: Hexagram对象
        shi_line: 世爻 YaoLine
        dongbian_results: 动变分析结果
        wangshuai_results: 旺衰分析结果
        yong_shen_liu_qin: 用神六亲
        month_zhi: 月支 (optional, from hexagram if not given)
        day_zhi: 日支 (optional, from hexagram if not given)

    Returns:
        dict: {
            "hua_po_is_false": bool,
            "liu_qin_priority": str or None,
            "override_reason": str,
            "effective_trend": str,
        }
    """
    if not shi_line or not shi_line.is_moving:
        return {
            "hua_po_is_false": False,
            "liu_qin_priority": None,
            "override_reason": "世爻未动",
            "effective_trend": "",
        }

    if month_zhi is None:
        month_zhi = hexagram.gan_zhi["month_zhi"]
    if day_zhi is None:
        day_zhi = hexagram.gan_zhi["day_zhi"]

    bian_zhi = shi_line.bian_di_zhi
    bian_lq = shi_line.bian_liu_qin
    ji_shen = JI_SHEN_TABLE.get(yong_shen_liu_qin, "")

    result = {
        "hua_po_is_false": False,
        "liu_qin_priority": None,
        "override_reason": "",
        "effective_trend": "",
    }

    if not bian_zhi:
        return result

    # Rule 1: 世爻化破不论破
    if is_hua_po(shi_line.di_zhi, bian_zhi):
        result["hua_po_is_false"] = True
        result["liu_qin_priority"] = bian_lq
        result["override_reason"] = "世爻化破不论破, 以变爻六亲定性"
        # Determine effective trend from liu_qin
        if bian_lq == yong_shen_liu_qin or bian_lq == "子孙":
            result["effective_trend"] = "吉"
        elif bian_lq == ji_shen or bian_lq == "官鬼":
            result["effective_trend"] = "凶"
        else:
            result["effective_trend"] = "中性"
        return result

    # Rule 2-4: 六亲定性优先
    # Check if bian coincides with day/month (日建/月建 or 日破/月破)
    is_hua_ri_jian = (bian_zhi == day_zhi)
    is_hua_yue_jian = (bian_zhi == month_zhi)
    is_hua_ri_po = (LIU_CHONG.get(day_zhi) == bian_zhi)
    is_hua_yue_po = (LIU_CHONG.get(month_zhi) == bian_zhi)

    has_day_month_coincidence = (is_hua_ri_jian or is_hua_yue_jian or
                                 is_hua_ri_po or is_hua_yue_po)

    # Rule 3: 世爻动变忌神/化鬼为真, 化日建月建为假
    if bian_lq == ji_shen or (bian_lq == "官鬼" and yong_shen_liu_qin != "官鬼"):
        result["liu_qin_priority"] = bian_lq
        if has_day_month_coincidence and (is_hua_ri_jian or is_hua_yue_jian):
            result["override_reason"] = (
                f"世爻动变{bian_lq}为真, "
                f"化日建/月建为假(六亲优先)")
        else:
            result["override_reason"] = f"世爻动变{bian_lq}, 以六亲定性"
        result["effective_trend"] = "凶"
        return result

    # Rule 4: 世爻动变用神/化子孙为真, 化日破月破为假
    if bian_lq == yong_shen_liu_qin or bian_lq == "子孙":
        result["liu_qin_priority"] = bian_lq
        if has_day_month_coincidence and (is_hua_ri_po or is_hua_yue_po):
            result["override_reason"] = (
                f"世爻动变{bian_lq}为真, "
                f"化日破/月破为假(六亲优先)")
        else:
            result["override_reason"] = f"世爻动变{bian_lq}, 以六亲定性"
        result["effective_trend"] = "吉"
        return result

    # General case: 六亲定性
    if bian_lq:
        result["liu_qin_priority"] = bian_lq
        result["override_reason"] = f"世爻动变{bian_lq}"
        result["effective_trend"] = "中性"

    return result
