"""
动变分析模块 - Dong-Bian (Movement/Change) Analysis

分析动爻变化趋势，识别有用/无用动爻，检测暗动。

【第十章核心规则】
─────────────────────────────────────────────────────
动爻变化判断：
  · 回头生：变爻五行生本爻五行 → 趋旺（有用动爻）
  · 回头克：变爻五行克本爻五行 → 趋衰（无用动爻）
  · 化进神：本爻化出同五行更进一步的地支 → 趋旺
    进神对照：亥→子 | 寅→卯 | 巳→午 | 申→酉 | 丑→辰→未→戌（土进）
  · 化退神：本爻化出同五行退一步的地支 → 趋衰（无用动爻）
  · 化绝：本爻五行在变爻处于绝地 → 趋衰（无用动爻）
  · 化破：本爻与变爻互冲 → 趋衰（无用动爻）
    ★ "化破"是本爻与变爻互冲关系，须说"X与Y互冲化破"，不说"X冲Y"

暗动检测规则（日冲静爻类）：
  ★ 六冲两两互冲，描述暗动时：
    正确："{爻支}与{日支}互冲（{日支}为日令），{爻支}冲起暗动"
    错误："{日支}冲{爻支}"（单向表述，与月破写法混淆）

  暗动成立的条件（静爻被日冲）：
    ① 月旺逢日冲 → 冲旺为暗动（旺爻被冲动，动而有力）
    ② 有月气逢日冲 → 余气暗动（爻生月，泄而有余气）
    ③ 旬空逢日冲 → 冲空为暗动（空爻被冲，出空发动）
    ④ 月衰有动爻生逢日冲 → 得生暗动（得补而被冲起）

  动爻逢日冲：冲起不为散（力度加强，不同于月破之衰）
─────────────────────────────────────────────────────
"""

from typing import Dict, List, Optional

from .data import (
    DI_ZHI, DI_ZHI_WU_XING,
    WU_XING_SHENG, WU_XING_KE,
    LIU_CHONG, LIU_HE,
    SAN_HE, SAN_HE_BY_ZHI,
    JIN_SHEN, TUI_SHEN,
    get_chang_sheng,
)
from .wangshuai import analyze_line_wangshuai

from typing import TypedDict

MovingAnalysis = TypedDict('MovingAnalysis', {
    'position': int,
    'ben_zhi': str,
    'bian_zhi': str,
    '趋旺': List[str],
    '趋衰': List[str],
    'is_useless': bool,
    'useless_reason': str,
})

DongbianResult = TypedDict('DongbianResult', {
    'moving_analyses': Dict[int, MovingAnalysis],
    'san_he_ju': List[Dict],
    'an_dong': List[Dict],
    'useful_moving': List[int],
    'useless_moving': List[int],
    'interactions': Dict[int, Dict],
})


def is_hui_tou_sheng(line_zhi, bian_zhi):
    """判断是否回头生：变爻五行生本爻五行"""
    line_wx = DI_ZHI_WU_XING[line_zhi]
    bian_wx = DI_ZHI_WU_XING[bian_zhi]
    return WU_XING_SHENG[bian_wx] == line_wx


def is_hui_tou_ke(line_zhi, bian_zhi):
    """判断是否回头克：变爻五行克本爻五行"""
    line_wx = DI_ZHI_WU_XING[line_zhi]
    bian_wx = DI_ZHI_WU_XING[bian_zhi]
    return WU_XING_KE[bian_wx] == line_wx


def is_hua_jin_shen(line_zhi, bian_zhi):
    """判断是否化进神：同五行向前进一步"""
    return JIN_SHEN.get(line_zhi) == bian_zhi


def is_hua_tui_shen(line_zhi, bian_zhi):
    """判断是否化退神：同五行退后一步"""
    return TUI_SHEN.get(line_zhi) == bian_zhi


def is_hua_jue(line_zhi, bian_zhi):
    """判断是否化绝：本爻五行在变爻处于绝地"""
    line_wx = DI_ZHI_WU_XING[line_zhi]
    stage = get_chang_sheng(line_wx, bian_zhi)
    return stage == "绝"


def is_hua_po(line_zhi, bian_zhi):
    """
    判断是否化破：本爻与变爻互冲。
    ★ 六冲是互冲关系（如巳亥互冲），化破描述为"{line_zhi}与{bian_zhi}互冲化破"。
    """
    return LIU_CHONG.get(line_zhi) == bian_zhi


def get_chong_zhi(zhi):
    """
    获取与某地支互冲的地支。
    ★ 统一用"互冲"描述，不用单向"X冲Y"写法。
    """
    return LIU_CHONG.get(zhi, "")


def analyze_moving_line(line, hexagram, month_zhi, day_zhi) -> Optional[MovingAnalysis]:
    """
    分析单个动爻的变化趋势。

    Args:
        line: YaoLine对象（必须是动爻）
        hexagram: Hexagram对象
        month_zhi: 月支
        day_zhi: 日支

    Returns:
        Optional[MovingAnalysis]: 动爻分析结果，包含趋旺/趋衰标签及无用标记
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

    # 检查化绝（若无回头生则为趋衰）
    if is_hua_jue(line.di_zhi, bian_zhi):
        if not is_hui_tou_sheng(line.di_zhi, bian_zhi):
            result["趋衰"].append("化绝")

    # 检查化破（本爻与变爻互冲）
    # 注：六冲是互冲关系，此处"化破"描述为本爻与变爻之间的互冲关系
    if is_hua_po(line.di_zhi, bian_zhi):
        if not is_hui_tou_sheng(line.di_zhi, bian_zhi) and \
           not is_hui_tou_ke(line.di_zhi, bian_zhi):
            result["趋衰"].append("化破")

    # 检查变出临日月（不受回头生克影响时有意义）
    if bian_zhi == month_zhi or bian_zhi == day_zhi:
        if not is_hui_tou_ke(line.di_zhi, bian_zhi) and \
           not is_hui_tou_sheng(line.di_zhi, bian_zhi):
            result["趋旺"].append("化出临日月")

    # 判断是否无用动爻
    # 无用条件：回头克 | 化退神 | 化破（无回头关系）| 化绝
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
        list: 每个三合局 {"wu_xing": 五行, "members": [地支], "wang_zhi": 帝旺爻}
    """
    moving_zhis = []
    for line in hexagram.lines:
        if line.is_moving:
            moving_zhis.append(line.di_zhi)

    # 导入三合帝旺表
    from .data import SAN_HE_WANG_ZHI

    san_he_results = []
    for wx, members in SAN_HE.items():
        if all(m in moving_zhis for m in members):
            san_he_results.append({
                "wu_xing": wx,
                "members": list(members),
                "wang_zhi": SAN_HE_WANG_ZHI[wx],  # 能量归宿（帝旺爻）
            })

    return san_he_results


