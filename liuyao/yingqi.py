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
    SAN_HE, SAN_HE_BY_ZHI,
    JIN_SHEN, TUI_SHEN,
    WU_XING_SHENG, WU_XING_KE,
    get_chang_sheng,
)


# ============================================================================
# Event Duration Classification
# ============================================================================

def classify_event_duration(question_type):
    """
    根据问事类型判断事件持续期。

    Args:
        question_type: 问事类型字符串

    Returns:
        str: "short", "medium", or "long"
    """
    short_types = {"bing"}
    medium_types = {"cai", "guan", "hun_male", "hun_female",
                    "kaoshi", "xingRen", "youHuan", "other", "zinv"}
    if question_type in short_types:
        return "short"
    if question_type in medium_types:
        return "medium"
    return "medium"


# ============================================================================
# Yuan Shen Identification
# ============================================================================

def identify_yuan_shen(yong_shen_liu_qin):
    """
    识别元神六亲(生用神的六亲)。

    Args:
        yong_shen_liu_qin: 用神六亲名称

    Returns:
        str: 元神六亲名称
    """
    yuan_shen_map = {
        "妻财": "子孙",
        "官鬼": "妻财",
        "父母": "官鬼",
        "子孙": "兄弟",
        "兄弟": "父母",
    }
    return yuan_shen_map.get(yong_shen_liu_qin, "")


# ============================================================================
# Andong (暗动) Timing
# ============================================================================

def estimate_andong_yingqi(line, an_dong_info, hexagram):
    """
    推断暗动爻的应期。

    Rules:
    1. 冲中逢值逢合 - 暗动爻逢值或逢合时应期
    2. 顺时而应 - 下一地支顺序
    3. 冲空即时生效 - 旬空被冲则即时应期

    Args:
        line: YaoLine对象
        an_dong_info: 暗动信息 dict (from dongbian an_dong list)
        hexagram: Hexagram对象

    Returns:
        list[dict]: 应期候选 [{"timing": str, "formula": str, "confidence": int}]
    """
    candidates = []
    line_zhi = line.di_zhi
    reason = an_dong_info.get("reason", "")

    # Rule 3: 冲空即时生效
    if "旬空" in reason:
        candidates.append({
            "timing": "即时(当日或次日)",
            "formula": "冲空即时生效",
            "confidence": 90,
        })
        return candidates

    # Rule 1: 逢值逢合
    candidates.append({
        "timing": f"{line_zhi}日/月(逢值)",
        "formula": "暗动逢值",
        "confidence": 70,
    })
    if line_zhi in LIU_HE:
        he_zhi = LIU_HE[line_zhi][0]
        candidates.append({
            "timing": f"{he_zhi}日/月(逢合)",
            "formula": "暗动逢合",
            "confidence": 65,
        })

    # Rule 2: 顺时而应
    zhi_idx = DI_ZHI.index(line_zhi)
    next_zhi = DI_ZHI[(zhi_idx + 1) % 12]
    candidates.append({
        "timing": f"{next_zhi}日/月(顺时而应)",
        "formula": "顺时而应",
        "confidence": 50,
    })

    return candidates


# ============================================================================
# Monthly Timing (月令应期)
# ============================================================================

def estimate_yueling_yingqi(line, hexagram, wangshuai_result):
    """
    推断月令相关应期。

    Rules:
    1. 临月建: 本月可能应期
    2. 月合: 三个月内应期

    Args:
        line: YaoLine对象
        hexagram: Hexagram对象
        wangshuai_result: 旺衰分析结果

    Returns:
        list[dict]: 应期候选
    """
    candidates = []
    line_zhi = line.di_zhi
    month_zhi = hexagram.gan_zhi["month_zhi"]

    # Rule 1: 临月建
    if line_zhi == month_zhi:
        candidates.append({
            "timing": "本月",
            "formula": "临月建",
            "confidence": 75,
        })

    # Rule 2: 月合
    if line_zhi in LIU_HE:
        he_zhi, _ = LIU_HE[line_zhi]
        if he_zhi == month_zhi:
            month_idx = DI_ZHI.index(month_zhi)
            future_months = []
            for offset in range(1, 4):
                future_months.append(DI_ZHI[(month_idx + offset) % 12])
            candidates.append({
                "timing": f"三月内({'/'.join(future_months)})",
                "formula": "月合数后三月",
                "confidence": 60,
            })

    return candidates


