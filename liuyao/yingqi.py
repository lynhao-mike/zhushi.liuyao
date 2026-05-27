"""
应期推断模块 - Ying-Qi (Response Period) Estimation

根据用神的状态推断事情发生的时间。
包含21个标准应期公式, 速度修正, 远近筛选, 候选排序。
"""

from dataclasses import dataclass, field
from typing import List, Optional

from .data import (
    DI_ZHI, DI_ZHI_WU_XING,
    LIU_CHONG, LIU_HE, SAN_HE,
    JIN_SHEN, TUI_SHEN,
    WU_XING_SHENG, WU_XING_KE,
)


# 墓库表: 五行 -> 墓所在地支
WU_XING_MU = {
    "木": "未",
    "火": "戌",
    "金": "丑",
    "水": "辰",
    "土": "辰",
}

# 三刑分组
SAN_XING_GROUPS = [
    ("巳", "申", "寅"),
    ("丑", "未", "戌"),
    ("子", "卯"),
]


@dataclass
class YingqiCandidate:
    """应期候选结果"""
    di_zhi: str              # 应期目标地支
    timing_type: str         # day/month/year
    formula_id: int          # 公式编号 (1-21)
    formula_name: str        # 公式名称
    reasoning: str           # 推理说明
    priority: int = 0        # 排序优先级
    speed_modifier: str = ""  # accelerated/decelerated/空


def _get_he_zhi(zhi):
    """获取六合对象地支"""
    entry = LIU_HE.get(zhi)
    if entry:
        return entry[0]
    return ""


def _get_chong_zhi(zhi):
    """获取六冲对象地支"""
    return LIU_CHONG.get(zhi, "")


def _get_mu_zhi(zhi):
    """获取某地支五行的墓库地支"""
    wx = DI_ZHI_WU_XING.get(zhi, "")
    return WU_XING_MU.get(wx, "")


def _same_wx_zhis(zhi):
    """获取与该地支同五行的所有地支"""
    wx = DI_ZHI_WU_XING.get(zhi, "")
    return [z for z in DI_ZHI if DI_ZHI_WU_XING[z] == wx]


def _get_sheng_zhis(zhi):
    """获取生该地支五行的地支列表"""
    wx = DI_ZHI_WU_XING.get(zhi, "")
    sheng_wx_list = [w for w, t in WU_XING_SHENG.items() if t == wx]
    if not sheng_wx_list:
        return []
    sheng_wx = sheng_wx_list[0]
    return [z for z in DI_ZHI if DI_ZHI_WU_XING[z] == sheng_wx]


def _get_ke_zhis(zhi):
    """获取克该地支五行的地支列表"""
    wx = DI_ZHI_WU_XING.get(zhi, "")
    ke_wx_list = [w for w, t in WU_XING_KE.items() if t == wx]
    if not ke_wx_list:
        return []
    ke_wx = ke_wx_list[0]
    return [z for z in DI_ZHI if DI_ZHI_WU_XING[z] == ke_wx]


# ============================================================================
# 21 Timing Formulas
# ============================================================================


def formula_01_static(line_zhi, overall):
    """公式1: 静爻 - 旺逢冲, 衰逢值"""
    candidates = []
    if overall == "旺":
        chong = _get_chong_zhi(line_zhi)
        if chong:
            candidates.append(YingqiCandidate(
                di_zhi=chong, timing_type="day", formula_id=1,
                formula_name="旺静逢冲", reasoning=f"旺静爻逢冲即应, {line_zhi}旺待{chong}冲"
            ))
    else:
        candidates.append(YingqiCandidate(
            di_zhi=line_zhi, timing_type="day", formula_id=1,
            formula_name="衰静逢值", reasoning=f"衰静爻逢值即应, 待{line_zhi}值日/月"
        ))
    return candidates


