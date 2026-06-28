"""
动变分析模块 - Dong-Bian (Movement/Change) Analysis

分析动爻变化趋势, 识别有用/无用动爻, 检测暗动。
"""

from .data import (
    DI_ZHI_WU_XING,
    WU_XING_SHENG, WU_XING_KE,
    LIU_CHONG,
    SAN_HE,
    JIN_SHEN, TUI_SHEN,
    get_chang_sheng,
)


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


def is_hua_po(line_zhi, bian_zhi):
    """判断是否化破: 本爻与变爻相冲"""
    return LIU_CHONG.get(line_zhi) == bian_zhi


def analyze_moving_line(line, month_zhi, day_zhi):
    """
    分析单个动爻的变化趋势。

    Args:
        line: YaoLine对象 (必须是动爻)
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

    line_zhi = line.di_zhi
    bian_zhi = line.bian_di_zhi
    line_wx = line.wu_xing
    bian_wx = line.bian_wu_xing or DI_ZHI_WU_XING[bian_zhi]
    is_hui_sheng = WU_XING_SHENG[bian_wx] == line_wx
    is_hui_ke = WU_XING_KE[bian_wx] == line_wx

    # 检查回头生/克
    if is_hui_sheng:
        result["趋旺"].append("回头生")
    if is_hui_ke:
        result["趋衰"].append("回头克")

    # 检查化进/退神
    if JIN_SHEN.get(line_zhi) == bian_zhi:
        result["趋旺"].append("化进神")
    if TUI_SHEN.get(line_zhi) == bian_zhi:
        result["趋衰"].append("化退神")

    # 检查化绝
    if get_chang_sheng(line_wx, bian_zhi) == "绝" and not is_hui_sheng:
        result["趋衰"].append("化绝")

    # 检查化破(本爻与变爻相冲)
    if LIU_CHONG.get(line_zhi) == bian_zhi and not is_hui_sheng and not is_hui_ke:
        result["趋衰"].append("化破")

    # 检查变出临日月
    if (bian_zhi == month_zhi or bian_zhi == day_zhi) and not is_hui_ke and not is_hui_sheng:
        result["趋旺"].append("化出临日月")

    # 判断是否无用动爻
    # 无用动爻条件: 回头克, 化退, 化破(无回头关系), 化绝
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


def _get_moving_lines(hexagram):
    """优先使用 Hexagram 预构建动爻索引, 兼容旧对象回退扫描。"""
    indexed = getattr(hexagram, "moving_lines", None)
    if indexed is not None:
        return indexed
    return [line for line in hexagram.lines if line.is_moving]


def find_san_he_ju(hexagram, moving_lines=None):
    """
    检查动爻中是否构成三合局。

    Returns:
        list: 每个三合局 {"wu_xing": 五行, "members": [地支]}
    """
    if moving_lines is None:
        moving_lines = _get_moving_lines(hexagram)
    if len(moving_lines) < 3:
        return []
    moving_zhis = {line.di_zhi for line in moving_lines}

    san_he_results = []
    for wx, members in SAN_HE.items():
        # 检查三合局三个地支是否都在动爻中出现
        if all(m in moving_zhis for m in members):
            san_he_results.append({
                "wu_xing": wx,
                "members": list(members),
            })

    return san_he_results


def check_dong_yao_interaction(target_line, moving_lines, moving_analyses):
    """
    检查其他动爻对目标爻的作用(生/克)。

    只有有用动爻才能对目标爻产生作用。

    Args:
        target_line: 目标爻 YaoLine
        moving_lines: 动爻列表
        moving_analyses: 所有动爻的分析结果 dict

    Returns:
        dict: {"受生": [来源], "受克": [来源]}
    """
    target_wx = DI_ZHI_WU_XING[target_line.di_zhi]
    interactions = {"受生": [], "受克": []}

    for line in moving_lines:
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


def _determine_compound_final_target(hexagram, primary_yong_position=None, question_type=None):
    """最终目标爻判定: 先处理世用合一，再区分自占/代占。"""
    shi_line = getattr(hexagram, "shi_line", None)
    if shi_line is None:
        return {
            "kind": "unknown",
            "position": None,
            "reason": "未找到世爻, 无法判定最终目标爻",
        }

    if primary_yong_position is not None and primary_yong_position == shi_line.position:
        return {
            "kind": "shi_yong",
            "position": shi_line.position,
            "reason": "世用合一, 复合动以世用一体为最终目标",
        }

    if question_type in {"fumu", "xiongdi", "zinv", "hun_male", "hun_female", "guan", "cai", "kaoshi", "bing", "other"}:
        return {
            "kind": "shi",
            "position": shi_line.position,
            "reason": "当前按自占/常规事占处理, 世爻作为复合动最终承受点",
        }

    if primary_yong_position is not None:
        return {
            "kind": "yong",
            "position": primary_yong_position,
            "reason": "代占/非自占场景暂以用神为最终目标",
        }

    return {
        "kind": "shi",
        "position": shi_line.position,
        "reason": "未提供主用神位置, 回退为世爻终点",
    }


def analyze_compound_movement(hexagram, moving_analyses, useful_moving, san_he_ju=None,
                              primary_yong_position=None, question_type=None):
    """复合之动: 输出可供规则层消费的最终目标爻裁判输入。"""
    final_target = _determine_compound_final_target(
        hexagram, primary_yong_position=primary_yong_position, question_type=question_type
    )
    if san_he_ju:
        return [{
            "mode": "san_he",
            "final_target_kind": final_target["kind"],
            "final_target_position": final_target["position"],
            "path": [],
            "aggregated_to_position": None,
            "acts_on_target": "none",
            "valid": True,
            "reason": "三合局优先于单爻连动",
            "source_positions": [],
            "ju": ju,
        } for ju in san_he_ju]

    useful = [line for line in _get_moving_lines(hexagram) if line.position in useful_moving]
    if len(useful) < 2:
        return []

    results = []
    target_pos = final_target["position"]
    for source in useful:
        for middle in useful:
            if source.position == middle.position:
                continue
            if WU_XING_SHENG[source.wu_xing] == middle.wu_xing:
                # 一跳：A -> target
                acts = "none"
                valid = False
                path = [source.position, middle.position]
                if target_pos is not None and middle.position == target_pos:
                    acts = "sheng"
                    valid = True
                else:
                    # 二跳：A -> B -> target
                    for target in useful:
                        if target.position in (source.position, middle.position):
                            continue
                        if target_pos is not None and target.position == target_pos and WU_XING_SHENG[middle.wu_xing] == target.wu_xing:
                            acts = "sheng"
                            valid = True
                            path = [source.position, middle.position, target.position]
                            break
                results.append({
                    "mode": "chain_sheng",
                    "final_target_kind": final_target["kind"],
                    "final_target_position": target_pos,
                    "path": path,
                    "aggregated_to_position": middle.position,
                    "acts_on_target": acts,
                    "valid": valid,
                    "reason": f"第{source.position}爻生第{middle.position}爻, {'并接续生到最终目标爻' if valid else '但未打到最终目标爻'}",
                    "source_positions": path,
                })
            elif WU_XING_KE[source.wu_xing] == middle.wu_xing:
                acts = "none"
                valid = False
                path = [source.position, middle.position]
                if target_pos is not None and middle.position == target_pos:
                    acts = "ke"
                    valid = True
                else:
                    # 二跳阻断：A 克 B，且 B 原可生目标
                    if target_pos is not None:
                        for target in useful:
                            if target.position in (source.position, middle.position):
                                continue
                            if target.position == target_pos and WU_XING_SHENG[middle.wu_xing] == target.wu_xing:
                                acts = "block"
                                valid = True
                                path = [source.position, middle.position, target.position]
                                break
                results.append({
                    "mode": "chain_ke_cancel",
                    "final_target_kind": final_target["kind"],
                    "final_target_position": target_pos,
                    "path": path,
                    "aggregated_to_position": middle.position,
                    "acts_on_target": acts,
                    "valid": valid,
                    "reason": f"第{source.position}爻克第{middle.position}爻, {'并阻断其后续到目标爻' if valid and acts == 'block' else ('最终克到目标爻' if valid else '但未打到最终目标爻')}",
                    "source_positions": path,
                })

    return results


def detect_an_dong(hexagram, wangshuai_results, moving_lines=None):
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
    if moving_lines is None:
        moving_lines = _get_moving_lines(hexagram)

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

        # 条件2: 有月气(月建同五行但非临/生/扶, 即余气)
        # "有气"指爻的五行在该月仍有余气, 如火在未月(未属土但火气未尽)
        # 这里检查爻五行与月支五行相同但未被条件1捕获的情况不存在,
        # 因此改为检查月支是否为爻五行的余气支(爻五行生月支五行, 即泄而非绝)
        line_wx = DI_ZHI_WU_XING[line.di_zhi]
        month_wx = DI_ZHI_WU_XING[month_zhi]
        if WU_XING_SHENG[line_wx] == month_wx:
            # 爻生月(泄气), 说明爻在该月仍有余气(未完全衰败)
            an_dong_list.append({
                "position": line.position,
                "di_zhi": line.di_zhi,
                "reason": "有月气(余气)逢日冲(暗动)",
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
        for other_line in moving_lines:
            if other_line.position != line.position:
                other_wx = other_line.wu_xing
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

    return an_dong_list


def analyze_dongbian(hexagram, wangshuai_results, primary_yong_position=None, question_type=None):
    """
    完整动变分析。

    Args:
        hexagram: Hexagram对象
        wangshuai_results: 各爻旺衰分析结果
        primary_yong_position: 主用神爻位(可选, 供复合之动判定最终目标爻)
        question_type: 问事类型(可选, 供自占/代占分流)

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

    # 分析每个动爻。优先复用 Hexagram 内置索引, 避免重复扫描六爻。
    moving_lines = _get_moving_lines(hexagram)
    moving_analyses = {}
    for line in moving_lines:
        analysis = analyze_moving_line(line, month_zhi, day_zhi)
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
    san_he_ju = find_san_he_ju(hexagram, moving_lines)

    # 检查复合之动: 三合局优先, 否则看有用动爻间的连动相生/相克
    compound_movement = analyze_compound_movement(
        hexagram, moving_analyses, useful_moving, san_he_ju,
        primary_yong_position=primary_yong_position,
        question_type=question_type,
    )

    # 检查动爻间的交互作用
    interactions = {}
    if moving_lines:
        for line in hexagram.lines:
            interaction = check_dong_yao_interaction(line, moving_lines, moving_analyses)
            if interaction["受生"] or interaction["受克"]:
                interactions[line.position] = interaction

    # 检测暗动
    an_dong = detect_an_dong(hexagram, wangshuai_results, moving_lines)

    return {
        "moving_analyses": moving_analyses,
        "san_he_ju": san_he_ju,
        "compound_movement": compound_movement,
        "an_dong": an_dong,
        "useful_moving": useful_moving,
        "useless_moving": useless_moving,
        "interactions": interactions,
    }
