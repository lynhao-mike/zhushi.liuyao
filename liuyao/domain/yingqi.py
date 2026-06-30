"""
应期推断模块 - Ying-Qi (Response Period) Estimation

据《古筮真诠》第四十章常用应期公式归纳, 实现23种应期判断:
1. 静爻逢值逢冲: 旺逢冲, 衰逢值
2. 动爻逢值逢合
3. 月破: 实破/补破/出月破
4. 旬空: 填空/冲空/出空
5. 化进神: 逢值/逢合/逢进
6. 化退神: 逢冲/逢退值
7. 入墓爻: 冲墓/冲爻/出墓
8. 反吟逢值
9. 伏吟逢冲
10. 暗动: 急应当日/逢值/逢合
11. 三合局: 外局喜成临值临合, 内局应破解之期
12. 伏神: 冲飞露伏
13. 多发逢墓
14. 太过逢克墓
15. 太衰逢长生
16. 化绝逢冲生
17. 化破逢实补出
18. 主从应期 (主辅冲值)
19. 应众不应寡
20. 应早不应迟
21. 应邻不应单
22. 应动不应静
23. 长事年月转换/短事日时转换

应期分析层面允许"灵活飘逸": 可论月墓与月绊, 可论半合三会, 可论三刑六害.
"""

from .data import (
    DI_ZHI, DI_ZHI_WU_XING,
    LIU_CHONG, LIU_HE,
    JIN_SHEN, TUI_SHEN,
    WU_XING_SHENG, WU_XING_KE,
    SAN_HE, SAN_HUI,
    WU_XING_MU, MU_BY_ZHI,
    BAN_HE_PAIRS,
)


def _zhi_for_wuxing(target_wx, exclude=()):
    """返回属指定五行的全部地支."""
    return [z for z in DI_ZHI if DI_ZHI_WU_XING[z] == target_wx and z not in exclude]


def _sheng_zhi_of(line_zhi):
    """返回生 line_zhi 的地支列表."""
    line_wx = DI_ZHI_WU_XING[line_zhi]
    sheng_wx = [wx for wx, target in WU_XING_SHENG.items() if target == line_wx]
    if not sheng_wx:
        return []
    return _zhi_for_wuxing(sheng_wx[0], exclude=(line_zhi,))


def _ke_zhi_of(line_zhi):
    """返回克 line_zhi 的地支列表."""
    line_wx = DI_ZHI_WU_XING[line_zhi]
    ke_wx = [wx for wx, target in WU_XING_KE.items() if target == line_wx]
    if not ke_wx:
        return []
    return _zhi_for_wuxing(ke_wx[0], exclude=(line_zhi,))


