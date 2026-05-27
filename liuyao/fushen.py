"""
伏神(藏爻)分析模块 - Fu Shen / Cang Yao Analysis

据《古筮真诠》第三十九章 (藏伏理论的应用):

【基本概念】
- 藏爻: 把整个本宫纯卦的所有爻套入主卦相应爻位之下, 用于补五行六亲
- 伏爻: 不作为用神的藏爻 (=主卦缺的五行六亲)
- 伏神: 取作用神的伏爻 (即用神不在主卦中, 从藏爻里取出来的)
- 飞神: 主卦中与伏神同一位置的爻 (盖在伏神上面的爻)

【飞伏关系四种 (传统古论)】
1. 飞神克伏神 = "伤身"  (飞神长期克制伏神, 伏神受伤)
2. 伏神克飞神 = "出暴"  (快且凶暴, 伏神反压飞神)
3. 伏神生飞神 = "泄气"  (伏神力量被飞神消耗)
4. 飞神生伏神 = "长生"  (依存关系: 飞为根, 伏为枝叶)

【朱辰彬更新观点 (本系统采用)】
传统飞伏关系太繁琐, 实用性不高。改用 3 个分析方向:
1. 卦理定性 - 伏空/伏破/用藏世伤/冲飞露伏(短期)
2. 卦意预兆 - 藏爻确认/冲合预兆 (在 patterns.py 已实现)
3. 心态反映 - 心态卦特征 (在 patterns.py 已实现)

【独立性原则 (重要修正)】
伏神只与本位的飞神发生卦理关系, 不与其他动静爻直接作用
(原理类似动爻只与变爻发生关系, 不与其他爻发生卦理关系)

【应期总原则: 冲飞露伏】
《黄金策》: "伏无提挈终徒尔, 飞不推开亦枉然"
1. 冲飞: 冲走飞神之时 (= 揭盖)
2. 露伏: 伏神逢值逢合的旺相之时
"""

from .data import (
    DI_ZHI_WU_XING,
    WU_XING_SHENG, WU_XING_KE,
    LIU_CHONG, LIU_HE,
)


# =============================================================================
# 伏神查找
# =============================================================================

def find_fu_shen(hexagram, yong_shen_liu_qin):
    """
    查找伏神: 当用神六亲在主卦中找不到, 从藏爻中查找.

    Args:
        hexagram: Hexagram 对象
        yong_shen_liu_qin: 用神六亲名称 ("妻财"/"父母" 等)

    Returns:
        dict or None: {
            "cang_yao": CangYao 对象,
            "position": int,
            "fei_shen": YaoLine 对象 (盖在上面的飞神),
        }
        如果用神在主卦中已现, 或藏爻中也无该六亲, 返回 None.
    """
    # 主卦中是否已有该用神
    main_lines_with_yong = [l for l in hexagram.lines if l.liu_qin == yong_shen_liu_qin]
    if main_lines_with_yong:
        return None  # 用神已在主卦中, 不需取伏神

    # 在藏爻中查找
    cang_with_yong = [c for c in hexagram.cang_yao if c.liu_qin == yong_shen_liu_qin]
    if not cang_with_yong:
        return None  # 藏爻中也无 - 用神彻底不上卦

    # 通常取第一个找到的 (本宫纯卦中, 同一六亲不会有多个)
    cang = cang_with_yong[0]
    fei_shen = hexagram.lines[cang.position - 1]

    return {
        "cang_yao": cang,
        "position": cang.position,
        "fei_shen": fei_shen,
        "fei_di_zhi": fei_shen.di_zhi,
        "fei_wu_xing": fei_shen.wu_xing,
        "fu_di_zhi": cang.di_zhi,
        "fu_wu_xing": cang.wu_xing,
    }


# =============================================================================
# 飞伏关系判定 (4种)
# =============================================================================

FEI_FU_RELATIONS = {
    "飞神克伏神": {"alias": "伤身", "implication": "飞神长期克制伏神, 伏神受伤"},
    "伏神克飞神": {"alias": "出暴", "implication": "快且凶暴, 伏神反压飞神引发激烈碰撞"},
    "伏神生飞神": {"alias": "泄气", "implication": "伏神力量被飞神慢慢消耗"},
    "飞神生伏神": {"alias": "长生", "implication": "依存关系, 飞为根伏为枝叶, 伏神得飞神生扶才旺"},
    "飞伏比和": {"alias": "比和", "implication": "彼此同行, 力量持平"},
}