def formula_02_moving(line_zhi):
    """公式2: 动爻 - 逢合, 逢值"""
    candidates = []
    he_zhi = _get_he_zhi(line_zhi)
    if he_zhi:
        candidates.append(YingqiCandidate(
            di_zhi=he_zhi, timing_type="day", formula_id=2,
            formula_name="动逢合", reasoning=f"动爻逢合即应, {line_zhi}合{he_zhi}"
        ))
    candidates.append(YingqiCandidate(
        di_zhi=line_zhi, timing_type="day", formula_id=2,
        formula_name="动逢值", reasoning=f"动爻逢值即应, 待{line_zhi}值日/月"
    ))
    return candidates


def formula_03_yue_po(line_zhi):
    """公式3: 月破爻 - 填实, 补破, 出月破"""
    candidates = []
    candidates.append(YingqiCandidate(
        di_zhi=line_zhi, timing_type="month", formula_id=3,
        formula_name="填实", reasoning=f"月破逢值填实, 待{line_zhi}月/日"
    ))
    he_zhi = _get_he_zhi(line_zhi)
    if he_zhi:
        candidates.append(YingqiCandidate(
            di_zhi=he_zhi, timing_type="month", formula_id=3,
            formula_name="补破", reasoning=f"月破补合, 待{he_zhi}合{line_zhi}"
        ))
    # 出月破: next month
    zhi_idx = DI_ZHI.index(line_zhi)
    next_zhi = DI_ZHI[(zhi_idx + 1) % 12]
    candidates.append(YingqiCandidate(
        di_zhi=next_zhi, timing_type="month", formula_id=3,
        formula_name="出月破", reasoning="过月即出破"
    ))
    return candidates


def formula_04_ri_chong(line_zhi):
    """公式4: 日冲爻 - 逢值(同地支)或次日"""
    candidates = []
    candidates.append(YingqiCandidate(
        di_zhi=line_zhi, timing_type="day", formula_id=4,
        formula_name="日冲逢值", reasoning=f"日冲之爻逢值即应, {line_zhi}日"
    ))
    zhi_idx = DI_ZHI.index(line_zhi)
    next_zhi = DI_ZHI[(zhi_idx + 1) % 12]
    candidates.append(YingqiCandidate(
        di_zhi=next_zhi, timing_type="day", formula_id=4,
        formula_name="日冲次日", reasoning=f"日冲次日即应"
    ))
    return candidates


def formula_05_xun_kong(line_zhi):
    """公式5: 旬空爻 - 填空(逢值), 冲空, 出空"""
    candidates = []
    candidates.append(YingqiCandidate(
        di_zhi=line_zhi, timing_type="day", formula_id=5,
        formula_name="填空", reasoning=f"旬空逢值填实, {line_zhi}日/月"
    ))
    chong = _get_chong_zhi(line_zhi)
    if chong:
        candidates.append(YingqiCandidate(
            di_zhi=chong, timing_type="day", formula_id=5,
            formula_name="冲空", reasoning=f"冲空则实, {chong}冲{line_zhi}"
        ))
    # 出空 marker - use line_zhi itself as proxy
    candidates.append(YingqiCandidate(
        di_zhi=line_zhi, timing_type="day", formula_id=5,
        formula_name="出空", reasoning="出旬之日"
    ))
    return candidates



def formula_06_yu_he_chong(line_zhi, is_yu_he=True):
    """公式6: 遇合逢两冲; 遇冲逢两合"""
    candidates = []
    if is_yu_he:
        # 遇合待冲: need 2 chongs
        chong = _get_chong_zhi(line_zhi)
        if chong:
            candidates.append(YingqiCandidate(
                di_zhi=chong, timing_type="day", formula_id=6,
                formula_name="遇合逢冲", reasoning=f"逢合之爻待冲解, {chong}冲开"
            ))
    else:
        # 遇冲待合: need 2 hes
        he_zhi = _get_he_zhi(line_zhi)
        if he_zhi:
            candidates.append(YingqiCandidate(
                di_zhi=he_zhi, timing_type="day", formula_id=6,
                formula_name="遇冲逢合", reasoning=f"逢冲之爻待合解, {he_zhi}合住"
            ))
    return candidates


