"""
卦象模式识别 - Hexagram Pattern Detection

实现《古筮真诠》理论中的结构性卦象模式识别:
- 入墓 (Ru Mu): 日墓/动墓/化墓 + 真假墓判别
- 三绊 (San Ban): 日绊/动绊/化绊
- 反吟 (Fan Yin): 卦象反吟/卦宫反吟/爻动反吟/爻化反吟
- 伏吟 (Fu Yin): 内卦伏吟/外卦伏吟/爻动伏吟
- 六冲六合卦 (Liu Chong / Liu He Gua) + 互化模式
- 三刑 / 六害 / 半合 / 三会局 (细节层面)
- 心态卦 (Xin Tai Gua) 识别
- 卦意分析法 (KuaYi 12 Patterns)
"""

from .data import (
    DI_ZHI_WU_XING,
    WU_XING_SHENG, WU_XING_KE,
    LIU_CHONG, LIU_HE,
    SAN_HE, SAN_HUI,
    BAN_HE_PAIRS,
    LIU_HAI,
    JIN_SHEN, TUI_SHEN,
    WU_XING_MU, WU_XING_MU_JIXIONG, MU_BY_ZHI,
    LIU_CHONG_GUA, LIU_HE_GUA,
    get_xing_relations,
    get_chang_sheng,
)




# =============================================================================
# 入墓 (Ru Mu) Detection
# =============================================================================

def detect_ru_mu(hexagram, wangshuai_results, dongbian_results,
                 month_zhi, day_zhi):
    """
    检测三种入墓: 日墓、动墓、化墓.

    据《古筮真诠》第三十五章, 吉凶层面只有两类爻有墓:
    - 寅卯木 墓在未
    - 巳午火 墓在戌
    其它五行的"墓"(金木水火土)只在应期细节层面有效.

    Returns:
        list[dict]: 每个入墓信息
            {position, line_zhi, mu_type(日/动/化), mu_zhi, is_real(真假墓), reason}
    """
    moving_analyses = dongbian_results.get("moving_analyses", {})
    san_he_ju = dongbian_results.get("san_he_ju", [])

    results = []

    for line in hexagram.lines:
        line_wx = line.wu_xing
        # 仅木火两类爻在吉凶层面有墓
        mu_zhi = WU_XING_MU_JIXIONG.get(line_wx)
        if not mu_zhi:
            continue

        ws = wangshuai_results[line.position - 1]
        is_yong_wang = ws["overall"] == "旺"

        # 1. 日墓: 日支 == 该爻五行的墓
        if day_zhi == mu_zhi:
            is_real = True
            reasons = []
            # 假墓判定
            if is_yong_wang:
                is_real = False
                reasons.append("世用旺相被墓为假墓")
            if line.is_moving:
                is_real = False
                reasons.append("动爻被日墓为假墓")
            results.append({
                "position": line.position,
                "line_zhi": line.di_zhi,
                "mu_type": "日墓",
                "mu_zhi": day_zhi,
                "is_real": is_real,
                "reason": "; ".join(reasons) if reasons else f"{line_wx}爻在日墓{day_zhi}",
            })

        # 2. 动墓: 卦中其他动爻地支 == 该爻五行的墓
        for other_line in hexagram.lines:
            if not other_line.is_moving:
                continue
            if other_line.position == line.position:
                continue
            if other_line.di_zhi == mu_zhi:
                # 动墓
                is_real = True
                reasons = []
                if is_yong_wang:
                    is_real = False
                    reasons.append("世用旺相被墓为假墓")
                # 动爻被动墓为假
                if line.is_moving:
                    is_real = False
                    reasons.append("动爻被动墓为假墓")
                results.append({
                    "position": line.position,
                    "line_zhi": line.di_zhi,
                    "mu_type": f"动墓(第{other_line.position}爻{other_line.di_zhi})",
                    "mu_zhi": other_line.di_zhi,
                    "is_real": is_real,
                    "reason": "; ".join(reasons) if reasons else f"{line_wx}爻被动爻{other_line.di_zhi}相墓",
                })

        # 3. 化墓: 该爻自身动而变出墓
        if line.is_moving and line.bian_di_zhi == mu_zhi:
            is_real = True
            reasons = []
            if is_yong_wang:
                is_real = False
                reasons.append("世用旺相化墓为假墓")
            results.append({
                "position": line.position,
                "line_zhi": line.di_zhi,
                "mu_type": "化墓",
                "mu_zhi": line.bian_di_zhi,
                "is_real": is_real,
                "reason": "; ".join(reasons) if reasons else f"{line_wx}爻动化{mu_zhi}入墓",
            })

    return results