def determine_fei_fu_relation(fei_wu_xing, fu_wu_xing):
    """
    判定飞伏关系 (五种, 含比和).

    Args:
        fei_wu_xing: 飞神五行
        fu_wu_xing: 伏神五行

    Returns:
        str: 关系名称 (飞神克伏神/伏神克飞神/伏神生飞神/飞神生伏神/飞伏比和)
    """
    if fei_wu_xing == fu_wu_xing:
        return "飞伏比和"
    if WU_XING_KE.get(fei_wu_xing) == fu_wu_xing:
        return "飞神克伏神"
    if WU_XING_KE.get(fu_wu_xing) == fei_wu_xing:
        return "伏神克飞神"
    if WU_XING_SHENG.get(fu_wu_xing) == fei_wu_xing:
        return "伏神生飞神"
    if WU_XING_SHENG.get(fei_wu_xing) == fu_wu_xing:
        return "飞神生伏神"
    return "飞伏比和"


# =============================================================================
# 伏神吉凶判断 (朱辰彬 3 大支柱之 1: 卦理定性)
# =============================================================================

def evaluate_fushen_jixiong(hexagram, fushen_info, wangshuai_results,
                            shi_line_wangshuai=None,
                            shi_line_dongbian=None,
                            is_short_term=True):
    """
    伏神吉凶判定 - 据卦理定性 4 项规则.

    朱辰彬主张: 摒弃传统飞伏关系判吉凶, 改用 4 项卦理特征判断:
    1. 伏空 - 伏神逢旬空 → 凶 ("伏居空地, 事与心违")
    2. 伏破 - 伏神逢日破/月破 → 凶 (深埋之物再遭破败)
    3. 用藏世伤 - 用神藏伏 + 世爻被伤 → 直接判事败
    4. 冲飞露伏 - 飞神空/破 (仅短期占有效) → 吉

    Args:
        hexagram: Hexagram 对象
        fushen_info: find_fu_shen 返回的字典
        wangshuai_results: 全卦旺衰结果 (用于判定飞神爻空破)
        shi_line_wangshuai: 世爻旺衰
        shi_line_dongbian: 世爻动变分析(可选)
        is_short_term: 是否短期事占 (短期才看冲飞露伏吉利)

    Returns:
        list[dict]: 每条规则的判定结果
            [{"rule": str, "result": "吉"/"凶"/"中性", "detail": str}, ...]
    """
    results = []
    cang = fushen_info["cang_yao"]
    fei = fushen_info["fei_shen"]
    fei_pos = fushen_info["position"]
    fei_ws = wangshuai_results[fei_pos - 1] if wangshuai_results else None

    # 规则 1: 伏空 (伏神旬空)
    if cang.is_xun_kong:
        results.append({
            "rule": "伏空",
            "result": "凶",
            "detail": (
                f"伏神{cang.liu_qin}{cang.di_zhi}陷入旬空 - "
                f"伏居空地, 事与心违 (《黄金策》)"
            ),
        })

    # 规则 2: 伏破 (伏神逢月破 - 即伏神地支与月支相冲)
    month_zhi = hexagram.gan_zhi.get("month_zhi", "")
    if month_zhi and LIU_CHONG.get(cang.di_zhi) == month_zhi:
        results.append({
            "rule": "伏破",
            "result": "凶",
            "detail": (
                f"伏神{cang.liu_qin}{cang.di_zhi}遭月破({month_zhi}冲) - "
                f"深埋之物再遭破败, 神仙难扭转"
            ),
        })

    # 规则 3: 用藏世伤 (世爻动变衰败/受克)
    if shi_line_wangshuai and shi_line_wangshuai.get("overall") == "衰":
        # 检查世爻是否被动爻克伤
        if shi_line_dongbian:
            ma = shi_line_dongbian
            shi_self_hurt = (
                "化绝" in ma.get("趋衰", []) or
                "化破" in ma.get("趋衰", []) or
                "回头克" in str(ma.get("useless_reason", ""))
            )
            if shi_self_hurt:
                results.append({
                    "rule": "用藏世伤",
                    "result": "凶",
                    "detail": "用神藏伏 + 世爻动变受伤 - 自身事谋, 自身受损, 事必败",
                })

    # 规则 4: 冲飞露伏 (仅短期占有效)
    if is_short_term and fei_ws:
        # 飞神旬空
        if fei.is_xun_kong:
            results.append({
                "rule": "冲飞露伏(飞空)",
                "result": "吉(短期)",
                "detail": (
                    f"飞神第{fei_pos}爻{fei.liu_qin}{fei.di_zhi}旬空 - "
                    f"盖子已虚, 短期内伏神易于显露 (《黄金策》: 空下伏神, 易于引拔)"
                ),
            })
        # 飞神月破
        elif "月破" in fei_ws.get("month_shuai", []):
            results.append({
                "rule": "冲飞露伏(飞破)",
                "result": "吉(短期)",
                "detail": (
                    f"飞神第{fei_pos}爻{fei.liu_qin}{fei.di_zhi}月破 - "
                    f"盖子已破, 短期内伏神易于显露"
                ),
            })

    if not results:
        results.append({
            "rule": "卦理定性",
            "result": "中性",
            "detail": (
                f"伏神{cang.liu_qin}{cang.di_zhi}藏伏在飞神{fei.liu_qin}{fei.di_zhi}下, "
                f"无明显空破或冲飞信号, 须配合卦意/心态分析综合定性"
            ),
        })

    return results


