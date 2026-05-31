"""
旺衰分析模块 - Wang-Shuai (Prosperity/Decline) Analysis

根据月建(月支)和日辰(日支)判断每爻的旺衰状态。
月建四旺四衰, 日辰五旺二衰。
"""

from .data import (
    DI_ZHI, DI_ZHI_WU_XING,
    WU_XING_SHENG, WU_XING_KE,
    LIU_CHONG, LIU_HE,
    get_chang_sheng,
)


# 旺衰状态常量
WANG = "旺"    # Prosperous
SHUAI = "衰"  # Declining
PING = "平"   # Neutral/balanced


def yue_jian_wangshuai(line_zhi, month_zhi):
    """
    月建旺衰判断 (4旺4衰)。

    旺的条件:
    1. 临月令: 爻支 == 月支
    2. 月令合: 爻支与月支六合
    3. 月令生: 月支五行生爻支五行
    4. 月令扶: 月支五行同爻支五行, 但地支不同

    衰的条件:
    1. 月破(月令冲): 月支冲爻支
    2. 月令克: 月支五行克爻支五行
    3. 休(爻克月): 爻支五行克月支五行
    4. 泄(爻生月): 爻支五行生月支五行

    Returns:
        tuple: (状态列表[str], 详情列表[str])
    """
    line_wx = DI_ZHI_WU_XING[line_zhi]
    month_wx = DI_ZHI_WU_XING[month_zhi]

    wang_reasons = []
    shuai_reasons = []

    # 旺的条件
    # 1. 临月令
    if line_zhi == month_zhi:
        wang_reasons.append("临月令")

    # 2. 月令合 (六合)
    if line_zhi in LIU_HE and LIU_HE[line_zhi][0] == month_zhi:
        wang_reasons.append("月令合")

    # 3. 月令生: 月支五行生爻支五行
    if WU_XING_SHENG[month_wx] == line_wx:
        wang_reasons.append("月令生")

    # 4. 月令扶: 同五行不同支
    if month_wx == line_wx and month_zhi != line_zhi:
        wang_reasons.append("月令扶")

    # 衰的条件
    # 1. 月破(月冲): 月支冲爻支
    if LIU_CHONG.get(month_zhi) == line_zhi:
        shuai_reasons.append("月破")

    # 2. 月令克: 月支五行克爻支五行
    if WU_XING_KE[month_wx] == line_wx:
        shuai_reasons.append("月令克")

    # 3. 休(爻克月): 爻支五行克月支五行
    if WU_XING_KE[line_wx] == month_wx:
        shuai_reasons.append("休")

    # 4. 泄(爻生月): 爻支五行生月支五行
    if WU_XING_SHENG[line_wx] == month_wx:
        shuai_reasons.append("泄")

    return wang_reasons, shuai_reasons


def ri_chen_wangshuai(line_zhi, day_zhi, is_static=True):
    """
    日辰旺衰判断 (5旺2衰)。

    旺的条件:
    1. 临日建: 爻支 == 日支
    2. 静爻日令合: 静爻与日支六合
    3. 日令生: 日支五行生爻支五行
    4. 日令扶: 日支五行同爻支五行, 但地支不同
    5. 临日令长生帝旺: 爻的五行在日支处于长生或帝旺

    衰的条件:
    1. 日令克: 日支五行克爻支五行
    2. 爻绝在日: 爻的五行在日支处于绝地

    Args:
        line_zhi: 爻的地支
        day_zhi: 日支
        is_static: 是否静爻 (影响六合条件)

    Returns:
        tuple: (旺因列表[str], 衰因列表[str])
    """
    line_wx = DI_ZHI_WU_XING[line_zhi]
    day_wx = DI_ZHI_WU_XING[day_zhi]

    wang_reasons = []
    shuai_reasons = []

    # 旺的条件
    # 1. 临日建
    if line_zhi == day_zhi:
        wang_reasons.append("临日建")

    # 2. 静爻日令合
    if is_static and line_zhi in LIU_HE and LIU_HE[line_zhi][0] == day_zhi:
        wang_reasons.append("日令合")

    # 3. 日令生
    if WU_XING_SHENG[day_wx] == line_wx:
        wang_reasons.append("日令生")

    # 4. 日令扶
    if day_wx == line_wx and day_zhi != line_zhi:
        wang_reasons.append("日令扶")

    # 5. 临日令长生帝旺
    stage = get_chang_sheng(line_wx, day_zhi)
    if stage in ("长生", "帝旺"):
        wang_reasons.append(f"临日令{stage}")

    # 衰的条件
    # 1. 日令克
    if WU_XING_KE[day_wx] == line_wx:
        shuai_reasons.append("日令克")

    # 2. 爻绝在日
    if stage == "绝":
        shuai_reasons.append("爻绝在日")

    return wang_reasons, shuai_reasons


