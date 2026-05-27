"""
动变分析模块 - Dong-Bian (Movement/Change) Analysis

分析动爻变化趋势, 识别有用/无用动爻, 检测暗动。
"""

from .data import (
    DI_ZHI, DI_ZHI_WU_XING,
    WU_XING_SHENG, WU_XING_KE,
    LIU_CHONG, LIU_HE,
    SAN_HE, SAN_HE_BY_ZHI,
    JIN_SHEN, TUI_SHEN,
    get_chang_sheng,
)
from .wangshuai import analyze_line_wangshuai


def is_hui_tou_sheng(line_zhi, bian_zhi):
    """判断是否回头生: 变爻五行生本爻五行"""
    line_wx = DI_ZHI_WU_XING[line_zhi]
    bian_wx = DI_ZHI_WU_XING[bian_zhi]
    return WU_XING_SHENG[bian_wx] == line_wx


def is_hui_tou_ke(line_zhi, bian_zhi):
    """判断是否回头克: 变爻五行克本爻五行"""
    line_wx = DI_ZHI_WU_XING[line_zhi]
    bian_wx = DI_ZHI_WU_XING[bian_zhi]
    return WU_XING_KE[bian_wx] == line_wx


def is_hua_jin_shen(line_zhi, bian_zhi):
    """判断是否化进神: 同五行向前进"""
    return JIN_SHEN.get(line_zhi) == bian_zhi


def is_hua_tui_shen(line_zhi, bian_zhi):
    """判断是否化退神: 同五行向后退"""
    return TUI_SHEN.get(line_zhi) == bian_zhi


def is_hua_jue(line_zhi, bian_zhi):
    """判断是否化绝: 本爻五行在变爻处于绝地"""
    line_wx = DI_ZHI_WU_XING[line_zhi]
    stage = get_chang_sheng(line_wx, bian_zhi)
    return stage == "绝"


def is_hua_po(line_zhi, bian_zhi, month_zhi, day_zhi):
    """
    判断是否化破(化月破或化日破).

    据《古筮真诠》知识点总结:
    '动而化破（化月破或日破）' = 变爻地支与月令相冲(化月破) 或与日令相冲(化日破).
    注: 动爻自身与变爻相冲是 反吟(fan yin), 不是化破.

    Args:
        line_zhi: 动爻地支
        bian_zhi: 变爻地支
        month_zhi: 月支
        day_zhi: 日支
    """
    # 化月破: 变爻地支 == 与月支相冲的地支 (即变爻被月令冲破)
    hua_yue_po = LIU_CHONG.get(month_zhi) == bian_zhi
    # 化日破: 变爻地支 == 与日支相冲的地支 (即变爻被日令冲破)
    hua_ri_po = LIU_CHONG.get(day_zhi) == bian_zhi
    return hua_yue_po or hua_ri_po


def is_fan_yin(line_zhi, bian_zhi):
    """
    判断是否化反吟: 动爻与变爻相冲 (distinct from 化破).

    反吟 = 动变相冲, 既可以是 bian_zhi 是 line_zhi 的相冲支,
    也可以是 line_zhi 是 bian_zhi 的相冲支 (互冲).
    """
    return LIU_CHONG.get(line_zhi) == bian_zhi