def estimate_yingqi(line, wangshuai_result, moving_analysis=None,
                    is_yong=False, mu_info=None, ban_info=None,
                    fu_yin_info=None, fan_yin_info=None):
    """
    推断单爻的应期候选, 综合所有可能特殊状态.

    Args:
        line: YaoLine 对象
        wangshuai_result: 该爻旺衰
        moving_analysis: 该爻动变分析(若是动爻)
        is_yong: 是否用神
        mu_info: 该爻入墓信息(若有)
        ban_info: 该爻三绊信息(若有)
        fu_yin_info: 是否伏吟
        fan_yin_info: 是否反吟

    Returns:
        list[str]: 应期候选说明列表(按重要性排序)
    """
    candidates = []
    line_zhi = line.di_zhi
    overall = wangshuai_result["overall"]
    is_yue_po = "月破" in wangshuai_result.get("month_shuai", [])

    chong_zhi = LIU_CHONG.get(line_zhi, "")
    he_zhi = LIU_HE.get(line_zhi, (None, None))[0]

    # 1. 旬空 - 填/冲/出三种应期
    if line.is_xun_kong:
        candidates.append(f"填空: 临值{line_zhi}日/月")
        if chong_zhi:
            candidates.append(f"冲空: {chong_zhi}日/月(冲空则实)")
        candidates.append("出空: 出旬之日")

    # 2. 月破 - 实/补/出三种
    if is_yue_po:
        candidates.append(f"实破: 临值{line_zhi}月/日(逢值填实)")
        if he_zhi:
            candidates.append(f"补破: {he_zhi}月(逢合补破)")
        candidates.append("出月破: 出当月即不破")

    # 3. 入墓爻 - 冲墓/出墓
    if mu_info and mu_info.get("is_real"):
        mu_zhi = mu_info["mu_zhi"]
        chong_mu = LIU_CHONG.get(mu_zhi, "")
        if chong_mu:
            candidates.append(f"冲墓: {chong_mu}日/月(冲走墓库释放)")
        if chong_zhi:
            candidates.append(f"冲爻: {chong_zhi}日/月(冲入墓之爻)")
        candidates.append("出墓: 过冲墓时段后出墓")

    # 4. 三绊 - 解绊
    if ban_info:
        for zhi in ban_info.get("zhis", []):
            if zhi != line_zhi:
                candidates.append(f"解绊: 临值{zhi}日/月(冲合两元素)")

    # 5. 反吟 - 逢值
    if fan_yin_info:
        candidates.append(f"反吟应期: 临值{line_zhi}日/月(动变两端逢值反复)")

    # 6. 伏吟 - 逢冲
    if fu_yin_info and chong_zhi:
        candidates.append(f"伏吟应期: 逢冲{chong_zhi}日/月")

    # 7. 动爻应期
    if line.is_moving and moving_analysis:
        # 7a. 化进神
        if "化进神" in moving_analysis.get("趋旺", []):
            bian_zhi = moving_analysis.get("bian_zhi", "")
            candidates.append(f"逢值: {line_zhi}日/月(化进逢值)")
            if he_zhi:
                candidates.append(f"逢合: {he_zhi}日/月(化进逢合)")
            if bian_zhi in JIN_SHEN:
                jin_zhi = JIN_SHEN[bian_zhi]
                candidates.append(f"逢进: {jin_zhi}日/月(化进再进一步)")

        # 7b. 化退神
        elif "化退神" in moving_analysis.get("趋衰", []):
            bian_zhi = moving_analysis.get("bian_zhi", "")
            if chong_zhi:
                candidates.append(f"逢冲: {chong_zhi}日/月(化退逢冲)")
            if bian_zhi:
                candidates.append(f"逢退值: {bian_zhi}日/月(临退神)")

        # 7c. 化绝
        elif "化绝" in moving_analysis.get("趋衰", []):
            sheng_zhis = _sheng_zhi_of(line_zhi)
            if sheng_zhis:
                candidates.append(f"逢生: {'/'.join(sheng_zhis)}日/月(化绝逢生)")

        # 7d. 化破
        elif "化破" in moving_analysis.get("趋衰", []):
            bian_zhi = moving_analysis.get("bian_zhi", "")
            if bian_zhi:
                candidates.append(f"补化破: 临值{bian_zhi}日/月(逢值填实化破)")

        # 7e. 一般动爻: 逢值/逢合
        else:
            if he_zhi:
                candidates.append(f"逢合: {he_zhi}日/月(动爻待合)")
            candidates.append(f"逢值: {line_zhi}日/月(动爻临值)")

    else:
        # 8. 静爻应期
        if overall == "旺":
            # 旺静逢冲
            if chong_zhi:
                candidates.append(f"逢冲: {chong_zhi}日/月(旺静待冲)")
            else:
                candidates.append(f"逢值: {line_zhi}日/月(无冲则待值)")
        else:
            # 衰静逢值
            candidates.append(f"逢值: {line_zhi}日/月(衰静待值)")
            # 衰静另可逢生
            sheng_zhis = _sheng_zhi_of(line_zhi)
            if sheng_zhis and is_yong:
                candidates.append(f"逢生: {'/'.join(sheng_zhis)}日/月(衰用待生)")

    # 9. 用神特殊: 加上半合应期
    if is_yong:
        for z1, z2, _wx in BAN_HE_PAIRS:
            if line_zhi in (z1, z2):
                other = z2 if line_zhi == z1 else z1
                hint = f"半合: {other}日/月(与{line_zhi}半合)"
                if hint not in candidates:
                    candidates.append(hint)

    # 去重保持顺序
    seen = set()
    deduped = []
    for c in candidates:
        if c not in seen:
            seen.add(c)
            deduped.append(c)

    return deduped


