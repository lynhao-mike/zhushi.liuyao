"""
旺衰分析模块 - Wang-Shuai (Prosperity/Decline) Analysis

根据月建(月支)和日辰(日支)判断每爻的旺衰状态。
月建四旺四衰，日辰五旺二衰。

【第十章核心规则】
─────────────────────────────────────────────────────
月令对爻的作用（优先级最高）：
  旺：临月令 | 月令合 | 月令生 | 月令扶
  衰：月破（月令与爻支互冲）| 月令克 | 休（爻克月） | 泄（爻生月）

  ★ 月破 = 月支与爻支互冲，爻受月冲，衰败之极。
    写法："{爻支}受月破"，而非"{月支}冲{爻支}"这种单向说法。
    例：亥月遇巳爻 → 巳亥互冲 → 巳爻月破（不能写"亥冲巳"）

日辰对爻的作用：
  旺：临日建 | 日令合（仅静爻）| 日令生 | 日令扶 | 临日令长生/帝旺
  衰：日令克 | 爻绝在日

  ★ 日冲静爻 = 冲起（由静转动，可成暗动），与月破截然不同！
    写法："{爻支}逢日冲（{冲支}与{爻支}互冲）冲起暗动"
  ★ 日冲动爻 = 冲起不为散（动爻被冲只会加强力度）

月令合爻 vs 日令合爻：
  月令合爻 → 旺相（无"月绊"之说）
  日令合爻 → 日绊（合而不动，延迟之意），不算旺相
─────────────────────────────────────────────────────
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
    2. 月令合: 爻支与月支六合（注：月令合为旺相，无"月绊"之说）
    3. 月令生: 月支五行生爻支五行
    4. 月令扶: 月支五行同爻支五行，但地支不同

    衰的条件:
    1. 月破: 月支与爻支互冲（爻受月令冲克，衰败之极）
       ★ 此处表述为"爻支受月破"，六冲关系本是互冲，月破特指月令冲爻。
       例：亥月巳爻 → 巳亥互冲 → 巳爻受月破
    2. 月令克: 月支五行克爻支五行
    3. 休（爻克月）: 爻支五行克月支五行
    4. 泄（爻生月）: 爻支五行生月支五行

    Returns:
        tuple: (旺因列表[str], 衰因列表[str])
    """
    line_wx = DI_ZHI_WU_XING[line_zhi]
    month_wx = DI_ZHI_WU_XING[month_zhi]

    wang_reasons = []
    shuai_reasons = []

    # 旺的条件
    # 1. 临月令
    if line_zhi == month_zhi:
        wang_reasons.append("临月令")

    # 2. 月令合（六合）
    if line_zhi in LIU_HE and LIU_HE[line_zhi][0] == month_zhi:
        wang_reasons.append("月令合")

    # 3. 月令生: 月支五行生爻支五行
    if WU_XING_SHENG[month_wx] == line_wx:
        wang_reasons.append("月令生")

    # 4. 月令扶: 同五行不同支
    if month_wx == line_wx and month_zhi != line_zhi:
        wang_reasons.append("月令扶")

    # 衰的条件
    # 1. 月破：月支与爻支互冲，爻受月令所冲
    #    判断：LIU_CHONG[month_zhi] == line_zhi，即月支冲到爻支
    #    注：六冲是互冲关系（巳亥互冲），这里用"月破"描述爻被月令冲破的状态
    if LIU_CHONG.get(month_zhi) == line_zhi:
        shuai_reasons.append("月破")

    # 2. 月令克: 月支五行克爻支五行
    if WU_XING_KE[month_wx] == line_wx:
        shuai_reasons.append("月令克")

    # 3. 休（爻克月）: 爻支五行克月支五行
    if WU_XING_KE[line_wx] == month_wx:
        shuai_reasons.append("休")

    # 4. 泄（爻生月）: 爻支五行生月支五行
    if WU_XING_SHENG[line_wx] == month_wx:
        shuai_reasons.append("泄")

    return wang_reasons, shuai_reasons