def formula_07_dong_yue_he(line_zhi):
    """公式7: 动逢月合 - 三个月内"""
    candidates = []
    zhi_idx = DI_ZHI.index(line_zhi)
    for offset in range(1, 4):
        next_zhi = DI_ZHI[(zhi_idx + offset) % 12]
        candidates.append(YingqiCandidate(
            di_zhi=next_zhi, timing_type="month", formula_id=7,
            formula_name="动逢月合", reasoning=f"动逢月合三月内, {next_zhi}月"
        ))
    return candidates


def formula_08_single_attr(line_zhi):
    """公式8: 单属性爻 - 同五行地支"""
    candidates = []
    same_zhis = _same_wx_zhis(line_zhi)
    for z in same_zhis:
        if z != line_zhi:
            candidates.append(YingqiCandidate(
                di_zhi=z, timing_type="day", formula_id=8,
                formula_name="同五行", reasoning=f"同五行地支, {z}与{line_zhi}同属{DI_ZHI_WU_XING[line_zhi]}"
            ))
    return candidates


def formula_09_bian_yao(line_zhi, bian_zhi, has_hui_tou):
    """公式9: 变爻 - 无回头则逢值/逢冲; 有回头则逢值/逢合"""
    candidates = []
    if not has_hui_tou:
        candidates.append(YingqiCandidate(
            di_zhi=line_zhi, timing_type="day", formula_id=9,
            formula_name="变爻逢值", reasoning=f"变爻无回头, 本爻{line_zhi}逢值"
        ))
        chong = _get_chong_zhi(line_zhi)
        if chong:
            candidates.append(YingqiCandidate(
                di_zhi=chong, timing_type="day", formula_id=9,
                formula_name="变爻逢冲", reasoning=f"变爻无回头, {chong}冲{line_zhi}"
            ))
    else:
        candidates.append(YingqiCandidate(
            di_zhi=line_zhi, timing_type="day", formula_id=9,
            formula_name="变爻回头逢值", reasoning=f"变爻有回头, 本爻{line_zhi}逢值"
        ))
        he_zhi = _get_he_zhi(line_zhi)
        if he_zhi:
            candidates.append(YingqiCandidate(
                di_zhi=he_zhi, timing_type="day", formula_id=9,
                formula_name="变爻回头逢合", reasoning=f"变爻有回头, {he_zhi}合{line_zhi}"
            ))
    return candidates


def formula_10_hua_jin(line_zhi, bian_zhi):
    """公式10: 化进神 - 逢值(本), 逢合(本之合), 逢进(变)"""
    candidates = []
    candidates.append(YingqiCandidate(
        di_zhi=line_zhi, timing_type="day", formula_id=10,
        formula_name="进神逢值", reasoning=f"化进神本爻逢值, {line_zhi}"
    ))
    he_zhi = _get_he_zhi(line_zhi)
    if he_zhi:
        candidates.append(YingqiCandidate(
            di_zhi=he_zhi, timing_type="day", formula_id=10,
            formula_name="进神逢合", reasoning=f"化进神逢合, {he_zhi}合{line_zhi}"
        ))
    candidates.append(YingqiCandidate(
        di_zhi=bian_zhi, timing_type="day", formula_id=10,
        formula_name="逢进", reasoning=f"化进神逢进位, {bian_zhi}"
    ))
    return candidates


def formula_11_hua_tui(line_zhi, bian_zhi):
    """公式11: 化退神 - 逢两冲(本+变之冲), 逢退值(变)"""
    candidates = []
    chong_ben = _get_chong_zhi(line_zhi)
    chong_bian = _get_chong_zhi(bian_zhi)
    if chong_ben:
        candidates.append(YingqiCandidate(
            di_zhi=chong_ben, timing_type="day", formula_id=11,
            formula_name="退神冲本", reasoning=f"化退神逢冲本爻, {chong_ben}冲{line_zhi}"
        ))
    if chong_bian:
        candidates.append(YingqiCandidate(
            di_zhi=chong_bian, timing_type="day", formula_id=11,
            formula_name="退神冲变", reasoning=f"化退神逢冲变爻, {chong_bian}冲{bian_zhi}"
        ))
    candidates.append(YingqiCandidate(
        di_zhi=bian_zhi, timing_type="day", formula_id=11,
        formula_name="逢退值", reasoning=f"化退神逢退位值, {bian_zhi}"
    ))
    return candidates