# =============================================================================
# 三绊 (San Ban) Detection
# =============================================================================

def detect_san_ban(hexagram, day_zhi, moving_lines=None):
    """
    检测三绊: 日绊、动绊、化绊.

    绊 = 六合关系 (但生克关系优先, 合中带克/带生不算纯绊)
    - 日绊: 动爻或变爻被日支六合
    - 动绊: 两动爻地支六合
    - 化绊: 动爻与其变爻六合

    Returns:
        list[dict]: 每个绊信息
    """
    results = []
    if moving_lines is None:
        moving_lines = hexagram.moving_lines

    # 1. 日绊: 动爻/变爻被日支六合
    he_of_day = LIU_HE.get(day_zhi, (None, None))[0]
    for line in moving_lines:
        if line.di_zhi == he_of_day:
            # 检查是否带生克
            line_wx = line.wu_xing
            day_wx = DI_ZHI_WU_XING[day_zhi]
            has_sheng_ke = (
                WU_XING_SHENG.get(line_wx) == day_wx or
                WU_XING_SHENG.get(day_wx) == line_wx or
                WU_XING_KE.get(line_wx) == day_wx or
                WU_XING_KE.get(day_wx) == line_wx
            )
            results.append({
                "ban_type": "日绊",
                "positions": [line.position],
                "zhis": [line.di_zhi, day_zhi],
                "with_sheng_ke": has_sheng_ke,
                "reason": f"第{line.position}爻动支{line.di_zhi}被日支{day_zhi}六合",
            })

    # 2. 动绊: 两动爻地支六合
    for i, l1 in enumerate(moving_lines):
        for l2 in moving_lines[i + 1:]:
            if LIU_HE.get(l1.di_zhi, (None, None))[0] == l2.di_zhi:
                results.append({
                    "ban_type": "动绊",
                    "positions": [l1.position, l2.position],
                    "zhis": [l1.di_zhi, l2.di_zhi],
                    "with_sheng_ke": False,
                    "reason": f"第{l1.position}爻{l1.di_zhi}与第{l2.position}爻{l2.di_zhi}动而六合",
                })

    # 3. 化绊: 动爻与其变爻六合
    for line in moving_lines:
        if line.bian_di_zhi:
            if LIU_HE.get(line.di_zhi, (None, None))[0] == line.bian_di_zhi:
                results.append({
                    "ban_type": "化绊",
                    "positions": [line.position],
                    "zhis": [line.di_zhi, line.bian_di_zhi],
                    "with_sheng_ke": False,
                    "reason": f"第{line.position}爻{line.di_zhi}动化变爻{line.bian_di_zhi}六合",
                })

    return results


# =============================================================================
# 反吟 (Fan Yin) Detection
# =============================================================================

# 八卦相冲对应关系
TRIGRAM_CHONG = {
    "乾": "巽", "巽": "乾",
    "坤": "震", "震": "坤",
    "坎": "离", "离": "坎",
    "艮": "兑", "兑": "艮",
}


