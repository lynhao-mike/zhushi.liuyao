"""
六冲六合卦分析模块 - Liu Chong / Liu He Hexagram Analysis

分析卦象是否为六冲卦或六合卦, 检测四种互化模式,
动爻趋合分析, 日绊(日合动爻)分析。
"""

from .data import (
    DI_ZHI_WU_XING, LIU_CHONG, LIU_HE,
    WU_XING_SHENG, WU_XING_KE,
    HEXAGRAM_BY_NAME,
)


def _get_hexagram_lines_zhi(hexagram, use_bian=False):
    """
    获取卦的六爻地支列表。

    Args:
        hexagram: Hexagram对象
        use_bian: 是否使用变卦地支(基于变卦的纳甲)

    Returns:
        list[str]: 6个地支
    """
    if not use_bian:
        return [line.di_zhi for line in hexagram.lines]

    # 对于变卦, 需要获取完整的变卦纳甲地支
    # 变卦的地支由变卦的上下经卦决定, 不是简单替换动爻
    bian_zhis = []
    for line in hexagram.lines:
        if line.is_moving and line.bian_di_zhi:
            bian_zhis.append(line.bian_di_zhi)
        else:
            # 非动爻在变卦中的地支取决于变卦的纳甲
            # 如果有任何动爻, 变卦的非动爻位置地支可能与本卦不同
            bian_zhis.append(line.di_zhi)

    # 如果有动爻, 需要用变卦的实际纳甲来获取完整地支
    has_moving = any(l.is_moving for l in hexagram.lines)
    if has_moving:
        from .data import NA_JIA, BINARY_TO_GUA
        # 计算变卦的上下经卦
        bian_lines = []
        for line in hexagram.lines:
            if line.is_moving:
                # 阳变阴, 阴变阳
                bian_lines.append(0 if line.yin_yang == 1 else 1)
            else:
                bian_lines.append(line.yin_yang)

        bian_lower = tuple(bian_lines[0:3])
        bian_upper = tuple(bian_lines[3:6])
        bian_lower_name = BINARY_TO_GUA[bian_lower]
        bian_upper_name = BINARY_TO_GUA[bian_upper]

        # 获取变卦纳甲
        lower_na_jia = NA_JIA[bian_lower_name]
        upper_na_jia = NA_JIA[bian_upper_name]

        bian_zhis = []
        for i in range(6):
            if i < 3:
                bian_zhis.append(lower_na_jia[1][i])
            else:
                bian_zhis.append(upper_na_jia[2][i - 3])

    return bian_zhis


def _is_liu_chong_pattern(zhis):
    """
    判断六爻地支是否构成六冲卦模式。
    六冲卦: 内卦三爻与外卦三爻对应相冲。
    即第1爻冲第4爻, 第2爻冲第5爻, 第3爻冲第6爻。
    """
    if len(zhis) != 6:
        return False
    for i in range(3):
        if LIU_CHONG.get(zhis[i]) != zhis[i + 3]:
            return False
    return True


def _is_liu_he_pattern(zhis):
    """
    判断六爻地支是否构成六合卦模式。
    六合卦: 内卦三爻与外卦三爻对应六合。
    即第1爻合第4爻, 第2爻合第5爻, 第3爻合第6爻。
    """
    if len(zhis) != 6:
        return False
    for i in range(3):
        he_pair = LIU_HE.get(zhis[i])
        if not he_pair or he_pair[0] != zhis[i + 3]:
            return False
    return True


def identify_liu_chong_gua(hexagram):
    """
    识别六冲卦。

    检查本卦(主卦)和变卦是否为六冲卦。
    六冲卦: 内卦三爻地支与外卦三爻地支分别构成六冲关系。
    例如乾为天: 内子寅辰, 外午申戌 (子午冲, 寅申冲, 辰戌冲)

    Args:
        hexagram: Hexagram对象

    Returns:
        dict: {
            'is_liu_chong': bool,
            'type': 'main'/'bian'/'both'/'none',
            'ben_gua_chong': bool,
            'bian_gua_chong': bool,
        }
    """
    # 本卦六冲检查
    ben_zhis = _get_hexagram_lines_zhi(hexagram, use_bian=False)
    ben_is_chong = _is_liu_chong_pattern(ben_zhis)

    # 变卦六冲检查
    bian_zhis = _get_hexagram_lines_zhi(hexagram, use_bian=True)
    bian_is_chong = _is_liu_chong_pattern(bian_zhis)

    # 确定类型
    if ben_is_chong and bian_is_chong:
        gua_type = "both"
    elif ben_is_chong:
        gua_type = "main"
    elif bian_is_chong:
        gua_type = "bian"
    else:
        gua_type = "none"

    return {
        "is_liu_chong": ben_is_chong or bian_is_chong,
        "type": gua_type,
        "ben_gua_chong": ben_is_chong,
        "bian_gua_chong": bian_is_chong,
    }