def check_dong_yao_interaction(target_line, hexagram, moving_analyses):
    """
    检查其他动爻对目标爻的作用（生/克）。

    只有有用动爻才能对目标爻产生作用。

    Args:
        target_line: 目标爻 YaoLine
        hexagram: Hexagram对象
        moving_analyses: 所有动爻的分析结果 dict

    Returns:
        dict: {"受生": [来源描述], "受克": [来源描述]}
    """
    target_wx = DI_ZHI_WU_XING[target_line.di_zhi]
    interactions = {"受生": [], "受克": []}

    for line in hexagram.lines:
        if not line.is_moving:
            continue
        if line.position == target_line.position:
            continue

        # 无用动爻不产生生克作用
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
    检测暗动（An-Dong）。

    ★ 核心规范：六冲为互冲关系，描述暗动时统一写法：
        "{爻支}与{日支}互冲，{爻支}冲起暗动"
        ——而非"{日支}冲{爻支}"（避免与月破"月令冲爻"的单向表述混淆）

    暗动成立条件（静爻被日辰冲起）：
    1. 月旺逢日冲 → 冲旺为暗动（旺而被冲，力度十足）
    2. 有月气（余气）逢日冲 → 余气暗动
    3. 静爻旬空逢日冲 → 冲空为暗动（空则出空，比月旺条件更宽松）
    4. 月衰但有动爻生、逢日冲 → 得生暗动
    5. 动爻逢日冲 → 冲起不为散（动爻被冲只会加强力度，不算暗动）

    Returns:
        list[dict]: 暗动的爻及原因
    """
    month_zhi = hexagram.gan_zhi["month_zhi"]
    day_zhi = hexagram.gan_zhi["day_zhi"]
    an_dong_list = []

    for i, line in enumerate(hexagram.lines):
        # 条件5：动爻被日冲 → 冲起不为散（记录但不算暗动）
        if line.is_moving:
            chong_of_day = LIU_CHONG.get(day_zhi, "")
            if chong_of_day == line.di_zhi:
                # 六冲互冲：day_zhi 与 line.di_zhi 互冲
                an_dong_list.append({
                    "position": line.position,
                    "di_zhi": line.di_zhi,
                    "reason": f"动爻{line.di_zhi}与日令{day_zhi}互冲（冲起不为散）",
                    "type": "冲起",
                })
            continue

        # 以下只检查静爻
        # 必要条件：被日辰冲（日支与爻支互冲）
        chong_of_day = LIU_CHONG.get(day_zhi, "")
        if chong_of_day != line.di_zhi:
            continue

        ws = wangshuai_results[i]

        # 条件1：月旺逢日冲 → 冲旺为暗动
        if ws["overall"] == "旺" or any(r in ("临月令", "月令生", "月令扶")
                                         for r in ws["month_wang"]):
            an_dong_list.append({
                "position": line.position,
                "di_zhi": line.di_zhi,
                "reason": f"月旺{line.di_zhi}逢日冲（{line.di_zhi}与{day_zhi}互冲），冲旺为暗动",
                "type": "暗动",
            })
            continue

        # 条件2：有月气（余气）逢日冲
        # 爻生月（泄气），说明爻在该月仍有余气未尽
        line_wx = DI_ZHI_WU_XING[line.di_zhi]
        month_wx = DI_ZHI_WU_XING[month_zhi]
        if WU_XING_SHENG[line_wx] == month_wx:
            an_dong_list.append({
                "position": line.position,
                "di_zhi": line.di_zhi,
                "reason": f"{line.di_zhi}有月气（余气）逢日冲（{line.di_zhi}与{day_zhi}互冲），暗动",
                "type": "暗动",
            })
            continue

        # 条件3：旬空逢日冲 → 冲空为暗动
        if line.is_xun_kong:
            an_dong_list.append({
                "position": line.position,
                "di_zhi": line.di_zhi,
                "reason": f"旬空{line.di_zhi}逢日冲（{line.di_zhi}与{day_zhi}互冲），冲空为暗动",
                "type": "暗动",
            })
            continue

        # 条件4：月衰但有动爻生、逢日冲
        has_dong_sheng = False
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
                "reason": f"月衰{line.di_zhi}有动爻生、逢日冲（{line.di_zhi}与{day_zhi}互冲），暗动",
                "type": "暗动",
            })
            continue

    return an_dong_list


def analyze_dongbian(hexagram, wangshuai_results) -> DongbianResult:
    """
    完整动变分析。

    Args:
        hexagram: Hexagram对象
        wangshuai_results: 各爻旺衰分析结果

    Returns:
        DongbianResult: {
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

    # 检查三合局（含帝旺归宿信息）
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