def detect_fan_yin(hexagram, moving_lines=None):
    """
    检测反吟: 反复折腾, 卦象/卦宫/爻动/爻化各种形式.

    Returns:
        dict: {
            "卦象反吟": bool,
            "卦宫反吟": list[str],  # 内卦宫反吟/外卦宫反吟
            "爻动反吟": list[tuple],  # [(pos1, pos2)] 两动爻相冲
            "爻化反吟": list[int],  # [pos] 动爻与变爻相冲
        }
    """
    result = {
        "卦象反吟": False,
        "卦宫反吟": [],
        "爻动反吟": [],
        "爻化反吟": [],
    }

    if moving_lines is None:
        moving_lines = hexagram.moving_lines

    # 1. 卦象反吟: 主卦与变卦六冲, 通过六冲卦变出对冲卦判断
    if hexagram.ben_gua_name in LIU_CHONG_GUA and hexagram.bian_gua_name in LIU_CHONG_GUA:
        # 进一步检查是否为震<->兑、巽<->乾、坎<->离、艮<->坤等纯对冲
        if hexagram.ben_gua_name != hexagram.bian_gua_name:
            # 简化判断: 都是六冲且不同, 视为可能的卦象反吟候选
            # 真实需检查上下卦都互冲
            from .data import HEXAGRAM_BY_NAME
            ben = HEXAGRAM_BY_NAME.get(hexagram.ben_gua_name)
            bian = HEXAGRAM_BY_NAME.get(hexagram.bian_gua_name)
            if ben and bian:
                if (TRIGRAM_CHONG.get(ben["upper"]) == bian["upper"] and
                        TRIGRAM_CHONG.get(ben["lower"]) == bian["lower"]):
                    result["卦象反吟"] = True

    # 2. 卦宫反吟: 主卦的内卦宫与变卦的内卦宫相冲, 或外卦宫相冲
    from .data import HEXAGRAM_BY_NAME
    ben = HEXAGRAM_BY_NAME.get(hexagram.ben_gua_name)
    bian = HEXAGRAM_BY_NAME.get(hexagram.bian_gua_name)
    if ben and bian:
        if TRIGRAM_CHONG.get(ben["lower"]) == bian["lower"]:
            result["卦宫反吟"].append(f"内卦宫反吟({ben['lower']}↔{bian['lower']})")
        if TRIGRAM_CHONG.get(ben["upper"]) == bian["upper"]:
            result["卦宫反吟"].append(f"外卦宫反吟({ben['upper']}↔{bian['upper']})")

    # 3. 爻动反吟: 两动爻地支相冲
    for i, l1 in enumerate(moving_lines):
        for l2 in moving_lines[i + 1:]:
            if LIU_CHONG.get(l1.di_zhi) == l2.di_zhi:
                result["爻动反吟"].append((l1.position, l2.position))

    # 4. 爻化反吟: 动爻与变爻相冲
    for line in moving_lines:
        if line.bian_di_zhi:
            if LIU_CHONG.get(line.di_zhi) == line.bian_di_zhi:
                result["爻化反吟"].append(line.position)

    return result


# =============================================================================
# 伏吟 (Fu Yin) Detection
# =============================================================================

def detect_fu_yin(hexagram, moving_lines=None):
    """
    检测伏吟: 动而不变, 呻吟、哀怨、不宁之象.

    伏吟的标志: 动爻发动后, 变出的地支与本爻一模一样
    或者: 主卦与变卦的内/外卦宫相同(不变)同时有动爻.

    内卦伏吟: 内卦下三爻中有动爻地支与变爻相同
    外卦伏吟: 外卦上三爻中有动爻地支与变爻相同

    Returns:
        dict: {
            "爻动伏吟": list[int],  # [pos] 动爻地支与变爻相同
            "内卦伏吟": bool,
            "外卦伏吟": bool,
        }
    """
    result = {
        "爻动伏吟": [],
        "内卦伏吟": False,
        "外卦伏吟": False,
    }

    inner_fu = False
    outer_fu = False
    if moving_lines is None:
        moving_lines = hexagram.moving_lines

    for line in moving_lines:
        if line.bian_di_zhi:
            if line.di_zhi == line.bian_di_zhi:
                result["爻动伏吟"].append(line.position)
                if line.position <= 3:
                    inner_fu = True
                else:
                    outer_fu = True

    result["内卦伏吟"] = inner_fu
    result["外卦伏吟"] = outer_fu
    return result


# =============================================================================
# 六冲六合卦识别 + 互化模式
# =============================================================================