def formula_12_san_he(san_he_info, is_internal=True):
    """公式12: 三合局 - 内合=破(冲成员), 外合=补(填缺)"""
    candidates = []
    if is_internal:
        # 内部三合已成, 应期为破局(冲某成员)
        for member in san_he_info.get("members", []):
            chong = _get_chong_zhi(member)
            if chong:
                candidates.append(YingqiCandidate(
                    di_zhi=chong, timing_type="month", formula_id=12,
                    formula_name="三合破局", reasoning=f"三合局内成待破, {chong}冲{member}"
                ))
    else:
        # 外部三合缺一员, 应期为补全(填缺)
        missing = san_he_info.get("missing", "")
        if missing:
            candidates.append(YingqiCandidate(
                di_zhi=missing, timing_type="month", formula_id=12,
                formula_name="三合补全", reasoning=f"三合局待补全, {missing}到位"
            ))
    return candidates


def formula_13_san_mu(line_zhi):
    """公式13: 入墓 - 冲墓, 冲爻, 出墓"""
    candidates = []
    mu_zhi = _get_mu_zhi(line_zhi)
    if mu_zhi:
        chong_mu = _get_chong_zhi(mu_zhi)
        if chong_mu:
            candidates.append(YingqiCandidate(
                di_zhi=chong_mu, timing_type="day", formula_id=13,
                formula_name="冲墓", reasoning=f"{line_zhi}入墓{mu_zhi}, {chong_mu}冲开墓库"
            ))
        chong_yao = _get_chong_zhi(line_zhi)
        if chong_yao:
            candidates.append(YingqiCandidate(
                di_zhi=chong_yao, timing_type="day", formula_id=13,
                formula_name="冲爻出墓", reasoning=f"冲{line_zhi}出墓, {chong_yao}"
            ))
        candidates.append(YingqiCandidate(
            di_zhi=mu_zhi, timing_type="day", formula_id=13,
            formula_name="出墓", reasoning=f"出墓之期, {mu_zhi}"
        ))
    return candidates


def formula_14_san_xing(line_zhi, hexagram_zhis):
    """公式14: 三刑 - 填缺元素"""
    candidates = []
    for group in SAN_XING_GROUPS:
        if line_zhi in group:
            present = [z for z in group if z in hexagram_zhis]
            missing = [z for z in group if z not in hexagram_zhis and z != line_zhi]
            for m in missing:
                candidates.append(YingqiCandidate(
                    di_zhi=m, timing_type="month", formula_id=14,
                    formula_name="三刑补缺", reasoning=f"三刑({'/'.join(group)})缺{m}, 待{m}到位"
                ))
            break
    return candidates


def formula_15_fan_yin(line_zhi):
    """公式15: 反吟 - 逢值期"""
    candidates = []
    candidates.append(YingqiCandidate(
        di_zhi=line_zhi, timing_type="month", formula_id=15,
        formula_name="反吟逢值", reasoning=f"反吟之爻逢值即应, {line_zhi}"
    ))
    return candidates


def formula_16_fu_yin(line_zhi, is_target=True):
    """公式16: 伏吟 - 目标爻逢值/逢冲; 非目标逢值/逢合"""
    candidates = []
    if is_target:
        candidates.append(YingqiCandidate(
            di_zhi=line_zhi, timing_type="day", formula_id=16,
            formula_name="伏吟目标逢值", reasoning=f"伏吟目标爻逢值, {line_zhi}"
        ))
        chong = _get_chong_zhi(line_zhi)
        if chong:
            candidates.append(YingqiCandidate(
                di_zhi=chong, timing_type="day", formula_id=16,
                formula_name="伏吟目标逢冲", reasoning=f"伏吟目标爻逢冲, {chong}冲{line_zhi}"
            ))
    else:
        candidates.append(YingqiCandidate(
            di_zhi=line_zhi, timing_type="day", formula_id=16,
            formula_name="伏吟非目标逢值", reasoning=f"伏吟非目标逢值, {line_zhi}"
        ))
        he_zhi = _get_he_zhi(line_zhi)
        if he_zhi:
            candidates.append(YingqiCandidate(
                di_zhi=he_zhi, timing_type="day", formula_id=16,
                formula_name="伏吟非目标逢合", reasoning=f"伏吟非目标逢合, {he_zhi}合{line_zhi}"
            ))
    return candidates


