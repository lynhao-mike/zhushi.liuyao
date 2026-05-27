"""
伏神/藏爻分析模块 - Fu-Shen / Cang-Yao (Hidden Spirit / Hidden Lines) Analysis

当卦中不现用神(六亲缺失)时, 需从本宫纯卦(伏神)中寻找。
伏神与飞神(寄身爻位的卦中原爻)的关系决定隐藏吉凶和应期。

核心逻辑:
1. 藏爻(get_cang_yao): 获取本宫纯卦所有6爻信息
2. 伏神(find_fu_shen): 找到卦中缺失的六亲在纯卦中的位置
3. 伏神状态(analyze_fu_shen_status): 判断伏神旬空、月破等
4. 伏神吉凶(judge_fushen_jixiong): 三路径判断
5. 伏神应期(estimate_fushen_yingqi): 冲飞露伏/逢值逢合
"""

from .data import (
    NA_JIA, DI_ZHI_WU_XING, PALACE_WU_XING,
    HEXAGRAM_BY_NAME, get_liu_qin,
    LIU_CHONG, LIU_HE,
)


def get_cang_yao(hexagram):
    """
    获取本宫纯卦(本宫卦/伏卦)的6爻信息。

    纯卦为上下卦均为本宫经卦的重卦。
    使用NA_JIA获取纯卦各爻的天干地支。

    Args:
        hexagram: Hexagram对象

    Returns:
        list[dict]: 6个字典, 每个包含 {position, di_zhi, wu_xing, liu_qin, tian_gan}
    """
    palace_name = hexagram.palace_name
    palace_wu_xing = hexagram.palace_wu_xing

    # 纯卦的上下卦都是本宫经卦, 纳甲相同
    na_jia_info = NA_JIA[palace_name]
    tian_gan = na_jia_info[0]
    inner_di_zhi = na_jia_info[1]  # 内卦(下卦) 3爻
    outer_di_zhi = na_jia_info[2]  # 外卦(上卦) 3爻

    cang_yao = []
    for pos in range(1, 7):
        if pos <= 3:
            dz = inner_di_zhi[pos - 1]
        else:
            dz = outer_di_zhi[pos - 4]

        wx = DI_ZHI_WU_XING[dz]
        lq = get_liu_qin(palace_wu_xing, wx)

        cang_yao.append({
            "position": pos,
            "di_zhi": dz,
            "wu_xing": wx,
            "liu_qin": lq,
            "tian_gan": tian_gan,
        })

    return cang_yao


def find_fu_shen(hexagram, target_liu_qin):
    """
    查找伏神: 当卦中缺失某六亲时, 从本宫纯卦中定位。

    Args:
        hexagram: Hexagram对象
        target_liu_qin: 目标六亲 (如 "官鬼", "妻财")

    Returns:
        dict or None: 若卦中已有该六亲返回None;
        否则返回 {position, fu_di_zhi, fu_wu_xing, fu_liu_qin, fu_tian_gan,
                  fei_di_zhi, fei_wu_xing, fei_liu_qin}
    """
    # 检查卦中是否已存在该六亲
    for line in hexagram.lines:
        if line.liu_qin == target_liu_qin:
            return None

    # 卦中不现, 从藏爻中寻找
    cang_yao = get_cang_yao(hexagram)

    for cy in cang_yao:
        if cy["liu_qin"] == target_liu_qin:
            # 找到伏神位置, 获取该位置的飞神(卦中原爻)
            fei_line = hexagram.lines[cy["position"] - 1]
            return {
                "position": cy["position"],
                "fu_di_zhi": cy["di_zhi"],
                "fu_wu_xing": cy["wu_xing"],
                "fu_liu_qin": cy["liu_qin"],
                "fu_tian_gan": cy["tian_gan"],
                "fei_di_zhi": fei_line.di_zhi,
                "fei_wu_xing": fei_line.wu_xing,
                "fei_liu_qin": fei_line.liu_qin,
            }

    # 纯卦中也找不到(理论上不应该出现)
    return None