def detect_chong_he_gua(hexagram, has_moving=None):
    """
    识别六冲卦/六合卦及其互化模式.

    Returns:
        dict: {
            "ben_chong": bool,    # 主卦是否六冲卦
            "ben_he": bool,       # 主卦是否六合卦
            "bian_chong": bool,   # 变卦是否六冲卦
            "bian_he": bool,      # 变卦是否六合卦
            "pattern": str,       # 互化模式标签
            "implication": str,   # 寓意
        }
    """
    ben_name = hexagram.ben_gua_name
    bian_name = hexagram.bian_gua_name

    ben_chong = ben_name in LIU_CHONG_GUA
    ben_he = ben_name in LIU_HE_GUA
    bian_chong = bian_name in LIU_CHONG_GUA
    bian_he = bian_name in LIU_HE_GUA

    # 是否有动爻
    if has_moving is None:
        has_moving = any(l.is_moving for l in hexagram.lines)

    pattern = ""
    implication = ""

    if has_moving and ben_name != bian_name:
        if ben_chong and bian_chong:
            pattern = "六冲变六冲"
            implication = "突发冲起紧接波澜, 短期动荡多变, 持久力缺乏, 败事概率较高"
        elif ben_chong and bian_he:
            pattern = "六冲变六合"
            implication = "事已遭挫破败, 但有目的性预兆破败将得到愈合; 占官非缠身/忧患不结反吉"
        elif ben_he and bian_chong:
            pattern = "六合变六冲"
            implication = "事正处相合状态, 变出六冲昭示原合状态将遭破坏(婚姻蜜月将见纠纷)"
        elif ben_he and bian_he:
            pattern = "六合变六合"
            implication = "拖延加缠绵, 短期急件遇此则不了了之、暂时搁置"
        elif ben_chong and not bian_he and not bian_chong:
            pattern = "主卦六冲"
            implication = "事态多变与突发性, 多反映过去/现在突变"
        elif ben_he and not bian_chong and not bian_he:
            pattern = "主卦六合"
            implication = "事态缠绵不息, 应期延缓"
    else:
        # 静卦或主变同卦
        if ben_chong:
            pattern = "静卦六冲"
            implication = "事态多变, 短期反复; 占病近愈久危"
        elif ben_he:
            pattern = "静卦六合"
            implication = "事态缠绵, 应期延缓"

    return {
        "ben_chong": ben_chong,
        "ben_he": ben_he,
        "bian_chong": bian_chong,
        "bian_he": bian_he,
        "pattern": pattern,
        "implication": implication,
    }


# =============================================================================
# 三刑 / 六害 / 半合 / 三会局 (细节层面)
# =============================================================================

def detect_san_xing(hexagram):
    """检测卦中三刑组合."""
    zhis = [(l.position, l.di_zhi) for l in hexagram.lines]
    results = []

    # 三刑组: 寅巳申、午亥酉
    from .data import SAN_XING_GROUPS, TU_XING, ZI_MAO_XING

    for group in SAN_XING_GROUPS:
        members = [p for p, z in zhis if z in group]
        if len(members) >= 2:
            results.append({
                "type": "三刑",
                "group": list(group),
                "positions": members,
            })

    # 四土自刑/互刑
    tu_members = [p for p, z in zhis if z in TU_XING]
    if len(tu_members) >= 2:
        results.append({
            "type": "土刑",
            "group": list(TU_XING),
            "positions": tu_members,
        })

    # 子卯互刑
    zm_members = [p for p, z in zhis if z in ZI_MAO_XING]
    if len(zm_members) == 2:
        results.append({
            "type": "子卯刑",
            "group": list(ZI_MAO_XING),
            "positions": zm_members,
        })

    return results


def detect_liu_hai(hexagram):
    """检测卦中六害组合."""
    zhis = [(l.position, l.di_zhi) for l in hexagram.lines]
    results = []
    seen = set()
    for p1, z1 in zhis:
        partner = LIU_HAI.get(z1)
        if not partner:
            continue
        for p2, z2 in zhis:
            if p2 == p1:
                continue
            if z2 == partner:
                key = tuple(sorted([p1, p2]))
                if key in seen:
                    continue
                seen.add(key)
                results.append({
                    "positions": [p1, p2],
                    "zhis": [z1, z2],
                    "reason": f"第{p1}爻{z1}与第{p2}爻{z2}相害",
                })
    return results