# ============================================================================
# Daily Timing (日令应期)
# ============================================================================

def estimate_riling_yingqi(line, hexagram, wangshuai_result, event_duration):
    """
    推断日令相关应期。

    Rules:
    - Short events: day branch cycles matter
    - Medium events: month branch cycles matter

    Args:
        line: YaoLine对象
        hexagram: Hexagram对象
        wangshuai_result: 旺衰分析结果
        event_duration: 事件持续期 ("short"/"medium"/"long")

    Returns:
        list[dict]: 应期候选
    """
    candidates = []
    line_zhi = line.di_zhi
    day_zhi = hexagram.gan_zhi["day_zhi"]
    month_zhi = hexagram.gan_zhi["month_zhi"]

    if event_duration == "short":
        # 短事日转月不转: 日支周期为主
        if line_zhi == day_zhi:
            candidates.append({
                "timing": "今日(临日令)",
                "formula": "短事临日令",
                "confidence": 80,
            })
        else:
            chong_zhi = LIU_CHONG.get(day_zhi, "")
            if line_zhi == chong_zhi:
                candidates.append({
                    "timing": f"{line_zhi}日(日冲需补)",
                    "formula": "短事日破需补",
                    "confidence": 55,
                })
            else:
                candidates.append({
                    "timing": f"{line_zhi}日(逢值)",
                    "formula": "短事逢值日",
                    "confidence": 60,
                })
    else:
        # 常事月转日不转: 月支周期为主
        if line_zhi == month_zhi:
            candidates.append({
                "timing": "本月(临月令)",
                "formula": "常事临月令",
                "confidence": 70,
            })
        else:
            candidates.append({
                "timing": f"{line_zhi}月(逢值月)",
                "formula": "常事逢值月",
                "confidence": 55,
            })

    return candidates



# ============================================================================
# Yuan Shen Timing (元神应期)
# ============================================================================

def estimate_yuan_shen_yingqi(hexagram, yong_shen_liu_qin, wangshuai_results,
                              jixiong_result):
    """
    推断元神应期(静卦中元神辅助判断)。

    Rules:
    - 吉: 元神出空或逢值时应期
    - 凶: 元神被冲时应期

    Args:
        hexagram: Hexagram对象
        yong_shen_liu_qin: 用神六亲
        wangshuai_results: 旺衰结果列表
        jixiong_result: 吉凶判断结果 dict

    Returns:
        list[dict]: 应期候选
    """
    candidates = []
    yuan_shen_lq = identify_yuan_shen(yong_shen_liu_qin)
    if not yuan_shen_lq:
        return candidates

    # Find yuan_shen lines
    yuan_lines = [l for l in hexagram.lines if l.liu_qin == yuan_shen_lq]
    if not yuan_lines:
        return candidates

    ji_xiong = jixiong_result.get("ji_xiong", "平") if jixiong_result else "平"

    for yl in yuan_lines:
        yl_zhi = yl.di_zhi
        if ji_xiong == "吉":
            # 吉: 元神出空或逢值
            if yl.is_xun_kong:
                candidates.append({
                    "timing": f"{yl_zhi}日/月(元神出空)",
                    "formula": "吉时元神出空",
                    "confidence": 65,
                })
                chong_zhi = LIU_CHONG.get(yl_zhi, "")
                if chong_zhi:
                    candidates.append({
                        "timing": f"{chong_zhi}日/月(冲元神出空)",
                        "formula": "吉时冲元神出空",
                        "confidence": 60,
                    })
            else:
                candidates.append({
                    "timing": f"{yl_zhi}日/月(元神逢值)",
                    "formula": "吉时元神逢值",
                    "confidence": 55,
                })
        else:
            # 凶: 元神被冲
            chong_zhi = LIU_CHONG.get(yl_zhi, "")
            if chong_zhi:
                candidates.append({
                    "timing": f"{chong_zhi}日/月(元神被冲)",
                    "formula": "凶时元神被冲",
                    "confidence": 60,
                })

    return candidates



