"""
应期推断模块 - Ying-Qi (Response Period) Estimation

根据用神的状态推断事情发生的时间。
基本公式:
- 静爻: 旺静逢冲, 衰静逢值
- 动爻: 逢合或逢值
- 月破爻: 填实、补破、出月破
- 旬空爻: 填空、冲空、出空
- 化进神: 逢值、逢合、逢进
- 化退神: 逢冲、逢退值
"""

from .data import (
    DI_ZHI, DI_ZHI_WU_XING,
    LIU_CHONG, LIU_HE,
    JIN_SHEN, TUI_SHEN,
)


def estimate_yingqi(line, wangshuai_result, moving_analysis=None):
    """
    推断单爻的应期候选。

    Args:
        line: YaoLine对象 (用神爻)
        wangshuai_result: 该爻的旺衰分析结果
        moving_analysis: 该爻的动变分析结果 (如果是动爻)

    Returns:
        list[str]: 应期候选说明列表
    """
    candidates = []
    line_zhi = line.di_zhi
    overall = wangshuai_result["overall"]
    is_yue_po = "月破" in wangshuai_result.get("month_shuai", [])

    # 旬空处理
    if line.is_xun_kong:
        candidates.append(f"填空: {line_zhi}日/月(逢值填实)")
        chong_zhi = LIU_CHONG.get(line_zhi, "")
        if chong_zhi:
            candidates.append(f"冲空: {chong_zhi}日/月(冲空则实)")
        candidates.append("出空: 出旬之日")
        return candidates

    # 月破处理
    if is_yue_po:
        candidates.append(f"填实: {line_zhi}月/日(逢值填实)")
        candidates.append(f"补破: 出{wangshuai_result.get('month_shuai', [''])}之月")
        candidates.append("出月破: 过月即出破")
        return candidates

    # 动爻处理
    if line.is_moving and moving_analysis:
        # 化进神
        if "化进神" in moving_analysis.get("趋旺", []):
            bian_zhi = moving_analysis.get("bian_zhi", "")
            candidates.append(f"逢值: {line_zhi}日/月")
            if line_zhi in LIU_HE:
                he_zhi = LIU_HE[line_zhi][0]
                candidates.append(f"逢合: {he_zhi}日/月")
            # 进神进一步
            if bian_zhi in JIN_SHEN:
                jin_zhi = JIN_SHEN[bian_zhi]
                candidates.append(f"逢进: {jin_zhi}日/月(再进一步)")
            return candidates

        # 化退神
        if "化退神" in moving_analysis.get("趋衰", []):
            chong_zhi = LIU_CHONG.get(line_zhi, "")
            bian_zhi = moving_analysis.get("bian_zhi", "")
            if chong_zhi:
                candidates.append(f"逢冲: {chong_zhi}日/月")
            candidates.append(f"逢退值: {bian_zhi}日/月")
            return candidates

        # 一般动爻: 逢合或逢值
        if line_zhi in LIU_HE:
            he_zhi = LIU_HE[line_zhi][0]
            candidates.append(f"逢合: {he_zhi}日/月")
        candidates.append(f"逢值: {line_zhi}日/月")
        return candidates

    # 静爻处理
    if overall == "旺":
        # 旺静逢冲
        chong_zhi = LIU_CHONG.get(line_zhi, "")
        if chong_zhi:
            candidates.append(f"逢冲: {chong_zhi}日/月(旺静待冲)")
    else:
        # 衰静逢值
        candidates.append(f"逢值: {line_zhi}日/月(衰静待值)")

    # 补充: 逢生之日月
    line_wx = DI_ZHI_WU_XING[line_zhi]
    sheng_zhis = [z for z in DI_ZHI if DI_ZHI_WU_XING[z] != line_wx
                  and z != line_zhi]
    # 找生我的地支
    from .data import WU_XING_SHENG
    sheng_wx = [wx for wx, target in WU_XING_SHENG.items() if target == line_wx]
    if sheng_wx:
        sheng_zhi_list = [z for z in DI_ZHI if DI_ZHI_WU_XING[z] == sheng_wx[0]]
        if sheng_zhi_list and overall != "旺":
            candidates.append(f"逢生: {'/'.join(sheng_zhi_list)}日/月({sheng_wx[0]}生{line_wx})")

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