def detect_san_hui(hexagram):
    """检测卦中三会局 (仅细节层面)."""
    zhis = [l.di_zhi for l in hexagram.lines]
    results = []
    for wx, members in SAN_HUI.items():
        if all(m in zhis for m in members):
            results.append({
                "wu_xing": wx,
                "members": list(members),
            })
    return results


# =============================================================================
# 心态卦 (XinTai Gua) 识别
# =============================================================================

def detect_xintai_gua(hexagram, question_type, yong_shen_liu_qin,
                      yong_shen_lines, dongbian_results):
    """
    识别心态卦.

    明心态卦: 卦题本身就是问心态(担忧/犹豫等), question_type 体现.
    暗心态卦: 事卦用神隐没/异象, 但卦面世应子鬼显着或子孙/官鬼发动.

    Returns:
        dict: {
            "is_xintai": bool,
            "type": "明" / "暗" / None,
            "xi_shen": "子孙",  # 喜神
            "you_shen": "官鬼",  # 忧神
            "signals": list[str],
            "implication": str,
        }
    """
    result = {
        "is_xintai": False,
        "type": None,
        "xi_shen": "子孙",
        "you_shen": "官鬼",
        "signals": [],
        "implication": "",
    }

    # 明心态卦特征: youHuan / 心态相关问题
    if question_type == "youHuan":
        result["is_xintai"] = True
        result["type"] = "明"
        result["signals"].append("question_type=youHuan, 直接判定为明心态卦")
        result["implication"] = "明心态卦: 子孙发动/持世为吉, 官鬼为凶兆"
        return result

    # 暗心态卦特征:
    # 1. 事卦用神不上卦 (用神不存在于卦面)
    # 2. 同时世应/动爻显示子孙或官鬼信号
    if not yong_shen_lines:
        # 用神不现, 检查是否有子孙官鬼显著
        zi_sun_lines = [l for l in hexagram.lines if l.liu_qin == "子孙"]
        guan_gui_lines = [l for l in hexagram.lines if l.liu_qin == "官鬼"]

        zi_sun_active = any(l.is_moving or l.is_shi for l in zi_sun_lines)
        guan_gui_active = any(l.is_moving or l.is_shi for l in guan_gui_lines)

        if zi_sun_active or guan_gui_active:
            result["is_xintai"] = True
            result["type"] = "暗"
            if zi_sun_active:
                result["signals"].append("用神不上卦, 卦中子孙爻动/持世(喜神显)")
            if guan_gui_active:
                result["signals"].append("用神不上卦, 卦中官鬼爻动/持世(忧神显)")
            result["implication"] = "暗心态卦: 心念由事态转为忧虑/喜厌, 据子孙官鬼对比定吉凶"

    return result


# =============================================================================
# 卦意分析法 - KuaYi Patterns Detection
# =============================================================================

def detect_shi_hua_yong_ji(hexagram, yong_shen_liu_qin, ji_shen_liu_qin):
    """
    世化用忌法: 自占, 世动变出用神(吉)或忌神(凶), 不回头作用世爻.

    Returns:
        dict or None
    """
    shi_line = getattr(hexagram, "shi_line", None)
    if not shi_line or not shi_line.is_moving or not shi_line.bian_liu_qin:
        return None

    bian_lq = shi_line.bian_liu_qin
    if bian_lq == yong_shen_liu_qin:
        return {
            "method": "世化用忌法",
            "result": "吉",
            "detail": f"世动化用神({yong_shen_liu_qin}), 用神临身, 事与自身同吉",
        }
    if bian_lq == ji_shen_liu_qin:
        return {
            "method": "世化用忌法",
            "result": "凶",
            "detail": f"世动化忌神({ji_shen_liu_qin}), 忌神临身, 事不利己",
        }
    return None