# ============================================================================
# Standard Timing Formulas (21条应期公式)
# ============================================================================

def apply_standard_formulas(line, hexagram, wangshuai_result, moving_analysis,
                            dongbian_results, event_duration, jixiong_result):
    """
    应用21条标准应期公式。

    Args:
        line: YaoLine对象 (用神爻)
        hexagram: Hexagram对象
        wangshuai_result: 该爻的旺衰分析结果
        moving_analysis: 该爻的动变分析结果
        dongbian_results: 全卦动变分析结果
        event_duration: 事件持续期
        jixiong_result: 吉凶判断结果

    Returns:
        list[dict]: 应期候选
            [{"timing": str, "formula_id": int, "formula_name": str, "confidence": int}]
    """
    candidates = []
    line_zhi = line.di_zhi
    overall = wangshuai_result.get("overall", "平")
    is_yue_po = "月破" in wangshuai_result.get("month_shuai", [])
    day_zhi = hexagram.gan_zhi["day_zhi"]
    month_zhi = hexagram.gan_zhi["month_zhi"]
    ji_xiong = jixiong_result.get("ji_xiong", "平") if jixiong_result else "平"

    # Formula 5: Xunkong (旬空): 填空/冲空/出空
    if line.is_xun_kong:
        candidates.append({
            "timing": f"{line_zhi}日/月(填空逢值)",
            "formula_id": 5,
            "formula_name": "旬空填空",
            "confidence": 80,
        })
        chong_zhi = LIU_CHONG.get(line_zhi, "")
        if chong_zhi:
            candidates.append({
                "timing": f"{chong_zhi}日/月(冲空)",
                "formula_id": 5,
                "formula_name": "旬空冲空",
                "confidence": 75,
            })
        candidates.append({
            "timing": "出旬之日(出空)",
            "formula_id": 5,
            "formula_name": "旬空出空",
            "confidence": 65,
        })
        return candidates

    # Formula 3: Month-broken (月破): 填实/补破/出月破
    if is_yue_po:
        candidates.append({
            "timing": f"{line_zhi}月/日(填实)",
            "formula_id": 3,
            "formula_name": "月破填实",
            "confidence": 75,
        })
        if line_zhi in LIU_HE:
            he_zhi = LIU_HE[line_zhi][0]
            candidates.append({
                "timing": f"{he_zhi}月/日(补破逢合)",
                "formula_id": 3,
                "formula_name": "月破补破",
                "confidence": 70,
            })
        candidates.append({
            "timing": "出月破(过月)",
            "formula_id": 3,
            "formula_name": "月破出破",
            "confidence": 60,
        })
        return candidates

    # Formula 4: Day-clashed (日冲)
    if LIU_CHONG.get(day_zhi) == line_zhi:
        candidates.append({
            "timing": "当日或次日(日冲即应)",
            "formula_id": 4,
            "formula_name": "日冲即应",
            "confidence": 70,
        })

    # Formula 2: Moving line (动爻): 逢合逢值
    if line.is_moving and moving_analysis:
        qu_wang = moving_analysis.get("趋旺", [])
        qu_shuai = moving_analysis.get("趋衰", [])

        # Formula 9: 化进神
        if "化进神" in qu_wang:
            bian_zhi = moving_analysis.get("bian_zhi", "")
            candidates.append({
                "timing": f"{line_zhi}日/月(逢值)",
                "formula_id": 9,
                "formula_name": "化进神逢值",
                "confidence": 80,
            })
            if line_zhi in LIU_HE:
                he_zhi = LIU_HE[line_zhi][0]
                candidates.append({
                    "timing": f"{he_zhi}日/月(逢合)",
                    "formula_id": 9,
                    "formula_name": "化进神逢合",
                    "confidence": 75,
                })
            if bian_zhi in JIN_SHEN:
                jin_zhi = JIN_SHEN[bian_zhi]
                candidates.append({
                    "timing": f"{jin_zhi}日/月(逢进)",
                    "formula_id": 9,
                    "formula_name": "化进神逢进",
                    "confidence": 70,
                })
            return candidates

        # Formula 10: 化退神
        if "化退神" in qu_shuai:
            chong_zhi = LIU_CHONG.get(line_zhi, "")
            bian_zhi = moving_analysis.get("bian_zhi", "")
            if chong_zhi:
                candidates.append({
                    "timing": f"{chong_zhi}日/月(逢冲)",
                    "formula_id": 10,
                    "formula_name": "化退神逢冲",
                    "confidence": 70,
                })
            if bian_zhi in TUI_SHEN:
                tui_zhi = TUI_SHEN[bian_zhi]
                candidates.append({
                    "timing": f"{tui_zhi}日/月(逢退值)",
                    "formula_id": 10,
                    "formula_name": "化退神逢退值",
                    "confidence": 65,
                })
            return candidates

        # Formula 8: Bian_yao timing
        bian_zhi = moving_analysis.get("bian_zhi", "")
        has_huitou = ("回头生" in qu_wang or "回头克" in qu_shuai)
        if bian_zhi:
            if has_huitou:
                # 有回头: 逢值逢合
                candidates.append({
                    "timing": f"{bian_zhi}日/月(变爻逢值)",
                    "formula_id": 8,
                    "formula_name": "变爻回头逢值",
                    "confidence": 70,
                })
                if bian_zhi in LIU_HE:
                    he_zhi = LIU_HE[bian_zhi][0]
                    candidates.append({
                        "timing": f"{he_zhi}日/月(变爻逢合)",
                        "formula_id": 8,
                        "formula_name": "变爻回头逢合",
                        "confidence": 65,
                    })
            else:
                # 无回头: 逢值逢冲
                candidates.append({
                    "timing": f"{bian_zhi}日/月(变爻逢值)",
                    "formula_id": 8,
                    "formula_name": "变爻非回头逢值",
                    "confidence": 65,
                })
                bian_chong = LIU_CHONG.get(bian_zhi, "")
                if bian_chong:
                    candidates.append({
                        "timing": f"{bian_chong}日/月(变爻逢冲)",
                        "formula_id": 8,
                        "formula_name": "变爻非回头逢冲",
                        "confidence": 60,
                    })

        # General moving line: 逢合逢值
        if line_zhi in LIU_HE:
            he_zhi = LIU_HE[line_zhi][0]
            candidates.append({
                "timing": f"{he_zhi}日/月(动爻逢合)",
                "formula_id": 2,
                "formula_name": "动爻逢合",
                "confidence": 70,
            })
        candidates.append({
            "timing": f"{line_zhi}日/月(动爻逢值)",
            "formula_id": 2,
            "formula_name": "动爻逢值",
            "confidence": 65,
        })
        return candidates

    # Formula 1: Static line (静爻): 旺逢冲, 衰逢值
    if overall == "旺":
        chong_zhi = LIU_CHONG.get(line_zhi, "")
        if chong_zhi:
            candidates.append({
                "timing": f"{chong_zhi}日/月(旺静逢冲)",
                "formula_id": 1,
                "formula_name": "旺静逢冲",
                "confidence": 80,
            })
    else:
        candidates.append({
            "timing": f"{line_zhi}日/月(衰静逢值)",
            "formula_id": 1,
            "formula_name": "衰静逢值",
            "confidence": 75,
        })

    # Formula 6: Month-harmony (月合): 数后三月
    if line_zhi in LIU_HE:
        he_zhi, _ = LIU_HE[line_zhi]
        if he_zhi == month_zhi:
            month_idx = DI_ZHI.index(month_zhi)
            future = [DI_ZHI[(month_idx + i) % 12] for i in range(1, 4)]
            candidates.append({
                "timing": f"三月内({'/'.join(future)})",
                "formula_id": 6,
                "formula_name": "月合数后三月",
                "confidence": 60,
            })

    # Formula 7: Same attribute (同属性时应)
    line_wx = DI_ZHI_WU_XING[line_zhi]
    same_wx_zhis = [z for z in DI_ZHI if DI_ZHI_WU_XING[z] == line_wx
                    and z != line_zhi]
    if same_wx_zhis:
        candidates.append({
            "timing": f"{'/'.join(same_wx_zhis)}日/月(同属性)",
            "formula_id": 7,
            "formula_name": "同属性时应",
            "confidence": 45,
        })

    # Formula 11: San-he-ju (三合局): 补缺成局
    san_he_wx = SAN_HE_BY_ZHI.get(line_zhi, "")
    if san_he_wx:
        san_he_members = SAN_HE[san_he_wx]
        present_zhis = set()
        for l in hexagram.lines:
            if l.di_zhi in san_he_members:
                present_zhis.add(l.di_zhi)
        missing = [z for z in san_he_members if z not in present_zhis]
        if len(missing) == 1:
            candidates.append({
                "timing": f"{missing[0]}日/月(补缺成{san_he_wx}局)",
                "formula_id": 11,
                "formula_name": "三合局补缺",
                "confidence": 55,
            })

    # Formula 12: Mu (墓): 冲墓
    line_wx = DI_ZHI_WU_XING[line_zhi]
    for z in DI_ZHI:
        if get_chang_sheng(line_wx, z) == "墓":
            mu_zhi = z
            chong_mu = LIU_CHONG.get(mu_zhi, "")
            if chong_mu:
                candidates.append({
                    "timing": f"{chong_mu}日/月(冲墓)",
                    "formula_id": 12,
                    "formula_name": "冲墓",
                    "confidence": 50,
                })
            break

    # Formula 13: Fan-yin (反吟): reversed branch value
    if line.is_moving and moving_analysis:
        bian_zhi = moving_analysis.get("bian_zhi", "")
        if bian_zhi and LIU_CHONG.get(line_zhi) == bian_zhi:
            candidates.append({
                "timing": f"{bian_zhi}日/月(反吟应期)",
                "formula_id": 13,
                "formula_name": "反吟逢值",
                "confidence": 55,
            })

    # Formula 14: 吉而受克: 忌爻受冲
    if ji_xiong == "吉":
        # Find potential ji_shen lines that are ke-ing yong_shen
        line_wx = DI_ZHI_WU_XING[line_zhi]
        for other in hexagram.lines:
            if other.position == line.position:
                continue
            other_wx = DI_ZHI_WU_XING[other.di_zhi]
            if WU_XING_KE.get(other_wx) == line_wx:
                chong_ji = LIU_CHONG.get(other.di_zhi, "")
                if chong_ji:
                    candidates.append({
                        "timing": f"{chong_ji}日/月(忌爻{other.di_zhi}受冲)",
                        "formula_id": 14,
                        "formula_name": "吉而受克忌爻受冲",
                        "confidence": 50,
                    })
                    break

    # Formula 15: 凶而受生: 生爻被冲
    if ji_xiong == "凶":
        line_wx = DI_ZHI_WU_XING[line_zhi]
        for other in hexagram.lines:
            if other.position == line.position:
                continue
            other_wx = DI_ZHI_WU_XING[other.di_zhi]
            if WU_XING_SHENG.get(other_wx) == line_wx:
                chong_sheng = LIU_CHONG.get(other.di_zhi, "")
                if chong_sheng:
                    candidates.append({
                        "timing": f"{chong_sheng}日/月(生爻{other.di_zhi}被冲)",
                        "formula_id": 15,
                        "formula_name": "凶而受生生爻被冲",
                        "confidence": 50,
                    })
                    break

    return candidates