def analyze_fu_shen_status(fu_shen_info, hexagram):
    """
    分析伏神的状态: 旬空、月破等。

    Args:
        fu_shen_info: find_fu_shen()返回的字典
        hexagram: Hexagram对象

    Returns:
        dict: {fu_kong, fu_po, fei_kong, fei_po, implications}
    """
    month_zhi = hexagram.gan_zhi["month_zhi"]

    fu_dz = fu_shen_info["fu_di_zhi"]
    fei_dz = fu_shen_info["fei_di_zhi"]

    # 伏神旬空
    fu_kong = fu_dz in hexagram.xun_kong

    # 伏神月破: 月支冲伏神地支
    fu_po = LIU_CHONG.get(month_zhi) == fu_dz

    # 飞神旬空
    fei_kong = fei_dz in hexagram.xun_kong

    # 飞神月破
    fei_po = LIU_CHONG.get(month_zhi) == fei_dz

    # 汇总含义
    implications = []
    if fu_kong:
        implications.append("伏神旬空, 所求之事暂无着落")
    if fu_po:
        implications.append("伏神月破, 所求之事难以实现")
    if fei_kong:
        implications.append("飞神旬空, 伏神得以显露")
    if fei_po:
        implications.append("飞神月破, 遮盖无力, 伏神易出")

    if not implications:
        implications.append("伏神状态正常, 待时而出")

    return {
        "fu_kong": fu_kong,
        "fu_po": fu_po,
        "fei_kong": fei_kong,
        "fei_po": fei_po,
        "implications": implications,
    }


def judge_fushen_jixiong(fu_shen_info, fu_status, hexagram,
                         wangshuai_results, dongbian_results):
    """
    伏神吉凶判断, 三路径评估。

    Path 1 - 卦理见凶 (Gua-Li Jian-Xiong):
        伏空(fu_kong): 藏而又空, 志愿难伸
        伏破(fu_po): 藏而又破, 绝望之象
        用藏世伤: 用神伏藏, 世爻又受动爻克

    Path 2 - 卦意预兆 (Gua-Yi Yu-Zhao):
        藏爻确认法: 伏神藏于应爻之下 = 找对门路

    Path 3 - 心态反映 (Xin-Tai Fan-Ying):
        事用伏藏, 但心态用神(子孙或官鬼)旺现于卦面

    Args:
        fu_shen_info: find_fu_shen()结果
        fu_status: analyze_fu_shen_status()结果
        hexagram: Hexagram对象
        wangshuai_results: 旺衰分析结果
        dongbian_results: 动变分析结果

    Returns:
        dict: {path, pattern, ji_xiong, explanation}
    """
    results = []

    # =========================================================================
    # Path 1: 卦理见凶
    # =========================================================================
    # 伏空
    if fu_status["fu_kong"]:
        results.append({
            "path": "卦理",
            "pattern": "伏空",
            "ji_xiong": "凶",
            "explanation": "用神伏藏又逢旬空, 志愿难伸, 所求无望",
        })

    # 伏破
    if fu_status["fu_po"]:
        results.append({
            "path": "卦理",
            "pattern": "伏破",
            "ji_xiong": "凶",
            "explanation": "用神伏藏又逢月破, 事已无救",
        })

    # 用藏世伤: 世爻受动爻克
    interactions = dongbian_results.get("interactions", {})
    shi_line = None
    for line in hexagram.lines:
        if line.is_shi:
            shi_line = line
            break

    if shi_line:
        shi_inter = interactions.get(shi_line.position, {"受克": []})
        if shi_inter["受克"]:
            results.append({
                "path": "卦理",
                "pattern": "用藏世伤",
                "ji_xiong": "凶",
                "explanation": "用神伏藏不现, 世爻又受动爻克伤, 大凶",
            })

    # =========================================================================
    # Path 2: 卦意预兆
    # =========================================================================
    # 伏神藏于应爻之下
    fu_pos = fu_shen_info["position"]
    ying_line = None
    for line in hexagram.lines:
        if line.is_ying:
            ying_line = line
            break

    if ying_line and fu_pos == ying_line.position:
        results.append({
            "path": "卦意",
            "pattern": "伏在应下",
            "ji_xiong": "吉",
            "explanation": "伏神藏于应爻之下, 找对门路之象, 求人可得",
        })

    # =========================================================================
    # Path 3: 心态反映
    # =========================================================================
    # 检查子孙或官鬼是否旺现于卦面(心态用神)
    xintai_liu_qin = ["子孙", "官鬼"]
    xintai_prominent = False
    for line in hexagram.lines:
        if line.liu_qin in xintai_liu_qin:
            ws = wangshuai_results[line.position - 1]
            if ws["overall"] == "旺" and line.is_moving:
                xintai_prominent = True
                break

    if xintai_prominent:
        results.append({
            "path": "心态",
            "pattern": "心态卦疑",
            "ji_xiong": "平",
            "explanation": "用神伏藏不现, 但心态用神旺动于卦面, 疑为心态卦",
        })

    # 综合判断: 取最严重的结果
    if not results:
        return {
            "path": "综合",
            "pattern": "伏而待时",
            "ji_xiong": "平",
            "explanation": "用神伏藏, 暂时不现, 待时机到来方可显露",
        }

    # 优先凶 > 吉 > 平
    xiong_results = [r for r in results if r["ji_xiong"] == "凶"]
    ji_results = [r for r in results if r["ji_xiong"] == "吉"]

    if xiong_results:
        primary = xiong_results[0]
    elif ji_results:
        primary = ji_results[0]
    else:
        primary = results[0]

    # 附加所有发现
    primary["all_findings"] = results
    return primary