def analyze_line_wangshuai(line_zhi, month_zhi, day_zhi, is_static=True):
    """
    综合分析单爻旺衰。

    综合月建和日辰的结果, 判断整体旺衰。
    特殊规则: 如整体趋旺, 日绝视为平; 如整体趋衰, 日绝为真衰。

    Returns:
        dict: {
            "overall": "旺"/"衰"/"平",
            "month_wang": [旺因],
            "month_shuai": [衰因],
            "day_wang": [旺因],
            "day_shuai": [衰因],
            "details": "综合说明"
        }
    """
    month_wang, month_shuai = yue_jian_wangshuai(line_zhi, month_zhi)
    day_wang, day_shuai = ri_chen_wangshuai(line_zhi, day_zhi, is_static)

    # 计算综合得分: 旺因+1, 衰因-1
    wang_score = len(month_wang) + len(day_wang)
    shuai_score = len(month_shuai) + len(day_shuai)

    # 特殊规则: 月令旺衰优先级更高
    # 如果临月令或月令生, 月破除外, 整体趋旺
    has_strong_month_wang = any(r in ("临月令", "月令生", "月令扶") for r in month_wang)
    has_yue_po = "月破" in month_shuai

    # 判断整体趋势(先不考虑日绝)
    preliminary_wang = wang_score > shuai_score
    if has_strong_month_wang and not has_yue_po:
        preliminary_wang = True

    # 特殊规则: 生旺墓绝与日辰的交互
    # 如果整体趋旺, 日绝当平看
    if "爻绝在日" in day_shuai:
        if preliminary_wang:
            day_shuai.remove("爻绝在日")
            day_wang.append("绝处逢生(以平论)")
            # 重新计算
            wang_score = len(month_wang) + len(day_wang)
            shuai_score = len(month_shuai) + len(day_shuai)

    # 最终判断
    if wang_score > shuai_score:
        overall = WANG
    elif shuai_score > wang_score:
        overall = SHUAI
    else:
        overall = PING

    # 月破为重度衰
    if has_yue_po and not has_strong_month_wang:
        overall = SHUAI

    # 生成详情说明
    details_parts = []
    if month_wang:
        details_parts.append(f"月建: {','.join(month_wang)}")
    if month_shuai:
        details_parts.append(f"月建: {','.join(month_shuai)}")
    if day_wang:
        details_parts.append(f"日辰: {','.join(day_wang)}")
    if day_shuai:
        details_parts.append(f"日辰: {','.join(day_shuai)}")
    details = "; ".join(details_parts) if details_parts else "无特殊关系"

    return {
        "overall": overall,
        "month_wang": month_wang,
        "month_shuai": month_shuai,
        "day_wang": day_wang,
        "day_shuai": day_shuai,
        "details": details,
    }


def analyze_hexagram_wangshuai(hexagram):
    """
    分析整卦所有爻的旺衰。

    Args:
        hexagram: Hexagram对象

    Returns:
        list[dict]: 每爻的旺衰分析结果, 索引0=初爻, 索引5=上爻
    """
    month_zhi = hexagram.gan_zhi["month_zhi"]
    day_zhi = hexagram.gan_zhi["day_zhi"]

    results = []
    for line in hexagram.lines:
        is_static = not line.is_moving
        result = analyze_line_wangshuai(
            line.di_zhi, month_zhi, day_zhi, is_static
        )
        result["position"] = line.position
        result["di_zhi"] = line.di_zhi
        result["wu_xing"] = line.wu_xing
        result["liu_qin"] = line.liu_qin
        results.append(result)

    return results