def formula_17_fu_shen(fu_zhi, fei_zhi):
    """公式17: 伏神 - 逢值/逢合伏神, 或冲飞"""
    candidates = []
    candidates.append(YingqiCandidate(
        di_zhi=fu_zhi, timing_type="day", formula_id=17,
        formula_name="伏神逢值", reasoning=f"伏神逢值出现, {fu_zhi}"
    ))
    he_zhi = _get_he_zhi(fu_zhi)
    if he_zhi:
        candidates.append(YingqiCandidate(
            di_zhi=he_zhi, timing_type="day", formula_id=17,
            formula_name="伏神逢合", reasoning=f"伏神逢合出现, {he_zhi}合{fu_zhi}"
        ))
    chong_fei = _get_chong_zhi(fei_zhi)
    if chong_fei:
        candidates.append(YingqiCandidate(
            di_zhi=chong_fei, timing_type="day", formula_id=17,
            formula_name="冲飞露伏", reasoning=f"冲飞露伏, {chong_fei}冲走飞神{fei_zhi}"
        ))
    return candidates


def formula_18_shou_ke(line_zhi, ke_source_zhi):
    """公式18: 吉用受克 - 等克源被冲"""
    candidates = []
    chong_source = _get_chong_zhi(ke_source_zhi)
    if chong_source:
        candidates.append(YingqiCandidate(
            di_zhi=chong_source, timing_type="day", formula_id=18,
            formula_name="冲去克源", reasoning=f"用神受克, 待{chong_source}冲去克源{ke_source_zhi}"
        ))
    return candidates


def formula_19_shou_sheng(line_zhi, sheng_source_zhi):
    """公式19: 凶用受生 - 等生源被冲"""
    candidates = []
    chong_source = _get_chong_zhi(sheng_source_zhi)
    if chong_source:
        candidates.append(YingqiCandidate(
            di_zhi=chong_source, timing_type="day", formula_id=19,
            formula_name="冲去生源", reasoning=f"忌神受生, 待{chong_source}冲去生源{sheng_source_zhi}"
        ))
    return candidates


def formula_20_guo_wang(line_zhi):
    """公式20: 实际过旺 - 逢墓或逢克期"""
    candidates = []
    mu_zhi = _get_mu_zhi(line_zhi)
    if mu_zhi:
        candidates.append(YingqiCandidate(
            di_zhi=mu_zhi, timing_type="month", formula_id=20,
            formula_name="过旺逢墓", reasoning=f"过旺入墓, {mu_zhi}为{line_zhi}之墓"
        ))
    ke_zhis = _get_ke_zhis(line_zhi)
    if ke_zhis:
        candidates.append(YingqiCandidate(
            di_zhi=ke_zhis[0], timing_type="month", formula_id=20,
            formula_name="过旺逢克", reasoning=f"过旺逢克制, {ke_zhis[0]}克{line_zhi}"
        ))
    return candidates


def formula_21_duo_xian(line_zhi):
    """公式21: 用神多现 - 逢墓期(墓收纳)"""
    candidates = []
    mu_zhi = _get_mu_zhi(line_zhi)
    if mu_zhi:
        candidates.append(YingqiCandidate(
            di_zhi=mu_zhi, timing_type="month", formula_id=21,
            formula_name="多现逢墓", reasoning=f"用神多现以墓收之, {mu_zhi}为{line_zhi}之墓"
        ))
    return candidates



# ============================================================================
# Speed Modifiers
# ============================================================================


