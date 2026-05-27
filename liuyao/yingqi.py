"""
应期推断模块 - Ying-Qi (Response Period) Estimation

根据用神的状态推断事情发生的时间。

【第十章应期基本公式】
─────────────────────────────────────────────────────
· 旺静爻：逢冲之日/月（旺静待冲）
    输出格式："{爻支}旺静，待{互冲支}日/月冲动"
    ★ 绝不输出"{冲支}冲{爻支}"——六冲是互冲，用"XY互冲"表述

· 衰静爻：逢值之日/月（衰静待值，逢本支）
· 动爻（一般）：逢合或逢值
· 化进神：逢值、逢合、待进（进一步的支）
· 化退神：待互冲支冲起，或逢退值（退后那支）
· 月破爻：填实（逢值）| 补破（出月破）| 过月即出破
· 旬空爻：填空（逢值）| 冲空（逢互冲支）| 出旬之日
─────────────────────────────────────────────────────
"""

from .data import (
    DI_ZHI, DI_ZHI_WU_XING,
    LIU_CHONG, LIU_HE,
    JIN_SHEN, TUI_SHEN,
    WU_XING_SHENG,
)

# 六冲互冲对照（用于应期输出时的规范表述）
_CHONG_PAIRS = {
    "子": "午", "午": "子",
    "丑": "未", "未": "丑",
    "寅": "申", "申": "寅",
    "卯": "酉", "酉": "卯",
    "辰": "戌", "戌": "辰",
    "巳": "亥", "亥": "巳",
}


def _chong_label(zhi_a, zhi_b):
    """
    生成规范的互冲描述标签。
    ★ 统一格式："{小支}{大支}互冲"，按 DI_ZHI 顺序排小的在前。
    例：_chong_label("亥", "巳") → "巳亥互冲"
    例：_chong_label("巳", "亥") → "巳亥互冲"
    """
    order = ("子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥")
    if order.index(zhi_a) <= order.index(zhi_b):
        return f"{zhi_a}{zhi_b}互冲"
    return f"{zhi_b}{zhi_a}互冲"


def estimate_yingqi(line, wangshuai_result, moving_analysis=None):
    """
    推断单爻的应期候选。

    Args:
        line: YaoLine对象（用神爻）
        wangshuai_result: 该爻的旺衰分析结果
        moving_analysis: 该爻的动变分析结果（如果是动爻）

    Returns:
        list[str]: 应期候选说明列表
    """
    candidates = []
    line_zhi = line.di_zhi
    overall = wangshuai_result["overall"]
    is_yue_po = "月破" in wangshuai_result.get("month_shuai", [])

    # ── 旬空处理 ────────────────────────────────────────────────
    if line.is_xun_kong:
        candidates.append(f"填空: 逢{line_zhi}日/月（临值填实）")
        chong_zhi = _CHONG_PAIRS.get(line_zhi, "")
        if chong_zhi:
            candidates.append(
                f"冲空: 逢{chong_zhi}日/月（{_chong_label(line_zhi, chong_zhi)}，冲空则实）"
            )
        candidates.append("出空: 出旬之日（旬满自实）")
        return candidates

    # ── 月破处理 ────────────────────────────────────────────────
    if is_yue_po:
        candidates.append(f"填实: 逢{line_zhi}日/月（临值补破）")
        candidates.append("出月破: 过当月即出破")
        return candidates

    # ── 动爻处理 ─────────────────────────────────────────────────
    if line.is_moving and moving_analysis:
        # 化进神
        if "化进神" in moving_analysis.get("趋旺", []):
            bian_zhi = moving_analysis.get("bian_zhi", "")
            candidates.append(f"逢值: {line_zhi}日/月（临本支）")
            if line_zhi in LIU_HE:
                he_zhi = LIU_HE[line_zhi][0]
                candidates.append(f"逢合: {he_zhi}日/月（{line_zhi}{he_zhi}合）")
            if bian_zhi in JIN_SHEN:
                jin_zhi = JIN_SHEN[bian_zhi]
                candidates.append(f"逢进: {jin_zhi}日/月（化进神再进一步）")
            return candidates

        # 化退神
        if "化退神" in moving_analysis.get("趋衰", []):
            chong_zhi = _CHONG_PAIRS.get(line_zhi, "")
            bian_zhi = moving_analysis.get("bian_zhi", "")
            if chong_zhi:
                candidates.append(
                    f"逢冲: {chong_zhi}日/月（{_chong_label(line_zhi, chong_zhi)}冲起）"
                )
            if bian_zhi:
                candidates.append(f"逢退值: {bian_zhi}日/月（化退后之支临值）")
            return candidates

        # 一般动爻：逢合或逢值
        if line_zhi in LIU_HE:
            he_zhi = LIU_HE[line_zhi][0]
            candidates.append(f"逢合: {he_zhi}日/月（{line_zhi}{he_zhi}合）")
        candidates.append(f"逢值: {line_zhi}日/月（临本支）")
        return candidates

    # ── 静爻处理 ─────────────────────────────────────────────────
    if overall == "旺":
        # 旺静逢冲（旺而被冲才能应期）
        chong_zhi = _CHONG_PAIRS.get(line_zhi, "")
        if chong_zhi:
            candidates.append(
                f"逢冲: {chong_zhi}日/月（{_chong_label(line_zhi, chong_zhi)}，旺静待冲）"
            )
    else:
        # 衰静逢值
        candidates.append(f"逢值: {line_zhi}日/月（衰静待临值）")

    # 补充：逢生之日月（衰爻得生可应期）
    line_wx = DI_ZHI_WU_XING[line_zhi]
    sheng_wx_list = [wx for wx, target in WU_XING_SHENG.items() if target == line_wx]
    if sheng_wx_list and overall != "旺":
        sheng_wx = sheng_wx_list[0]
        sheng_zhi_list = [z for z in DI_ZHI if DI_ZHI_WU_XING[z] == sheng_wx]
        if sheng_zhi_list:
            candidates.append(
                f"逢生: {'/'.join(sheng_zhi_list)}日/月（{sheng_wx}生{line_wx}）"
            )

    return candidates


def analyze_yingqi(hexagram, yong_shen_lines, wangshuai_results, dongbian_results):
    """
    分析用神的应期。

    Args:
        hexagram: Hexagram对象
        yong_shen_lines: 用神爻列表
        wangshuai_results: 所有爻的旺衰结果
        dongbian_results: 动变分析结果

    Returns:
        list[dict]: 每个用神爻的应期候选
    """
    results = []
    moving_analyses = dongbian_results.get("moving_analyses", {})

    for line in yong_shen_lines:
        ws = wangshuai_results[line.position - 1]
        ma = moving_analyses.get(line.position)

        candidates = estimate_yingqi(line, ws, ma)
        results.append({
            "position": line.position,
            "di_zhi": line.di_zhi,
            "liu_qin": line.liu_qin,
            "candidates": candidates,
        })

    return results