def detect_shi_dong_hua_gui(hexagram, yong_shen_liu_qin):
    """
    世动化鬼法: 自占, 世爻动变官鬼, 且变出的官鬼非用神/喜悦象.

    寓意: 卦主将被祸患纠缠.
    例外: 父母持世动而化官鬼回头生为吉.

    Returns:
        dict or None
    """
    shi_line = getattr(hexagram, "shi_line", None)
    if not shi_line or not shi_line.is_moving:
        return None

    if shi_line.bian_liu_qin != "官鬼":
        return None

    # 排除: 用神是官鬼则化出官鬼可能为吉
    if yong_shen_liu_qin == "官鬼":
        return None

    # 排除: 父母持世化官鬼回头生
    if shi_line.liu_qin == "父母":
        # 检查是否回头生
        shi_wx = shi_line.wu_xing
        bian_wx = DI_ZHI_WU_XING.get(shi_line.bian_di_zhi or "")
        if bian_wx and WU_XING_SHENG.get(bian_wx) == shi_wx:
            return None  # 卦理回头生优先, 不算化鬼

    return {
        "method": "世动化鬼法",
        "result": "凶",
        "detail": f"世爻({shi_line.liu_qin})动化官鬼({shi_line.bian_di_zhi}), "
                  f"非临场病阻即灾祸临身",
    }


def detect_yong_ji_hu_hua(hexagram, yong_shen_liu_qin, ji_shen_liu_qin,
                          question_type):
    """
    用忌互化法: 代占他事, 用神动变忌神(凶) 或 忌神动变用神(吉).

    Returns:
        dict or None
    """
    # 仅适用于代占类型(此处简化判断: 非自占类型)
    # 假定 question_type 中 hun_male, hun_female 等可能含代占成分
    for line in hexagram.lines:
        if not line.is_moving or not line.bian_liu_qin:
            continue
        if line.liu_qin == yong_shen_liu_qin and line.bian_liu_qin == ji_shen_liu_qin:
            return {
                "method": "用忌互化法",
                "result": "凶",
                "detail": f"用神{yong_shen_liu_qin}动化忌神{ji_shen_liu_qin}, 事败之兆",
            }
        if line.liu_qin == ji_shen_liu_qin and line.bian_liu_qin == yong_shen_liu_qin:
            return {
                "method": "用忌互化法",
                "result": "吉",
                "detail": f"忌神{ji_shen_liu_qin}动化用神{yong_shen_liu_qin}, 阻除事成",
            }
    return None


def detect_gui_yong_hu_hua(hexagram, yong_shen_liu_qin):
    """
    鬼用互化法: 占用神非官鬼, 用神与官鬼互变 → 祸患与事情纠缠.
    """
    if yong_shen_liu_qin == "官鬼":
        return None  # 官鬼为用神不算
    for line in hexagram.lines:
        if not line.is_moving or not line.bian_liu_qin:
            continue
        if (line.liu_qin == yong_shen_liu_qin and line.bian_liu_qin == "官鬼") or \
           (line.liu_qin == "官鬼" and line.bian_liu_qin == yong_shen_liu_qin):
            return {
                "method": "鬼用互化法",
                "result": "凶",
                "detail": f"用神({yong_shen_liu_qin})与官鬼互化, 祸患与事情纠缠",
            }
    return None


def detect_jian_yao_zu_ge(hexagram, yong_shen_lines):
    """
    间爻阻隔法: 世应间爻发动作梗 (无明确指向用神或世爻的卦理).
    """
    shi_line = getattr(hexagram, "shi_line", None)
    ying_line = getattr(hexagram, "ying_line", None)
    if not shi_line or not ying_line:
        return None

    # 间爻位置: 介于世应之间
    pos_low = min(shi_line.position, ying_line.position)
    pos_high = max(shi_line.position, ying_line.position)

    yong_positions = {l.position for l in yong_shen_lines}

    blocking = []
    for line in getattr(hexagram, "moving_lines", hexagram.lines):
        if not (pos_low < line.position < pos_high):
            continue
        # 间爻动 + 既非世应又非用神
        if line.position == shi_line.position or line.position == ying_line.position:
            continue
        if line.position in yong_positions:
            continue
        # 检查是否对世/用产生卦理生克 (简化: 同五行或冲合关系视为有指向)
        line_wx = line.wu_xing
        shi_wx = shi_line.wu_xing
        # 如果与世爻有生克关系, 不算阻隔
        has_targeted = (
            WU_XING_SHENG.get(line_wx) == shi_wx or
            WU_XING_KE.get(line_wx) == shi_wx or
            WU_XING_SHENG.get(shi_wx) == line_wx or
            WU_XING_KE.get(shi_wx) == line_wx
        )
        if not has_targeted:
            blocking.append(line.position)

    if blocking:
        return {
            "method": "间爻阻隔法",
            "result": "凶",
            "detail": f"间爻第{','.join(str(p) for p in blocking)}爻发动作梗, 即使用神旺亦不改凶兆",
        }
    return None