def estimate_yingqi_for_san_he(san_he_ju, hexagram):
    """
    分析三合局的应期.

    Returns:
        list[str]: 三合局应期候选
    """
    if not san_he_ju:
        return []

    candidates = []
    for sh in san_he_ju:
        wx = sh["wu_xing"]
        members = sh["members"]
        # 检查是否完整 (3个全在动爻)
        moving_zhis = {l.di_zhi for l in hexagram.lines if l.is_moving}
        in_moving = [m for m in members if m in moving_zhis]
        in_static = [m for m in members if m not in moving_zhis]

        if len(in_static) == 0:
            # 完整三合, 待局整体临值临合
            candidates.append(
                f"三合{wx}局({'-'.join(members)})成局应期: 临值组成爻或冲破之期"
            )
        elif len(in_static) == 1:
            # 缺一爻待补
            missing = in_static[0]
            chong = LIU_CHONG.get(missing, "")
            candidates.append(
                f"三合{wx}局缺{missing}静爻: 待{missing}临值或被{chong}冲起成局"
            )

    return candidates


def estimate_yingqi_gen(hexagram, primary_yong, wangshuai_results, dongbian_results) -> list[str]:
    """应期卦有根/无根判定: 无根则提示应期意外风险。"""
    candidates = []
    if not primary_yong:
        return candidates
    ws = wangshuai_results[primary_yong.position - 1]
    moving_analyses = dongbian_results.get("moving_analyses", {})
    has_dong = any(l.is_moving for l in hexagram.lines)
    if has_dong:
        return candidates  # ponytail: 有动即排除应期意外, 无需标记; upgrade: 出现有动爻但仍有应期意外的反馈样本时重新评估排除逻辑
    # 静卦: 检查是否有日月生扶
    has_month_support = bool(
        ws.get("month_wang") and any(r in ("临月令", "月令生", "月令扶") for r in ws["month_wang"])
    )
    has_day_support = bool(
        ws.get("day_wang") and any(r in ("临日令", "日令生", "日令扶") for r in ws["day_wang"])
    )
    if not (has_month_support or has_day_support):
        candidates.append("无根提示: 静卦且用神无日月生扶, 应期意外风险, 不可确认必应")
    return candidates


def estimate_yingqi_dujing(hexagram, yong_shen_lines) -> list[str]:
    """独静卦应期: 五爻动一爻静, 独静爻为应期焦点, 逢值逢冲应事。"""
    candidates = []
    moving_count = sum(1 for l in hexagram.lines if l.is_moving)
    if moving_count != 5:
        return candidates
    static = [l for l in hexagram.lines if not l.is_moving]
    if len(static) != 1:
        return candidates
    line = static[0]
    zhi = line.di_zhi
    chong = LIU_CHONG.get(zhi)
    label = f"独静{line.liu_qin}{zhi}"
    if chong:
        candidates.append(f"独静: {zhi}日/月(逢值) 或 {chong}日/月(逢冲)")
    else:
        candidates.append(f"独静: {zhi}日/月(逢值)")
    return candidates