def detect_speed_modifiers(dongbian_results, hexagram=None):
    """
    检测速度修正因素。

    Returns:
        str: 'accelerated' / 'decelerated' / ''
    """
    # Acceleration: an_dong present or gua-bian is liu-chong
    an_dong = dongbian_results.get("an_dong", [])
    if an_dong:
        return "accelerated"

    # Check if bian_gua is a pure hexagram (liu-chong pattern)
    if hexagram:
        bian_name = getattr(hexagram, "bian_gua_name", "")
        # Six pure hexagrams that indicate self-clash
        chong_gua_names = [
            "乾为天", "坤为地", "震为雷", "巽为风",
            "坎为水", "离为火", "艮为山", "兑为泽"
        ]
        if bian_name in chong_gua_names:
            return "accelerated"

    # Deceleration: san_he_ju present
    san_he = dongbian_results.get("san_he_ju", [])
    if san_he:
        return "decelerated"

    return ""


# ============================================================================
# Candidate Ranking
# ============================================================================


def rank_yingqi_candidates(candidates, current_month_zhi=None, current_day_zhi=None):
    """
    对应期候选排序。
    原则:
    1. 同一地支出现频率越高, 优先级越高
    2. 距离当前月/日越近(按DI_ZHI顺序), 优先级越高
    3. 相邻地支对有加成

    Args:
        candidates: List[YingqiCandidate]
        current_month_zhi: 当前月支 (用于计算距离)
        current_day_zhi: 当前日支 (用于计算距离)

    Returns:
        List[YingqiCandidate]: 排序后的候选列表
    """
    if not candidates:
        return []

    # Count frequency of each di_zhi
    freq = {}
    for c in candidates:
        freq[c.di_zhi] = freq.get(c.di_zhi, 0) + 1

    # Calculate distance from current position
    ref_zhi = current_month_zhi or current_day_zhi or "子"
    ref_idx = DI_ZHI.index(ref_zhi)

    # Collect all di_zhi present
    all_zhis = set(c.di_zhi for c in candidates)

    # Adjacent bonus: if both zhi and its neighbor appear
    adjacent_bonus = set()
    for z in all_zhis:
        z_idx = DI_ZHI.index(z)
        next_z = DI_ZHI[(z_idx + 1) % 12]
        prev_z = DI_ZHI[(z_idx - 1) % 12]
        if next_z in all_zhis:
            adjacent_bonus.add(z)
            adjacent_bonus.add(next_z)
        if prev_z in all_zhis:
            adjacent_bonus.add(z)
            adjacent_bonus.add(prev_z)

    # Score each candidate
    for c in candidates:
        score = 0
        # Frequency bonus (x10)
        score += freq.get(c.di_zhi, 0) * 10
        # Proximity bonus (closer = higher, max 12)
        c_idx = DI_ZHI.index(c.di_zhi)
        distance = (c_idx - ref_idx) % 12
        if distance == 0:
            distance = 12  # same position = furthest (full cycle)
        score += (12 - distance)
        # Adjacent bonus
        if c.di_zhi in adjacent_bonus:
            score += 5
        c.priority = score

    # Sort by priority descending
    return sorted(candidates, key=lambda x: x.priority, reverse=True)


# ============================================================================
# Main Functions (backward compatible)
# ============================================================================


def estimate_yingqi(line, wangshuai_result, moving_analysis=None):
    """
    推断单爻的应期候选 (向后兼容接口)。

    Args:
        line: YaoLine对象 (用神爻)
        wangshuai_result: 该爻的旺衰分析结果
        moving_analysis: 该爻的动变分析结果 (如果是动爻)

    Returns:
        list[str]: 应期候选说明列表
    """
    candidates = estimate_yingqi_candidates(line, wangshuai_result, moving_analysis)
    # Convert to legacy string format
    return [f"{c.formula_name}: {c.di_zhi}日/月({c.reasoning})" for c in candidates]