def detect_qian_lian_ju_he(hexagram, yong_shen_lines, dongbian_results):
    """
    牵连聚合法: 世动变用神, 或世用同在三合局, 或动爻聚合三合局.
    """
    shi_line = getattr(hexagram, "shi_line", None)
    if not shi_line:
        return None

    # 1. 世动变用神 = 牵连聚合
    if shi_line.is_moving and yong_shen_lines:
        for yl in yong_shen_lines:
            if shi_line.bian_liu_qin == yl.liu_qin:
                return {
                    "method": "牵连聚合法",
                    "result": "吉",
                    "detail": f"世动({shi_line.di_zhi})变出用神({shi_line.bian_di_zhi}), "
                              f"自身与用神牵连相合",
                }

    # 2. 三合局含世+用
    san_he = dongbian_results.get("san_he_ju", [])
    yong_positions = {l.position for l in yong_shen_lines}
    for sh in san_he:
        # 检查 sh 中是否含世爻和用神爻
        sh_zhis = sh["members"]
        positions_in_he = []
        for line in getattr(hexagram, "moving_lines", hexagram.lines):
            if line.di_zhi in sh_zhis:
                positions_in_he.append(line.position)
        if shi_line.position in positions_in_he:
            yong_in = [p for p in yong_positions if p in positions_in_he]
            if yong_in:
                return {
                    "method": "牵连聚合法",
                    "result": "吉",
                    "detail": f"世爻与用神同在三合{sh['wu_xing']}局, 同局得利",
                }

    return None


def detect_dai_ru(hexagram, yong_shen_lines):
    """
    代入确认法: 与世用同属性或相冲、相合的爻 → 同类竞争对手 / 朋友 / 情敌.
    """
    shi_line = getattr(hexagram, "shi_line", None)
    if not shi_line or not yong_shen_lines:
        return None

    yong = yong_shen_lines[0]
    # 同属性者代表同类 → 求财时用神所同属者代表竞争对手
    same_wx_lines = []
    for line in getattr(hexagram, "moving_lines", hexagram.lines):
        if line.position == yong.position:
            continue
        if line.wu_xing == yong.wu_xing:
            same_wx_lines.append(line.position)

    if same_wx_lines:
        return {
            "method": "代入确认法",
            "result": "提示",
            "detail": f"用神({yong.di_zhi})同属性的第{','.join(str(p) for p in same_wx_lines)}爻"
                      f"动, 寓意竞争对手/同类参与",
        }
    return None


def detect_dong_dong_xiang_lian(hexagram, yong_shen_lines, dongbian_results):
    """
    动动相连法: 多个动爻彼此先连动后聚力, 而非僵化指向世用.
    """
    moving_lines = list(getattr(hexagram, "moving_lines", []))
    if not moving_lines:
        moving_lines = [l for l in hexagram.lines if l.is_moving]
    if len(moving_lines) < 2:
        return None

    # 检查动爻间是否有连续生克
    chain = []
    for i in range(len(moving_lines) - 1):
        l1, l2 = moving_lines[i], moving_lines[i + 1]
        wx1, wx2 = l1.wu_xing, l2.wu_xing
        if WU_XING_SHENG.get(wx1) == wx2:
            chain.append(f"第{l1.position}爻{wx1}生第{l2.position}爻{wx2}")
        elif WU_XING_KE.get(wx1) == wx2:
            chain.append(f"第{l1.position}爻{wx1}克第{l2.position}爻{wx2}")

    if len(chain) >= 1 and len(moving_lines) >= 2:
        return {
            "method": "动动相连法",
            "result": "提示",
            "detail": "动爻间存在连动关系: " + "; ".join(chain),
        }
    return None


# =============================================================================
# 综合卦意分析入口
# =============================================================================

