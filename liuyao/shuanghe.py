"""
双合卦分析模块 - Shuang-He Gua (Dual-Core Hexagram) Analysis

当问卦涉及"特指"(te_zhi)或"嫁接"(jia_jie)类问题时,
应爻作为"半个用神"参与判断, 需同时分析用神与应爻的动态关系。

主要功能:
1. 识别双合卦类型 (特指/嫁接/普通)
2. 分析应爻参与度 (无关/对比/关联)
3. 双核吉凶判断 (当应爻参与时)
"""

from .data import (
    DI_ZHI_WU_XING,
    WU_XING_SHENG, WU_XING_KE,
    LIU_CHONG,
)
from .jixiong import find_ying_line, find_yong_shen_lines, find_shi_line


# 特指关键词: 暗示问卦针对特定对象
TE_ZHI_KEYWORDS = [
    "这家", "这个", "那家", "那个", "此",
    "指定", "特定", "具体",
]

# 嫁接关键词: 暗示问卦涉及合作对象的利益
JIA_JIE_KEYWORDS = [
    "合作", "合伙", "与他", "跟他", "和他",
    "对方", "他能", "她能",
]


def detect_shuanghe_type(question_type, question_desc=""):
    """
    识别问卦是否为双合卦类型。

    双合卦分两种:
    - te_zhi (特指): 问"能否在这家公司成功", 应爻代表该特定对象
    - jia_jie (嫁接): 问"与此人合作能否获利", 应爻代表合作方

    Args:
        question_type: 问事类型 (如 "cai", "te_zhi_cai", "jia_jie_cai")
        question_desc: 问事描述文本

    Returns:
        str: "te_zhi" / "jia_jie" / "normal"
    """
    # 从 question_type 前缀判断
    if question_type.startswith("te_zhi_"):
        return "te_zhi"
    if question_type.startswith("jia_jie_"):
        return "jia_jie"

    # 从描述文本判断
    if question_desc:
        for kw in TE_ZHI_KEYWORDS:
            if kw in question_desc:
                return "te_zhi"
        for kw in JIA_JIE_KEYWORDS:
            if kw in question_desc:
                return "jia_jie"

    return "normal"


def analyze_ying_yao_role(hexagram, yong_shen_lines, dongbian_results, wangshuai_results):
    """
    分析应爻的参与程度。

    分类:
    - wu_guan (无关): 应爻与动变/用神无任何关系, 不干扰判断
    - dui_bi (对比): 应爻与动变/用神形成比较关系(同支/同行/冲), 干扰判断
    - guan_lian (关联): 应爻自身发动, 或动爻仅指向应爻, 或应爻+用神形成联动, 干扰判断

    Args:
        hexagram: Hexagram对象
        yong_shen_lines: 用神爻列表
        dongbian_results: 动变分析结果
        wangshuai_results: 旺衰分析结果

    Returns:
        dict: {
            "role": "wu_guan" / "dui_bi" / "guan_lian",
            "details": str  # 说明
        }
    """
    ying_line = find_ying_line(hexagram)
    if not ying_line:
        return {"role": "wu_guan", "details": "未找到应爻"}

    ying_zhi = ying_line.di_zhi
    ying_wx = DI_ZHI_WU_XING[ying_zhi]

    moving_analyses = dongbian_results.get("moving_analyses", {})
    interactions = dongbian_results.get("interactions", {})

    # =========================================================================
    # 检查 guan_lian (关联): 应爻自身发动
    # =========================================================================
    if ying_line.is_moving:
        return {
            "role": "guan_lian",
            "details": f"应爻({ying_zhi})自身发动, 深度参与卦局",
        }

    # 检查动爻是否仅指向应爻(而非用神)
    # 如果有动爻, 检查其交互中是否只作用于应爻位置
    moving_positions = [pos for pos, ma in moving_analyses.items() if not ma.get("is_useless", False)]
    if moving_positions:
        # 统计动爻对应爻和用神的作用
        yong_positions = {yl.position for yl in yong_shen_lines}
        targets_ying = False
        targets_yong = False

        for pos in moving_positions:
            moving_line = hexagram.lines[pos - 1]
            moving_wx = DI_ZHI_WU_XING[moving_line.di_zhi]
            # 动爻生/克应爻
            if (WU_XING_SHENG[moving_wx] == ying_wx or
                    WU_XING_KE[moving_wx] == ying_wx):
                targets_ying = True
            # 动爻生/克用神
            for yp in yong_positions:
                yong_wx = DI_ZHI_WU_XING[hexagram.lines[yp - 1].di_zhi]
                if (WU_XING_SHENG[moving_wx] == yong_wx or
                        WU_XING_KE[moving_wx] == yong_wx):
                    targets_yong = True

        if targets_ying and not targets_yong:
            return {
                "role": "guan_lian",
                "details": f"动爻仅指向应爻({ying_zhi}), 不作用于用神",
            }

    # =========================================================================
    # 检查 dui_bi (对比): 应爻与用神/动变形成比较关系
    # =========================================================================
    for yl in yong_shen_lines:
        yong_zhi = yl.di_zhi
        yong_wx = DI_ZHI_WU_XING[yong_zhi]

        # 同地支
        if ying_zhi == yong_zhi:
            return {
                "role": "dui_bi",
                "details": f"应爻({ying_zhi})与用神同地支, 形成对比",
            }
        # 同五行
        if ying_wx == yong_wx:
            return {
                "role": "dui_bi",
                "details": f"应爻({ying_zhi}{ying_wx})与用神({yong_zhi}{yong_wx})同五行, 形成对比",
            }
        # 六冲关系
        if LIU_CHONG.get(ying_zhi) == yong_zhi:
            return {
                "role": "dui_bi",
                "details": f"应爻({ying_zhi})与用神({yong_zhi})相冲, 形成对比",
            }

    # 检查应爻与动变爻的比较关系
    for pos, ma in moving_analyses.items():
        bian_zhi = ma.get("bian_zhi", "")
        if not bian_zhi:
            continue
        bian_wx = DI_ZHI_WU_XING.get(bian_zhi, "")
        # 变爻与应爻同支或同行
        if ying_zhi == bian_zhi:
            return {
                "role": "dui_bi",
                "details": f"变爻({bian_zhi})与应爻({ying_zhi})同地支, 形成对比",
            }
        if bian_wx and ying_wx == bian_wx:
            return {
                "role": "dui_bi",
                "details": f"变爻({bian_zhi}{bian_wx})与应爻({ying_zhi}{ying_wx})同五行, 形成对比",
            }
        if LIU_CHONG.get(ying_zhi) == bian_zhi:
            return {
                "role": "dui_bi",
                "details": f"变爻({bian_zhi})与应爻({ying_zhi})相冲, 形成对比",
            }

    # =========================================================================
    # 无关
    # =========================================================================
    return {
        "role": "wu_guan",
        "details": f"应爻({ying_zhi})与动变/用神无直接关系",
    }