# =============================================================================
# 伏神应期 (冲飞 + 露伏)
# =============================================================================

def fushen_yingqi(fushen_info):
    """
    伏神应期: 冲飞 + 露伏.

    Returns:
        list[str]: 应期候选
    """
    cang = fushen_info["cang_yao"]
    fei = fushen_info["fei_shen"]

    candidates = []
    fei_chong = LIU_CHONG.get(fei.di_zhi, "")
    fu_zhi = cang.di_zhi
    fu_he = LIU_HE.get(fu_zhi, (None, None))[0]

    if fei_chong:
        candidates.append(f"冲飞: {fei_chong}日/月 (冲走飞神{fei.di_zhi}揭盖)")
    candidates.append(f"露伏(逢值): {fu_zhi}日/月 (伏神临值显露)")
    if fu_he:
        candidates.append(f"露伏(逢合): {fu_he}日/月 (伏神逢合显露)")

    return candidates


# =============================================================================
# 综合伏神分析入口
# =============================================================================

def analyze_fushen(hexagram, yong_shen_liu_qin, wangshuai_results,
                   dongbian_results, question_type="other"):
    """
    伏神综合分析入口 - 仅当用神不上卦时启用.

    Args:
        hexagram: Hexagram 对象
        yong_shen_liu_qin: 用神六亲
        wangshuai_results: 旺衰结果
        dongbian_results: 动变结果
        question_type: 问事类型(用于判断是否短期占)

    Returns:
        dict or None: 完整伏神分析
            {
                "fushen_info": ...,
                "fei_fu_relation": str,
                "fei_fu_implication": str,
                "jixiong_evaluations": list,
                "yingqi_candidates": list,
            }
        如果用神已在主卦, 返回 None.
    """
    fushen_info = find_fu_shen(hexagram, yong_shen_liu_qin)
    if not fushen_info:
        return None

    # 飞伏关系
    relation = determine_fei_fu_relation(
        fushen_info["fei_wu_xing"], fushen_info["fu_wu_xing"]
    )
    relation_meta = FEI_FU_RELATIONS.get(relation, {})

    # 短期占类型 (失物/疾病/文书/股票通常为短期)
    short_term_types = {
        "shiwu", "bing", "kaoshi", "xingRen", "youHuan", "cai", "other"
    }
    is_short = question_type in short_term_types

    # 世爻旺衰 / 动变信息 (用于"用藏世伤"规则)
    shi_line = next((l for l in hexagram.lines if l.is_shi), None)
    shi_ws = wangshuai_results[shi_line.position - 1] if shi_line else None
    shi_db = None
    if shi_line and shi_line.is_moving:
        shi_db = dongbian_results.get("moving_analyses", {}).get(shi_line.position)

    # 卦理定性 (4 规则)
    jixiong_evals = evaluate_fushen_jixiong(
        hexagram, fushen_info, wangshuai_results,
        shi_line_wangshuai=shi_ws,
        shi_line_dongbian=shi_db,
        is_short_term=is_short,
    )

    # 应期
    yingqi_candidates = fushen_yingqi(fushen_info)

    return {
        "fushen_info": fushen_info,
        "fei_fu_relation": relation,
        "fei_fu_alias": relation_meta.get("alias", ""),
        "fei_fu_implication": relation_meta.get("implication", ""),
        "jixiong_evaluations": jixiong_evals,
        "yingqi_candidates": yingqi_candidates,
        "is_short_term": is_short,
    }