# ============================================================================
# Timing Modifiers (加速/减速信号)
# ============================================================================

def detect_timing_modifiers(hexagram, dongbian_results, liuchong_liuhe_results=None):
    """
    检测应期加速/减速修正信号。

    加速: 暗动, 临日令而动, 卦变六冲
    减速: 三合局, 卦变六合

    Args:
        hexagram: Hexagram对象
        dongbian_results: 动变分析结果
        liuchong_liuhe_results: 六冲六合分析结果 (optional)

    Returns:
        dict: {"acceleration": [str], "deceleration": [str]}
    """
    acceleration = []
    deceleration = []

    # Check for andong (暗动)
    an_dong = dongbian_results.get("an_dong", [])
    for ad in an_dong:
        if ad.get("type") == "暗动":
            acceleration.append(f"暗动(第{ad['position']}爻{ad['di_zhi']})")

    # Check for 临日令而动
    day_zhi = hexagram.gan_zhi["day_zhi"]
    moving_analyses = dongbian_results.get("moving_analyses", {})
    for pos, ma in moving_analyses.items():
        line = hexagram.lines[pos - 1]
        if line.di_zhi == day_zhi and not ma.get("is_useless"):
            acceleration.append(f"临日令而动(第{pos}爻{line.di_zhi})")

    # Check for san-he-ju (三合局) -> deceleration
    san_he_ju = dongbian_results.get("san_he_ju", [])
    if san_he_ju:
        for sh in san_he_ju:
            deceleration.append(f"三合局({sh['wu_xing']}局)")

    # Check liuchong_liuhe patterns
    if liuchong_liuhe_results:
        liu_chong = liuchong_liuhe_results.get("liu_chong", {})
        liu_he = liuchong_liuhe_results.get("liu_he", {})
        huhua = liuchong_liuhe_results.get("chong_he_huhua", {})

        # 卦变六冲 -> acceleration
        if liu_chong.get("is_liu_chong"):
            chong_type = liu_chong.get("type", "")
            if chong_type in ("bian", "both"):
                acceleration.append("卦变六冲")

        # 卦变六合 -> deceleration
        if liu_he.get("is_liu_he"):
            he_type = liu_he.get("type", "")
            if he_type in ("bian", "both"):
                deceleration.append("卦变六合")

    return {"acceleration": acceleration, "deceleration": deceleration}