def analyze_moving_line(line, hexagram, month_zhi, day_zhi):
    """
    分析单个动爻的变化趋势。

    Args:
        line: YaoLine对象 (必须是动爻)
        hexagram: Hexagram对象
        month_zhi: 月支
        day_zhi: 日支

    Returns:
        dict: 动爻分析结果
    """
    if not line.is_moving or not line.bian_di_zhi:
        return None

    result = {
        "position": line.position,
        "ben_zhi": line.di_zhi,
        "bian_zhi": line.bian_di_zhi,
        "趋旺": [],
        "趋衰": [],
        "is_useless": False,
        "useless_reason": "",
    }

    bian_zhi = line.bian_di_zhi

    # 检查回头生
    if is_hui_tou_sheng(line.di_zhi, bian_zhi):
        result["趋旺"].append("回头生")

    # 检查回头克
    if is_hui_tou_ke(line.di_zhi, bian_zhi):
        result["趋衰"].append("回头克")

    # 检查化进神
    if is_hua_jin_shen(line.di_zhi, bian_zhi):
        result["趋旺"].append("化进神")

    # 检查化退神
    if is_hua_tui_shen(line.di_zhi, bian_zhi):
        result["趋衰"].append("化退神")

    # 检查化绝
    if is_hua_jue(line.di_zhi, bian_zhi):
        # 如果没有回头生则为趋衰
        if not is_hui_tou_sheng(line.di_zhi, bian_zhi):
            result["趋衰"].append("化绝")

    # 检查化破(变爻被月令或日令冲破, 即化月破/化日破)
    # 注: 动爻与变爻相冲是 反吟, 不是化破
    if is_hua_po(line.di_zhi, bian_zhi, month_zhi, day_zhi):
        # 如果没有回头生/克关系才算化破; 且不能同时是进退神
        if (not is_hui_tou_sheng(line.di_zhi, bian_zhi) and
                not is_hui_tou_ke(line.di_zhi, bian_zhi) and
                not is_hua_jin_shen(line.di_zhi, bian_zhi) and
                not is_hua_tui_shen(line.di_zhi, bian_zhi)):
            result["趋衰"].append("化破")

    # 检查化反吟(动爻与变爻相冲) - 吉凶层面记录, 但不直接定性为无用
    # 化反吟≠化破: 反吟是动变相冲, 化破是变爻被月/日令冲
    if is_fan_yin(line.di_zhi, bian_zhi):
        result["趋衰"].append("化反吟")

    # 检查变出临日月
    if bian_zhi == month_zhi or bian_zhi == day_zhi:
        if not is_hui_tou_ke(line.di_zhi, bian_zhi) and \
           not is_hui_tou_sheng(line.di_zhi, bian_zhi):
            result["趋旺"].append("化出临日月")

    # 判断是否无用动爻
    # 无用动爻条件: 回头克 / 化退神 / 化破(化月破日破) / 化绝
    # 注: 化反吟(动变相冲)单独不等于无用, 若同时带回头克才算无用
    if "回头克" in result["趋衰"]:
        result["is_useless"] = True
        result["useless_reason"] = "动变回头克"
    elif "化退神" in result["趋衰"]:
        result["is_useless"] = True
        result["useless_reason"] = "动而化退"
    elif "化破" in result["趋衰"]:
        result["is_useless"] = True
        result["useless_reason"] = "动而化破"
    elif "化绝" in result["趋衰"]:
        result["is_useless"] = True
        result["useless_reason"] = "动而化绝"

    return result


def find_san_he_ju(hexagram):
    """
    检查动爻中是否构成三合局。

    Returns:
        list: 每个三合局 {"wu_xing": 五行, "members": [地支]}
    """
    moving_zhis = []
    for line in hexagram.lines:
        if line.is_moving:
            moving_zhis.append(line.di_zhi)

    san_he_results = []
    for wx, members in SAN_HE.items():
        # 检查三合局三个地支是否都在动爻中出现
        if all(m in moving_zhis for m in members):
            san_he_results.append({
                "wu_xing": wx,
                "members": list(members),
            })

    return san_he_results