def ri_chen_wangshuai(line_zhi, day_zhi, is_static=True):
    """
    日辰旺衰判断 (5旺2衰)。

    旺的条件:
    1. 临日建: 爻支 == 日支
    2. 日令合（仅静爻）: 静爻与日支六合
       ★ 注意：日令合静爻 = 旺相；日令合动爻 = 日绊（延迟，不算旺相）
    3. 日令生: 日支五行生爻支五行
    4. 日令扶: 日支五行同爻支五行，但地支不同
    5. 临日令长生/帝旺: 爻的五行在日支处于长生或帝旺位

    衰的条件:
    1. 日令克: 日支五行克爻支五行
    2. 爻绝在日: 爻的五行在日支处于绝地
       ★ 注意：整体趋旺时日绝当平看，勿轻易断衰

    日冲静爻（不在此函数处理，见 detect_an_dong）：
    · 静爻得月旺而被日冲 → 冲旺为暗动（爻由静转动）
    · 静爻旬空而被日冲   → 冲空为暗动
    · 与月破（月令冲爻）截然不同，月破论衰，日冲静爻论暗动

    Args:
        line_zhi: 爻的地支
        day_zhi: 日支
        is_static: 是否静爻（影响日令合的旺衰判断）

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

    # 2. 静爻日令合（动爻与日令相合为"日绊"，不在此处计旺）
    if is_static and line_zhi in LIU_HE and LIU_HE[line_zhi][0] == day_zhi:
        wang_reasons.append("日令合")

    # 3. 日令生
    if WU_XING_SHENG[day_wx] == line_wx:
        wang_reasons.append("日令生")

    # 4. 日令扶
    if day_wx == line_wx and day_zhi != line_zhi:
        wang_reasons.append("日令扶")

    # 5. 临日令长生/帝旺（吉凶层面精简规则：仅长生与帝旺算旺相）
    stage = get_chang_sheng(line_wx, day_zhi)
    if stage in ("长生", "帝旺"):
        wang_reasons.append(f"临日令{stage}")

    # 衰的条件
    # 1. 日令克
    if WU_XING_KE[day_wx] == line_wx:
        shuai_reasons.append("日令克")

    # 2. 爻绝在日（整体趋旺时此条将在 analyze_line_wangshuai 中撤销）
    if stage == "绝":
        shuai_reasons.append("爻绝在日")

    return wang_reasons, shuai_reasons


def analyze_line_wangshuai(line_zhi, month_zhi, day_zhi, is_static=True):
    """
    综合分析单爻旺衰。

    综合月建和日辰的结果，判断整体旺衰。
    特殊规则：如整体趋旺，日绝当平看；月破为重度衰，优先级高于其余因素。

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

    # 月令旺衰优先级最高
    # 临月令/月令生/月令扶 → 整体趋旺（月破除外）
    has_strong_month_wang = any(r in ("临月令", "月令生", "月令扶") for r in month_wang)
    has_yue_po = "月破" in month_shuai

    # 初步判断整体趋势（先不处理日绝）
    preliminary_wang = wang_score > shuai_score
    if has_strong_month_wang and not has_yue_po:
        preliminary_wang = True

    # 特殊规则：整体趋旺时，日绝当平看（从于卦理，卦理优先）
    # 依据第十章：生旺墓绝"从于卦理"，一切卦理与之冲突均以卦理为先
    if "爻绝在日" in day_shuai:
        if preliminary_wang:
            day_shuai.remove("爻绝在日")
            day_wang.append("绝处逢生(以平论)")
            wang_score = len(month_wang) + len(day_wang)
            shuai_score = len(month_shuai) + len(day_shuai)

    # 最终判断
    if wang_score > shuai_score:
        overall = WANG
    elif shuai_score > wang_score:
        overall = SHUAI
    else:
        overall = PING

    # 月破为重度衰（无强月旺因素时，月破定衰不可逆）
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
        list[dict]: 每爻的旺衰分析结果，索引0=初爻，索引5=上爻
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