def judge_shuanghe_jixiong(hexagram, yong_shen_liu_qin, ying_role,
                           wangshuai_results, dongbian_results, question_type):
    """
    双核吉凶判断。

    当应爻参与度为 dui_bi 或 guan_lian 时, 需要分析:
    - 动爻指向用神多还是指向应爻多
    - 若指向应爻更多, 则成功可能关联"替代目标"而非"指定目标"
    - te_zhi_match 表示结果是否与指定目标一致

    Args:
        hexagram: Hexagram对象
        yong_shen_liu_qin: 用神六亲
        ying_role: analyze_ying_yao_role()的返回结果
        wangshuai_results: 旺衰分析结果
        dongbian_results: 动变分析结果
        question_type: 问事类型

    Returns:
        dict: {
            "te_zhi_match": bool,  # 是否与指定目标一致
            "ying_strength": str,  # 应爻强度 ("强"/"弱"/"平")
            "explanation": str,    # 说明
        }
    """
    ying_line = find_ying_line(hexagram)
    yong_lines = find_yong_shen_lines(hexagram, yong_shen_liu_qin)

    if not ying_line or not yong_lines:
        return {
            "te_zhi_match": True,
            "ying_strength": "平",
            "explanation": "未找到应爻或用神, 按常规判断",
        }

    ying_zhi = ying_line.di_zhi
    ying_wx = DI_ZHI_WU_XING[ying_zhi]

    # 应爻旺衰
    ying_ws = wangshuai_results[ying_line.position - 1]
    ying_overall = ying_ws["overall"]

    # 用神旺衰(取主用神)
    primary_yong = yong_lines[0]
    primary_yong_ws = wangshuai_results[primary_yong.position - 1]
    for i, yl in enumerate(yong_lines):
        if yl.is_moving:
            primary_yong = yl
            primary_yong_ws = wangshuai_results[yl.position - 1]
            break

    yong_zhi = primary_yong.di_zhi
    yong_wx = DI_ZHI_WU_XING[yong_zhi]
    yong_overall = primary_yong_ws["overall"]

    # 统计动爻对应爻和用神的作用力
    moving_analyses = dongbian_results.get("moving_analyses", {})
    ying_score = 0  # 动爻指向应爻的计数
    yong_score = 0  # 动爻指向用神的计数

    for pos, ma in moving_analyses.items():
        if ma.get("is_useless", False):
            continue
        moving_line = hexagram.lines[pos - 1]
        moving_wx = DI_ZHI_WU_XING[moving_line.di_zhi]

        # 对应爻的作用
        if WU_XING_SHENG[moving_wx] == ying_wx or WU_XING_KE[moving_wx] == ying_wx:
            ying_score += 1
        if moving_line.di_zhi == ying_zhi:
            ying_score += 1

        # 对用神的作用
        if WU_XING_SHENG[moving_wx] == yong_wx or WU_XING_KE[moving_wx] == yong_wx:
            yong_score += 1
        if moving_line.di_zhi == yong_zhi:
            yong_score += 1

    # 应爻自身发动额外加分
    if ying_line.is_moving:
        ying_score += 2

    # 确定应爻强度
    if ying_overall == "旺":
        ying_strength = "强"
    elif ying_overall == "衰":
        ying_strength = "弱"
    else:
        ying_strength = "平"

    # 判断 te_zhi_match
    # 当动爻更多指向应爻时, 结果可能偏离指定目标
    if ying_score > yong_score:
        te_zhi_match = False
        explanation = (
            f"动爻指向应爻({ying_zhi})多于用神({yong_zhi}), "
            f"应爻{ying_strength}, "
            f"成功可能关联替代目标而非指定目标"
        )
    elif ying_score == yong_score and ying_strength == "强":
        te_zhi_match = False
        explanation = (
            f"动爻对应爻({ying_zhi})和用神({yong_zhi})作用均等, "
            f"但应爻旺强, 结果可能偏向替代目标"
        )
    else:
        te_zhi_match = True
        explanation = (
            f"动爻指向用神({yong_zhi})多于应爻({ying_zhi}), "
            f"结果与指定目标一致"
        )

    return {
        "te_zhi_match": te_zhi_match,
        "ying_strength": ying_strength,
        "explanation": explanation,
    }