def identify_liu_he_gua(hexagram):
    """
    识别六合卦。

    检查本卦(主卦)和变卦是否为六合卦。
    六合卦: 内卦三爻地支与外卦三爻地支分别构成六合关系。

    Args:
        hexagram: Hexagram对象

    Returns:
        dict: {
            'is_liu_he': bool,
            'type': 'main'/'bian'/'both'/'none',
            'ben_gua_he': bool,
            'bian_gua_he': bool,
        }
    """
    # 本卦六合检查
    ben_zhis = _get_hexagram_lines_zhi(hexagram, use_bian=False)
    ben_is_he = _is_liu_he_pattern(ben_zhis)

    # 变卦六合检查
    bian_zhis = _get_hexagram_lines_zhi(hexagram, use_bian=True)
    bian_is_he = _is_liu_he_pattern(bian_zhis)

    # 确定类型
    if ben_is_he and bian_is_he:
        gua_type = "both"
    elif ben_is_he:
        gua_type = "main"
    elif bian_is_he:
        gua_type = "bian"
    else:
        gua_type = "none"

    return {
        "is_liu_he": ben_is_he or bian_is_he,
        "type": gua_type,
        "ben_gua_he": ben_is_he,
        "bian_gua_he": bian_is_he,
    }


def analyze_chong_he_huhua(hexagram):
    """
    分析六冲六合互化模式。

    四种模式:
    1. 六合变六冲: 现状缠绵, 趋势将破裂
    2. 六冲变六合: 现状遭破, 趋势将愈合
    3. 六合变六合: 拖延不决, 缠绵趋势加剧
    4. 六冲变六冲: 突发多变, 持久力缺乏

    Args:
        hexagram: Hexagram对象

    Returns:
        dict: {
            'pattern': str or None,
            'meaning': str,
            'ben_is_chong': bool,
            'ben_is_he': bool,
            'bian_is_chong': bool,
            'bian_is_he': bool,
        }
    """
    ben_zhis = _get_hexagram_lines_zhi(hexagram, use_bian=False)
    bian_zhis = _get_hexagram_lines_zhi(hexagram, use_bian=True)

    ben_is_chong = _is_liu_chong_pattern(ben_zhis)
    ben_is_he = _is_liu_he_pattern(ben_zhis)
    bian_is_chong = _is_liu_chong_pattern(bian_zhis)
    bian_is_he = _is_liu_he_pattern(bian_zhis)

    pattern = None
    meaning = ""

    if ben_is_he and bian_is_chong:
        pattern = "六合变六冲"
        meaning = "现状缠绵相合, 趋势将遭破坏分离; 长事见之吉兆不久, 凶兆亦不长"
    elif ben_is_chong and bian_is_he:
        pattern = "六冲变六合"
        meaning = "现状遭受破败, 趋势将愈合修复; 破败之事有转机"
    elif ben_is_he and bian_is_he:
        pattern = "六合变六合"
        meaning = "拖延不决的现状加上缠绵不绝的趋势; 短事变拖沓不了了之"
    elif ben_is_chong and bian_is_chong:
        pattern = "六冲变六冲"
        meaning = "突发多变, 刚起波澜又告平息; 持久力缺乏, 败事概率大于成事"

    return {
        "pattern": pattern,
        "meaning": meaning,
        "ben_is_chong": ben_is_chong,
        "ben_is_he": ben_is_he,
        "bian_is_chong": bian_is_chong,
        "bian_is_he": bian_is_he,
    }