def analyze_kuayi_patterns(hexagram, yong_shen_liu_qin, ji_shen_liu_qin,
                           yong_shen_lines, dongbian_results, question_type):
    """
    综合应用12种卦意分析法识别卦象的特殊模式.

    Returns:
        list[dict]: 检测到的所有卦意模式
    """
    patterns = []

    detectors = [
        lambda: detect_shi_hua_yong_ji(hexagram, yong_shen_liu_qin, ji_shen_liu_qin),
        lambda: detect_shi_dong_hua_gui(hexagram, yong_shen_liu_qin),
        lambda: detect_yong_ji_hu_hua(hexagram, yong_shen_liu_qin, ji_shen_liu_qin,
                                      question_type),
        lambda: detect_gui_yong_hu_hua(hexagram, yong_shen_liu_qin),
        lambda: detect_jian_yao_zu_ge(hexagram, yong_shen_lines),
        lambda: detect_qian_lian_ju_he(hexagram, yong_shen_lines, dongbian_results),
        lambda: detect_dai_ru(hexagram, yong_shen_lines),
        lambda: detect_dong_dong_xiang_lian(hexagram, yong_shen_lines, dongbian_results),
    ]

    for detector in detectors:
        try:
            result = detector()
            if result:
                patterns.append(result)
        except Exception:
            continue

    return patterns


# =============================================================================
# 综合模式识别入口
# =============================================================================

def analyze_structural_patterns(hexagram, wangshuai_results, dongbian_results):
    """计算与具体用神视角无关的结构模式, 供多视角流程复用。"""
    month_zhi = hexagram.gan_zhi["month_zhi"]
    day_zhi = hexagram.gan_zhi["day_zhi"]
    moving_lines = hexagram.moving_lines
    has_moving = bool(moving_lines)

    return {
        "ru_mu": detect_ru_mu(hexagram, wangshuai_results, dongbian_results,
                              month_zhi, day_zhi),
        "san_ban": detect_san_ban(hexagram, day_zhi, moving_lines),
        "fan_yin": detect_fan_yin(hexagram, moving_lines),
        "fu_yin": detect_fu_yin(hexagram, moving_lines),
        "chong_he_gua": detect_chong_he_gua(hexagram, has_moving),
        "san_xing": detect_san_xing(hexagram),
        "liu_hai": detect_liu_hai(hexagram),
        "san_hui": detect_san_hui(hexagram),
    }


def analyze_perspective_patterns(hexagram, dongbian_results,
                                 yong_shen_liu_qin, ji_shen_liu_qin,
                                 yong_shen_lines, question_type):
    """计算依赖用神/问事类型的视角模式。"""
    return {
        "xintai_gua": detect_xintai_gua(hexagram, question_type, yong_shen_liu_qin,
                                        yong_shen_lines, dongbian_results),
        "kuayi_patterns": analyze_kuayi_patterns(
            hexagram, yong_shen_liu_qin, ji_shen_liu_qin,
            yong_shen_lines, dongbian_results, question_type
        ),
    }


def merge_pattern_results(structural_patterns, perspective_patterns):
    """合并结构模式与视角模式, 保持旧版 analyze_all_patterns 返回结构。"""
    merged = dict(structural_patterns or {})
    merged.update(perspective_patterns or {})
    return merged


def analyze_all_patterns(hexagram, wangshuai_results, dongbian_results,
                        yong_shen_liu_qin, ji_shen_liu_qin,
                        yong_shen_lines, question_type):
    """
    一站式分析所有结构模式.

    Returns:
        dict: {
            "ru_mu": [...],
            "san_ban": [...],
            "fan_yin": {...},
            "fu_yin": {...},
            "chong_he_gua": {...},
            "san_xing": [...],
            "liu_hai": [...],
            "san_hui": [...],
            "xintai_gua": {...},
            "kuayi_patterns": [...],
        }
    """
    structural_patterns = analyze_structural_patterns(
        hexagram, wangshuai_results, dongbian_results
    )
    perspective_patterns = analyze_perspective_patterns(
        hexagram, dongbian_results,
        yong_shen_liu_qin, ji_shen_liu_qin,
        yong_shen_lines, question_type,
    )
    return merge_pattern_results(structural_patterns, perspective_patterns)