def estimate_yingqi_candidates(line, wangshuai_result, moving_analysis=None):
    """
    推断单爻的应期候选 (返回YingqiCandidate对象)。

    Args:
        line: YaoLine对象 (用神爻)
        wangshuai_result: 该爻的旺衰分析结果
        moving_analysis: 该爻的动变分析结果 (如果是动爻)

    Returns:
        List[YingqiCandidate]: 应期候选列表
    """
    candidates = []
    line_zhi = line.di_zhi
    overall = wangshuai_result["overall"]
    is_yue_po = "月破" in wangshuai_result.get("month_shuai", [])

    # Formula 5: Xun-kong
    if line.is_xun_kong:
        candidates.extend(formula_05_xun_kong(line_zhi))
        return candidates

    # Formula 3: Yue-po
    if is_yue_po:
        candidates.extend(formula_03_yue_po(line_zhi))
        return candidates

    # Moving line formulas
    if line.is_moving and moving_analysis:
        bian_zhi = moving_analysis.get("bian_zhi", "")

        # Formula 10: Hua-jin-shen
        if "化进神" in moving_analysis.get("趋旺", []):
            candidates.extend(formula_10_hua_jin(line_zhi, bian_zhi))
            return candidates

        # Formula 11: Hua-tui-shen
        if "化退神" in moving_analysis.get("趋衰", []):
            candidates.extend(formula_11_hua_tui(line_zhi, bian_zhi))
            return candidates

        # Formula 9: Bian-yao with hui-tou
        has_hui_tou = ("回头生" in moving_analysis.get("趋旺", []) or
                       "回头克" in moving_analysis.get("趋衰", []))
        if has_hui_tou and bian_zhi:
            candidates.extend(formula_09_bian_yao(line_zhi, bian_zhi, has_hui_tou))
            return candidates

        # Formula 2: General moving line
        candidates.extend(formula_02_moving(line_zhi))
        return candidates

    # Formula 1: Static line
    candidates.extend(formula_01_static(line_zhi, overall))

    # Supplementary: sheng formulas for shuai static
    if overall != "旺":
        sheng_zhis = _get_sheng_zhis(line_zhi)
        if sheng_zhis:
            line_wx = DI_ZHI_WU_XING[line_zhi]
            sheng_wx = DI_ZHI_WU_XING[sheng_zhis[0]]
            for sz in sheng_zhis[:2]:
                candidates.append(YingqiCandidate(
                    di_zhi=sz, timing_type="day", formula_id=8,
                    formula_name="逢生", reasoning=f"{sheng_wx}生{line_wx}, {sz}日/月"
                ))

    return candidates



def analyze_yingqi(hexagram, yong_shen_lines, wangshuai_results, dongbian_results,
                   time_scope=None):
    """
    分析用神的应期。

    Args:
        hexagram: Hexagram对象
        yong_shen_lines: 用神爻列表
        wangshuai_results: 所有爻的旺衰结果
        dongbian_results: 动变分析结果
        time_scope: 时间范围筛选 ('short'/'medium'/'long'/None)
            short: 优先日级, 排除年级
            medium: 优先月级
            long: 优先年级, 排除日级短暂候选

    Returns:
        list[dict]: 每个用神爻的应期候选
    """
    results = []
    moving_analyses = dongbian_results.get("moving_analyses", {})

    # Detect speed modifiers
    speed = detect_speed_modifiers(dongbian_results, hexagram)

    for line in yong_shen_lines:
        ws = wangshuai_results[line.position - 1]
        ma = moving_analyses.get(line.position)

        # Get structured candidates
        raw_candidates = estimate_yingqi_candidates(line, ws, ma)

        # Apply additional formulas based on context
        _apply_contextual_formulas(
            raw_candidates, line, ws, ma, hexagram, dongbian_results
        )

        # Apply speed modifier
        if speed:
            for c in raw_candidates:
                c.speed_modifier = speed

        # Filter by time_scope
        filtered = _filter_by_scope(raw_candidates, time_scope)

        # Rank
        month_zhi = hexagram.gan_zhi.get("month_zhi", "子")
        day_zhi = hexagram.gan_zhi.get("day_zhi", "子")
        ranked = rank_yingqi_candidates(filtered, month_zhi, day_zhi)

        # Build legacy-compatible result
        legacy_candidates = []
        for c in ranked:
            desc = f"{c.formula_name}: {c.di_zhi}日/月({c.reasoning})"
            if c.speed_modifier:
                speed_label = "加速" if c.speed_modifier == "accelerated" else "减速"
                desc += f" [{speed_label}]"
            legacy_candidates.append(desc)

        results.append({
            "position": line.position,
            "di_zhi": line.di_zhi,
            "liu_qin": line.liu_qin,
            "candidates": legacy_candidates,
            "ranked_candidates": ranked,
        })

    return results