# ============================================================================
# Timing Candidate Ranking (应期排序)
# ============================================================================

def rank_timing_candidates(candidates):
    """
    对应期候选进行排序打分。

    Principles:
    1. 应众不应寡: 重复出现的时间点得分更高
    2. 应早不应迟: 地支序号靠前的得分奖励
    3. 应邻不应单: 相邻地支对得分奖励

    Args:
        candidates: list of dicts, each with "timing" and "confidence" keys

    Returns:
        list[dict]: sorted [{"timing": str, "score": int, "formulas": [str]}]
    """
    if not candidates:
        return []

    # Deduplicate: same timing string from the same formula source should only
    # count once for the "应众不应寡" bonus. Group by timing, then within each
    # group, deduplicate by formula_name/formula so overlapping formula paths
    # don't inflate counts.
    timing_groups = {}
    for c in candidates:
        timing = c.get("timing", "")
        # Use full timing string as key
        if timing not in timing_groups:
            timing_groups[timing] = {
                "timing": timing,
                "score": 0,
                "formulas": [],
                "confidence_sum": 0,
                "count": 0,
                "_seen_formulas": set(),
            }
        group = timing_groups[timing]
        conf = c.get("confidence", 50)
        formula_name = c.get("formula_name", c.get("formula", ""))
        # Deduplicate: only count each unique formula source once per timing
        if formula_name and formula_name in group["_seen_formulas"]:
            # Same formula already contributed to this timing - skip for count
            # but still use the max confidence from this formula
            continue
        if formula_name:
            group["_seen_formulas"].add(formula_name)
        group["confidence_sum"] += conf
        group["count"] += 1
        if formula_name and formula_name not in group["formulas"]:
            group["formulas"].append(formula_name)

    # Calculate scores
    results = []
    for key, group in timing_groups.items():
        score = group["confidence_sum"]
        # Principle 1: 应众不应寡 - duplicate entries get bonus
        if group["count"] > 1:
            score += group["count"] * 20

        group["score"] = score
        results.append(group)

    # Principle 3: 应邻不应单 - find adjacent DI_ZHI in results and boost
    timing_zhis = {}
    for r in results:
        timing_str = r["timing"]
        for z in DI_ZHI:
            if z in timing_str:
                timing_zhis[z] = r
                break

    for z, r in timing_zhis.items():
        z_idx = DI_ZHI.index(z)
        prev_z = DI_ZHI[(z_idx - 1) % 12]
        next_z = DI_ZHI[(z_idx + 1) % 12]
        if prev_z in timing_zhis or next_z in timing_zhis:
            r["score"] += 15

    # Principle 2: 应早不应迟 - earlier in DI_ZHI gets small bonus
    for r in results:
        timing_str = r["timing"]
        for idx, z in enumerate(DI_ZHI):
            if z in timing_str:
                r["score"] += max(0, 12 - idx)
                break

    # Sort by score descending
    results.sort(key=lambda x: x["score"], reverse=True)

    # Clean up output
    final = []
    for r in results:
        final.append({
            "timing": r["timing"],
            "score": r["score"],
            "formulas": r["formulas"],
        })

    return final