def analyze_dong_yao_quhe(hexagram, dongbian_results):
    """
    分析动爻趋合 (动爻与静爻之间的六合关系)。

    理论:
    - 纯为趋合不带生克才算真正意义上的动而趋合
    - 爻旺被趋合, 得力更旺
    - 爻衰被趋合, 立足不稳, 反被牵引过去
    - 合中带生/合中带克在吉凶判断层面并不能作合断(以生克论)

    Args:
        hexagram: Hexagram对象
        dongbian_results: 动变分析结果

    Returns:
        list[dict]: 每个趋合关系的分析
    """
    moving_analyses = dongbian_results.get("moving_analyses", {})
    useful_moving = dongbian_results.get("useful_moving", [])

    quhe_results = []

    for line in hexagram.lines:
        if not line.is_moving:
            continue
        if line.position not in useful_moving:
            continue

        # 检查是否与静爻六合
        for target in hexagram.lines:
            if target.is_moving:
                continue
            if target.position == line.position:
                continue

            # 检查六合关系
            he_pair = LIU_HE.get(line.di_zhi)
            if not he_pair or he_pair[0] != target.di_zhi:
                continue

            # 确定是否带生克
            dong_wx = DI_ZHI_WU_XING[line.di_zhi]
            jing_wx = DI_ZHI_WU_XING[target.di_zhi]

            has_sheng = (WU_XING_SHENG[dong_wx] == jing_wx)
            has_ke = (WU_XING_KE[dong_wx] == jing_wx)
            is_pure_quhe = not has_sheng and not has_ke

            # 确定类型
            if is_pure_quhe:
                quhe_type = "纯趋合"
                note = "纯合无生克, 真正的动而趋合"
            elif has_sheng:
                quhe_type = "合中带生"
                note = "吉凶层面以生论, 不作合断"
            else:
                quhe_type = "合中带克"
                note = "吉凶层面以克论, 不作合断"

            quhe_results.append({
                "dong_position": line.position,
                "dong_zhi": line.di_zhi,
                "jing_position": target.position,
                "jing_zhi": target.di_zhi,
                "type": quhe_type,
                "is_pure": is_pure_quhe,
                "note": note,
            })

    return quhe_results


def analyze_ri_ban(hexagram, dongbian_results, wangshuai_results):
    """
    日绊分析 - 日支合动爻/变爻形成日绊。

    理论:
    - 静爻得日合则论合旺
    - 动爻/变爻被日合则为日绊
    - 真绊: 动爻衰弱, 被日合绊住无法发挥作用
    - 假绊: 动爻旺相, 日合只是表面, 不真正受绊

    Args:
        hexagram: Hexagram对象
        dongbian_results: 动变分析结果
        wangshuai_results: 旺衰分析结果

    Returns:
        list[dict]: 日绊分析结果
    """
    day_zhi = hexagram.gan_zhi["day_zhi"]
    ri_ban_results = []

    for line in hexagram.lines:
        if not line.is_moving:
            continue

        # 检查动爻本身是否与日支六合
        he_pair = LIU_HE.get(line.di_zhi)
        is_dong_ban = (he_pair is not None and he_pair[0] == day_zhi)

        # 检查变爻是否与日支六合
        is_bian_ban = False
        if line.bian_di_zhi:
            bian_he_pair = LIU_HE.get(line.bian_di_zhi)
            is_bian_ban = (bian_he_pair is not None and bian_he_pair[0] == day_zhi)

        if not is_dong_ban and not is_bian_ban:
            continue

        # 判断真绊假绊
        ws = wangshuai_results[line.position - 1]
        overall = ws["overall"]

        if is_dong_ban:
            if overall == "衰":
                ban_type = "真绊"
                note = "动爻衰弱被日合绊住, 不能发挥作用"
            else:
                ban_type = "假绊"
                note = "动爻旺相, 日合不能真正绊住"
        else:
            # 变爻被日绊
            ban_type = "变爻日绊"
            note = "变爻被日支合住"

        ri_ban_results.append({
            "position": line.position,
            "di_zhi": line.di_zhi,
            "bian_zhi": line.bian_di_zhi,
            "ban_target": "动爻" if is_dong_ban else "变爻",
            "ban_type": ban_type,
            "overall": overall,
            "note": note,
        })

    return ri_ban_results


def analyze_liuchong_liuhe(hexagram, dongbian_results, wangshuai_results):
    """
    六冲六合综合分析入口。

    Args:
        hexagram: Hexagram对象
        dongbian_results: 动变分析结果
        wangshuai_results: 旺衰分析结果

    Returns:
        dict: 综合分析结果
    """
    return {
        "liu_chong": identify_liu_chong_gua(hexagram),
        "liu_he": identify_liu_he_gua(hexagram),
        "chong_he_huhua": analyze_chong_he_huhua(hexagram),
        "dong_yao_quhe": analyze_dong_yao_quhe(hexagram, dongbian_results),
        "ri_ban": analyze_ri_ban(hexagram, dongbian_results, wangshuai_results),
    }