def _apply_contextual_formulas(candidates, line, ws, ma, hexagram, dongbian_results):
    """根据卦局上下文追加额外公式候选"""
    line_zhi = line.di_zhi

    # Formula 4: Ri-chong detection
    day_zhi = hexagram.gan_zhi.get("day_zhi", "")
    if LIU_CHONG.get(day_zhi) == line_zhi:
        candidates.extend(formula_04_ri_chong(line_zhi))

    # Formula 6: Yu-he / Yu-chong
    month_zhi = hexagram.gan_zhi.get("month_zhi", "")
    he_partner = _get_he_zhi(line_zhi)
    if he_partner == month_zhi or he_partner == day_zhi:
        # Line is in harmony with month/day -> yu-he, need chong to break
        candidates.extend(formula_06_yu_he_chong(line_zhi, is_yu_he=True))
    chong_partner = _get_chong_zhi(line_zhi)
    if chong_partner == month_zhi or chong_partner == day_zhi:
        # Line is clashed by month/day -> yu-chong, need he to resolve
        candidates.extend(formula_06_yu_he_chong(line_zhi, is_yu_he=False))

    # Formula 12: San-he-ju
    san_he = dongbian_results.get("san_he_ju", [])
    for sh in san_he:
        candidates.extend(formula_12_san_he(sh, is_internal=True))

    # Formula 13: Check if line is in mu (tomb)
    mu_zhi = _get_mu_zhi(line_zhi)
    if mu_zhi:
        # Check if mu_zhi is present in the hexagram (indicating entombment)
        hex_zhis = [l.di_zhi for l in hexagram.lines]
        if mu_zhi in hex_zhis or mu_zhi == month_zhi or mu_zhi == day_zhi:
            candidates.extend(formula_13_san_mu(line_zhi))

    # Formula 14: San-xing
    hex_zhis = [l.di_zhi for l in hexagram.lines]
    for group in SAN_XING_GROUPS:
        if line_zhi in group:
            present_count = sum(1 for z in group if z in hex_zhis)
            if present_count >= 2:
                candidates.extend(formula_14_san_xing(line_zhi, hex_zhis))
            break

    # Formula 20: Guo-wang (too prosperous)
    overall = ws["overall"]
    if overall == "旺":
        month_wang = ws.get("month_wang", [])
        day_wang = ws.get("day_wang", [])
        # If both month and day strengthen it, it may be too prosperous
        if len(month_wang) >= 2 and len(day_wang) >= 1:
            candidates.extend(formula_20_guo_wang(line_zhi))

    # Formula 21: Yong-shen-duo-xian (use-spirit appears multiple times)
    # detected externally based on yong_shen_lines count


def _filter_by_scope(candidates, time_scope):
    """根据时间范围筛选候选"""
    if not time_scope:
        return candidates

    if time_scope == "short":
        # Prioritize day-level, exclude year-level
        filtered = [c for c in candidates if c.timing_type != "year"]
        if not filtered:
            filtered = candidates
        # Boost day-level priority
        for c in filtered:
            if c.timing_type == "day":
                c.priority += 5
        return filtered

    elif time_scope == "medium":
        # Prioritize month-level
        for c in candidates:
            if c.timing_type == "month":
                c.priority += 5
        return candidates

    elif time_scope == "long":
        # Prioritize year-level, exclude transient day-level
        filtered = [c for c in candidates if c.timing_type != "day"]
        if not filtered:
            filtered = candidates
        for c in filtered:
            if c.timing_type == "year":
                c.priority += 5
        return filtered

    return candidates