def check_dong_yao_interaction(target_line, hexagram, moving_analyses):
    """
    检查其他动爻对目标爻的作用(生/克)。

    只有有用动爻才能对目标爻产生作用。

    Args:
        target_line: 目标爻 YaoLine
        hexagram: Hexagram对象
        moving_analyses: 所有动爻的分析结果 dict

    Returns:
        dict: {"受生": [来源], "受克": [来源]}
    """
    target_wx = DI_ZHI_WU_XING[target_line.di_zhi]
    interactions = {"受生": [], "受克": []}

    for line in hexagram.lines:
        if not line.is_moving:
            continue
        if line.position == target_line.position:
            continue

        # 检查该动爻是否无用
        analysis = moving_analyses.get(line.position)
        if analysis and analysis["is_useless"]:
            continue

        line_wx = DI_ZHI_WU_XING[line.di_zhi]

        # 动爻生目标爻
        if WU_XING_SHENG[line_wx] == target_wx:
            interactions["受生"].append(f"第{line.position}爻{line.di_zhi}{line_wx}")

        # 动爻克目标爻
        if WU_XING_KE[line_wx] == target_wx:
            interactions["受克"].append(f"第{line.position}爻{line.di_zhi}{line_wx}")

    return interactions


def detect_an_dong(hexagram, wangshuai_results):
    """
    检测暗动(An-Dong)。

    暗动条件(有用暗动):
    1. 静爻得月令趋旺, 且被日辰冲 -> 暗动(冲旺为暗动)
    2. 静爻有月气(月建同五行), 且被日辰冲 -> 暗动
    3. 静爻旬空, 且被日辰冲 -> 冲空为暗动
    4. 静爻月衰, 但有动爻生之, 且被日辰冲 -> 暗动
    5. 用神旺相, 且世爻被日辰冲(不论世的旺衰) -> 世爻暗动
    6. 动爻被日辰冲(动不为散) -> 总是有用的暗动/冲起

    Returns:
        list[dict]: 暗动的爻及原因
    """
    month_zhi = hexagram.gan_zhi["month_zhi"]
    day_zhi = hexagram.gan_zhi["day_zhi"]
    an_dong_list = []

    for i, line in enumerate(hexagram.lines):
        # 条件6: 动爻被日冲 (动不为散, 不算暗动但记录)
        if line.is_moving:
            if LIU_CHONG.get(day_zhi) == line.di_zhi:
                an_dong_list.append({
                    "position": line.position,
                    "di_zhi": line.di_zhi,
                    "reason": "动爻逢日冲(冲起不为散)",
                    "type": "冲起",
                })
            continue

        # 只检查静爻
        # 必要条件: 被日辰冲
        if LIU_CHONG.get(day_zhi) != line.di_zhi:
            continue

        ws = wangshuai_results[i]

        # 条件1: 得月令趋旺 (临月令、月令生、月令扶)
        if ws["overall"] == "旺" or any(r in ("临月令", "月令生", "月令扶")
                                         for r in ws["month_wang"]):
            an_dong_list.append({
                "position": line.position,
                "di_zhi": line.di_zhi,
                "reason": "月旺逢日冲(冲旺为暗动)",
                "type": "暗动",
            })
            continue

        # 条件2: 有月气(爻五行与月支同五行但不同地支), 且受日冲 → 暗动
        # 据知识点: '静爻得月令之气而受日冲' 中, "月令之气"指同五行不同地支的月气扶
        # 知识点特例: 丑月亥水受日冲、辰月寅木受日冲、未月巳火受日冲 → 不暗动反应日破
        # 规律: 知识点中三个特例都是月令克爻五行的情况(丑土克亥水, 辰土克寅木, 未土克巳火)
        # 即: 月令五行克爻五行时, 即使同五行月气也不暗动
        line_wx = DI_ZHI_WU_XING[line.di_zhi]
        month_wx = DI_ZHI_WU_XING[month_zhi]
        has_yue_qi = (line_wx == month_wx and line.di_zhi != month_zhi)
        month_ke_line = (WU_XING_KE.get(month_wx) == line_wx)
        if has_yue_qi and not month_ke_line:
            an_dong_list.append({
                "position": line.position,
                "di_zhi": line.di_zhi,
                "reason": "有月气逢日冲(暗动)",
                "type": "暗动",
            })
            continue

        # 条件3: 旬空逢日冲
        if line.is_xun_kong:
            an_dong_list.append({
                "position": line.position,
                "di_zhi": line.di_zhi,
                "reason": "旬空逢日冲(冲空为暗动)",
                "type": "暗动",
            })
            continue

        # 条件4: 月衰但有动爻生
        has_dong_sheng = False
        line_wx = DI_ZHI_WU_XING[line.di_zhi]
        for other_line in hexagram.lines:
            if other_line.is_moving and other_line.position != line.position:
                other_wx = DI_ZHI_WU_XING[other_line.di_zhi]
                if WU_XING_SHENG[other_wx] == line_wx:
                    has_dong_sheng = True
                    break
        if has_dong_sheng:
            an_dong_list.append({
                "position": line.position,
                "di_zhi": line.di_zhi,
                "reason": "月衰有动爻生逢日冲(暗动)",
                "type": "暗动",
            })
            continue

    # 条件5 (单独处理, 不在逐爻循环中):
    # '用神旺相，世爻若受日令冲动，则无论其旺衰，皆算冲起暗动' (用趋世兴)
    # 此条件需要先完成逐爻循环才能确定哪些爻是用神(该模块不知道用神),
    # 所以在此处记录"世爻受日冲"的候选, 由 analyze_dongbian 调用方根据用神旺衰最终判断.
    # 简化处理: 直接检测世爻是否受日冲且为静爻, 作为潜在暗动候选记录
    for line in hexagram.lines:
        if line.is_shi and not line.is_moving:
            if LIU_CHONG.get(day_zhi) == line.di_zhi:
                # 检查是否已经被前面的条件1-4捕获
                already_captured = any(
                    d["position"] == line.position for d in an_dong_list
                )
                if not already_captured:
                    ws = wangshuai_results[line.position - 1]
                    an_dong_list.append({
                        "position": line.position,
                        "di_zhi": line.di_zhi,
                        "reason": "世爻受日冲(待用神旺时确认暗动)",
                        "type": "暗动_候选",
                    })

    return an_dong_list