def estimate_yingqi_atypical(line, wangshuai_result, all_results,
                              yong_lines):
    """
    检测特殊应期: 太过 (过旺/过衰).

    太过者损之斯成: 用神过旺, 应在墓绝/逢克之期
    用神过衰, 应在长生/逢生旺之期

    Returns:
        list[str]: 非典型应期
    """
    candidates = []
    line_wx = DI_ZHI_WU_XING[line.di_zhi]
    same_wx_count = sum(
        1 for ws in all_results
        if DI_ZHI_WU_XING[ws["di_zhi"]] == line_wx
    )
    is_yong = any(yl.position == line.position for yl in yong_lines)

    if same_wx_count >= 3 and is_yong:
        # 多发逢墓
        mu_zhi = WU_XING_MU.get(line_wx)
        if mu_zhi:
            candidates.append(f"多发逢墓: 临值{mu_zhi}日/月(同行多发待墓收藏)")

        # 太过逢克
        ke_zhis = _ke_zhi_of(line.di_zhi)
        if ke_zhis:
            candidates.append(f"太过逢克: {'/'.join(ke_zhis)}日/月")

    return candidates


def analyze_yingqi(hexagram, yong_shen_lines, wangshuai_results, dongbian_results,
                   patterns_results=None):
    """
    综合分析用神的应期.

    Args:
        hexagram: Hexagram 对象
        yong_shen_lines: 用神爻列表
        wangshuai_results: 各爻旺衰
        dongbian_results: 动变分析
        patterns_results: 模式识别结果(入墓/三绊/反吟/伏吟)

    Returns:
        list[dict]: 每个用神爻的应期候选
    """
    results = []
    moving_analyses = dongbian_results.get("moving_analyses", {})

    # 提取模式信息并按爻位预索引, 避免每个用神爻重复线性搜索。
    patterns_results = patterns_results or {}
    ru_mu_list = patterns_results.get("ru_mu", [])
    san_ban_list = patterns_results.get("san_ban", [])
    ru_mu_by_position = {m["position"]: m for m in ru_mu_list if "position" in m}
    san_ban_by_position = {}
    for ban in san_ban_list:
        for position in ban.get("positions", []):
            san_ban_by_position.setdefault(position, ban)
    fan_yin = patterns_results.get("fan_yin", {})
    fu_yin = patterns_results.get("fu_yin", {})

    fan_yin_positions = set()
    for poslist in fan_yin.get("爻动反吟", []):
        fan_yin_positions.update(poslist)
    fan_yin_positions.update(fan_yin.get("爻化反吟", []))
    fu_yin_positions = set(fu_yin.get("爻动伏吟", []))

    for line in yong_shen_lines:
        ws = wangshuai_results[line.position - 1]
        ma = moving_analyses.get(line.position)

        # 查找该爻的入墓/三绊信息
        mu_info = ru_mu_by_position.get(line.position)
        ban_info = san_ban_by_position.get(line.position)

        candidates = estimate_yingqi(
            line, ws, ma,
            is_yong=True,
            mu_info=mu_info,
            ban_info=ban_info,
            fu_yin_info=line.position in fu_yin_positions,
            fan_yin_info=line.position in fan_yin_positions,
        )

        # 添加非典型应期(过旺/过衰)
        atypical = estimate_yingqi_atypical(line, ws, wangshuai_results, yong_shen_lines)
        candidates.extend(atypical)

        results.append({
            "position": line.position,
            "di_zhi": line.di_zhi,
            "liu_qin": line.liu_qin,
            "candidates": candidates,
        })

    # 应期卦有根/无根提示
    gen = estimate_yingqi_gen(hexagram, yong_shen_lines[0] if yong_shen_lines else None,
                              wangshuai_results, dongbian_results)
    if gen:
        results.append({"position": 0, "di_zhi": "", "liu_qin": "无根", "candidates": gen})

    # 独静卦应期 (五动一静)
    dujing = estimate_yingqi_dujing(hexagram, yong_shen_lines)
    if dujing:
        results.append({
            "position": 0,
            "di_zhi": "",
            "liu_qin": "独静",
            "candidates": dujing,
        })

    # 三合局应期 (单独添加)
    san_he_yingqi = estimate_yingqi_for_san_he(
        dongbian_results.get("san_he_ju", []), hexagram
    )
    if san_he_yingqi:
        results.append({
            "position": 0,
            "di_zhi": "",
            "liu_qin": "三合局",
            "candidates": san_he_yingqi,
        })

    return results