# ============================================================================
# Original Functions (Backward Compatible)
# ============================================================================

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
    sheng_wx = [wx for wx, target in WU_XING_SHENG.items() if target == line_wx]
    if sheng_wx:
        sheng_zhi_list = [z for z in DI_ZHI if DI_ZHI_WU_XING[z] == sheng_wx[0]]
        if sheng_zhi_list and overall != "旺":
            candidates.append(f"逢生: {'/'.join(sheng_zhi_list)}日/月({sheng_wx[0]}生{line_wx})")

    return candidates



# ============================================================================
# Enhanced analyze_yingqi (Backward Compatible)
# ============================================================================

def analyze_yingqi(hexagram, yong_shen_lines, wangshuai_results, dongbian_results,
                   **kwargs):
    """
    分析用神的应期。

    Args:
        hexagram: Hexagram对象
        yong_shen_lines: 用神爻列表
        wangshuai_results: 所有爻的旺衰结果
        dongbian_results: 动变分析结果
        **kwargs: 可选增强参数
            event_duration: 事件持续期 (str)
            jixiong_result: 吉凶判断结果 (dict)
            liuchong_liuhe_results: 六冲六合分析结果 (dict)

    Returns:
        list[dict]: 每个用神爻的应期候选
    """
    event_duration = kwargs.get("event_duration", "medium")
    jixiong_result = kwargs.get("jixiong_result", None)
    liuchong_liuhe_results = kwargs.get("liuchong_liuhe_results", None)

    results = []
    moving_analyses = dongbian_results.get("moving_analyses", {})
    an_dong_list = dongbian_results.get("an_dong", [])

    # Build an_dong lookup by position
    an_dong_by_pos = {}
    for ad in an_dong_list:
        an_dong_by_pos[ad["position"]] = ad

    for line in yong_shen_lines:
        ws = wangshuai_results[line.position - 1]
        ma = moving_analyses.get(line.position)

        # Original candidates (backward compatible)
        candidates = estimate_yingqi(line, ws, ma)

        result = {
            "position": line.position,
            "di_zhi": line.di_zhi,
            "liu_qin": line.liu_qin,
            "candidates": candidates,
        }

        # Enhanced analysis
        result["event_duration"] = event_duration

        # Collect all timing candidates for ranking
        all_candidates = []

        # Standard formulas
        formula_candidates = apply_standard_formulas(
            line, hexagram, ws, ma, dongbian_results,
            event_duration, jixiong_result
        )
        all_candidates.extend(formula_candidates)

        # Andong timing
        if line.position in an_dong_by_pos:
            andong_candidates = estimate_andong_yingqi(
                line, an_dong_by_pos[line.position], hexagram
            )
            all_candidates.extend(andong_candidates)

        # Yueling timing
        yueling_candidates = estimate_yueling_yingqi(line, hexagram, ws)
        all_candidates.extend(yueling_candidates)

        # Riling timing
        riling_candidates = estimate_riling_yingqi(
            line, hexagram, ws, event_duration
        )
        all_candidates.extend(riling_candidates)

        # Rank candidates
        ranked = rank_timing_candidates(all_candidates)
        result["ranked_candidates"] = ranked

        # Modifiers
        modifiers = detect_timing_modifiers(
            hexagram, dongbian_results, liuchong_liuhe_results
        )
        result["modifiers"] = modifiers

        # Yuan_shen timing
        yuan_shen_timing = []
        if jixiong_result:
            # Use the explicit yong_shen_liu_qin from kwargs (passed by analyzer)
            # rather than line.liu_qin, which is fragile if line selection changes
            explicit_yong_lq = kwargs.get("yong_shen_liu_qin", line.liu_qin)
            yuan_shen_timing = estimate_yuan_shen_yingqi(
                hexagram, explicit_yong_lq, wangshuai_results, jixiong_result
            )
        result["yuan_shen_timing"] = yuan_shen_timing

        results.append(result)

    return results