def analyze_dongbian(hexagram, wangshuai_results):
    """
    完整动变分析。

    Args:
        hexagram: Hexagram对象
        wangshuai_results: 各爻旺衰分析结果

    Returns:
        dict: {
            "moving_analyses": {pos: 动爻分析},
            "san_he_ju": [三合局],
            "an_dong": [暗动],
            "useful_moving": [有用动爻位置],
            "useless_moving": [无用动爻位置],
            "interactions": {pos: 动爻对其他爻的作用},
        }
    """
    month_zhi = hexagram.gan_zhi["month_zhi"]
    day_zhi = hexagram.gan_zhi["day_zhi"]

    # 分析每个动爻
    moving_analyses = {}
    for line in hexagram.lines:
        if line.is_moving:
            analysis = analyze_moving_line(line, hexagram, month_zhi, day_zhi)
            if analysis:
                moving_analyses[line.position] = analysis

    # 分类有用/无用动爻
    useful_moving = []
    useless_moving = []
    for pos, analysis in moving_analyses.items():
        if analysis["is_useless"]:
            useless_moving.append(pos)
        else:
            useful_moving.append(pos)

    # 检查三合局
    san_he_ju = find_san_he_ju(hexagram)

    # 检查动爻间的交互作用
    interactions = {}
    for line in hexagram.lines:
        interaction = check_dong_yao_interaction(line, hexagram, moving_analyses)
        if interaction["受生"] or interaction["受克"]:
            interactions[line.position] = interaction

    # 检测暗动
    an_dong = detect_an_dong(hexagram, wangshuai_results)

    return {
        "moving_analyses": moving_analyses,
        "san_he_ju": san_he_ju,
        "an_dong": an_dong,
        "useful_moving": useful_moving,
        "useless_moving": useless_moving,
        "interactions": interactions,
    }