def estimate_fushen_yingqi(fu_shen_info, fu_status, hexagram):
    """
    伏神应期推断。

    三种出伏方式:
    1. 冲飞露伏 (chong_fei): 冲去飞神地支之日/月, 伏神显露
    2. 逢值逢合 (lu_fu): 伏神地支逢值或逢六合之日/月
    3. 飞空伏现 (fei_kong_fu_xian): 飞神旬空, 出空期伏神自现

    Args:
        fu_shen_info: find_fu_shen()结果
        fu_status: analyze_fu_shen_status()结果
        hexagram: Hexagram对象

    Returns:
        dict: {chong_fei, lu_fu, fei_kong_fu_xian, candidates}
    """
    fu_dz = fu_shen_info["fu_di_zhi"]
    fei_dz = fu_shen_info["fei_di_zhi"]

    candidates = []

    # 1. 冲飞露伏: 冲掉飞神的地支
    chong_fei_zhi = LIU_CHONG.get(fei_dz, "")
    chong_fei = None
    if chong_fei_zhi:
        chong_fei = chong_fei_zhi
        candidates.append(f"冲飞露伏: {chong_fei_zhi}日/月(冲去飞神{fei_dz})")

    # 2. 逢值逢合: 伏神地支逢值, 或六合伴侣到来
    lu_fu_val = fu_dz
    lu_fu_he = None
    candidates.append(f"逢值: {fu_dz}日/月(伏神逢值而出)")

    if fu_dz in LIU_HE:
        lu_fu_he = LIU_HE[fu_dz][0]
        candidates.append(f"逢合: {lu_fu_he}日/月(伏神逢合而出)")

    # 3. 飞空伏现: 飞神旬空时, 出空期伏神自现
    fei_kong_fu_xian = None
    if fu_status["fei_kong"]:
        fei_kong_fu_xian = fei_dz
        candidates.append(f"飞空伏现: 出旬空期({fei_dz}填实后)伏神自现")

    return {
        "chong_fei": chong_fei,
        "lu_fu": {"feng_zhi": lu_fu_val, "feng_he": lu_fu_he},
        "fei_kong_fu_xian": fei_kong_fu_xian,
        "candidates": candidates,
    }
