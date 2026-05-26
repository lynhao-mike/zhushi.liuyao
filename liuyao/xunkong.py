"""
旬空深层分析模块 - Xun Kong (Void) Enhanced Analysis

区分真空与假空, 旬空特殊应用, 出空方法。
"""

from .data import (
    DI_ZHI, DI_ZHI_WU_XING, LIU_CHONG, LIU_HE,
    WU_XING_SHENG, WU_XING_KE,
)


def is_jia_kong(line, hexagram, wangshuai_result):
    """
    判断旬空爻是否为假空(假空=不为真空)。

    假空条件:
    1. 旺相之静爻 - 旺不为空
    2. 动变之爻(动爻或变爻) - 动不为空

    Args:
        line: YaoLine对象
        hexagram: Hexagram对象
        wangshuai_result: 该爻的旺衰分析结果

    Returns:
        dict: {
            'is_jia_kong': bool,
            'reason': str,
        }
    """
    # 非旬空爻不讨论
    if not line.is_xun_kong:
        return {"is_jia_kong": False, "reason": "非旬空爻"}

    # 条件2: 动爻 - 动不为空
    if line.is_moving:
        return {"is_jia_kong": True, "reason": "动不为空(动爻旬空为假空)"}

    # 检查是否有其他动爻的变爻落入此地支(化空)
    # 化空不为真空
    for other_line in hexagram.lines:
        if other_line.is_moving and other_line.bian_di_zhi:
            if other_line.bian_di_zhi in hexagram.xun_kong:
                # 这是变爻化空的情况, 对变爻而言是假空
                pass

    # 条件1: 旺相之静爻 - 旺不为空
    overall = wangshuai_result.get("overall", "平")
    if not line.is_moving and overall == "旺":
        return {"is_jia_kong": True, "reason": "旺不为空(旺相静爻旬空为假空)"}

    return {"is_jia_kong": False, "reason": "不满足假空条件"}


def is_zhen_kong_yongshen(line, hexagram, wangshuai_results):
    """
    判断用神是否为真空。

    用神真空条件:
    - 静爻(非动爻)
    - 平相或衰弱(不符合用旺条件, 即不达到旺的标准)
    - 理论: 静而平相的用神亦为真空

    Args:
        line: YaoLine对象(用神爻)
        hexagram: Hexagram对象
        wangshuai_results: 全卦旺衰分析结果列表

    Returns:
        dict: {
            'is_zhen_kong': bool,
            'reason': str,
        }
    """
    if not line.is_xun_kong:
        return {"is_zhen_kong": False, "reason": "非旬空爻"}

    # 动爻不为真空
    if line.is_moving:
        return {"is_zhen_kong": False, "reason": "动不为空"}

    ws = wangshuai_results[line.position - 1]
    overall = ws.get("overall", "平")

    # 用神旺则为假空(不为真空)
    if overall == "旺":
        return {"is_zhen_kong": False, "reason": "用神旺相, 旺不为空"}

    # 平相或衰弱的静爻用神 = 真空
    return {
        "is_zhen_kong": True,
        "reason": f"用神静爻旬空且{overall}相, 不符合用旺条件, 为真空",
    }


def is_zhen_kong_shiyao(line, hexagram, wangshuai_results):
    """
    判断世爻是否为真空。

    世爻真空条件:
    - 静爻旬空
    - 日令月令均无生扶(无来自日月的生/扶/合)
    - 或受动爻冲克

    世爻假空条件:
    - 得日月其一生扶(即使总体衰败也不算真空)

    Args:
        line: YaoLine对象(世爻)
        hexagram: Hexagram对象
        wangshuai_results: 全卦旺衰分析结果列表

    Returns:
        dict: {
            'is_zhen_kong': bool,
            'reason': str,
        }
    """
    if not line.is_xun_kong:
        return {"is_zhen_kong": False, "reason": "非旬空爻"}

    # 动爻不为真空
    if line.is_moving:
        return {"is_zhen_kong": False, "reason": "动不为空"}

    ws = wangshuai_results[line.position - 1]

    # 检查日月是否有生扶
    day_wang = ws.get("day_wang", [])
    month_wang = ws.get("month_wang", [])

    # 生扶条件: 日令生/日令扶/日令合/临日建/月令生/月令扶/月令合/临月令
    support_keywords = ["日令生", "日令扶", "日令合", "临日建",
                        "月令生", "月令扶", "月令合", "临月令"]

    has_support = False
    for kw in support_keywords:
        if kw in day_wang or kw in month_wang:
            has_support = True
            break

    # 检查是否受动爻冲克
    has_dong_chong_ke = False
    line_wx = DI_ZHI_WU_XING[line.di_zhi]
    for other_line in hexagram.lines:
        if not other_line.is_moving:
            continue
        if other_line.position == line.position:
            continue
        other_wx = DI_ZHI_WU_XING[other_line.di_zhi]
        # 动爻克世爻
        if WU_XING_KE[other_wx] == line_wx:
            has_dong_chong_ke = True
            break
        # 动爻冲世爻
        if LIU_CHONG.get(other_line.di_zhi) == line.di_zhi:
            has_dong_chong_ke = True
            break

    if has_support and not has_dong_chong_ke:
        return {
            "is_zhen_kong": False,
            "reason": "世爻得日月生扶且未受动爻冲克, 为假空",
        }

    if has_dong_chong_ke:
        return {
            "is_zhen_kong": True,
            "reason": "世爻静空受动爻冲克, 为真空",
        }

    if not has_support:
        return {
            "is_zhen_kong": True,
            "reason": "世爻静空且日月均无生扶, 为真空",
        }

    return {"is_zhen_kong": False, "reason": "世爻旬空但条件不明确"}


def analyze_xunkong_special(hexagram, yong_shen_liu_qin, question_type,
                            wangshuai_results):
    """
    旬空在吉凶判断上的特殊应用。

    五种特殊应用:
    1. 占病用神旬空 = 病况能短期痊愈或暂见好转
    2. 求财兄弟持世空亡 = 短期得财, 不利长久
    3. 行人世空/用神空 = 行人即将归来
    4. 占仕途子孙持世旬空 = 功名难持久
    5. 忧患子孙逢空 = 忧患短期内无法了结

    Args:
        hexagram: Hexagram对象
        yong_shen_liu_qin: 用神六亲名称
        question_type: 问事类型
        wangshuai_results: 旺衰分析结果

    Returns:
        list[dict]: 特殊应用结果
    """
    specials = []

    # 找世爻
    shi_line = None
    for line in hexagram.lines:
        if line.is_shi:
            shi_line = line
            break

    # 找用神爻(旬空的)
    yong_kong_lines = []
    for line in hexagram.lines:
        if line.liu_qin == yong_shen_liu_qin and line.is_xun_kong:
            yong_kong_lines.append(line)

    # 1. 占病用神旬空
    if question_type == "bing" and yong_kong_lines:
        specials.append({
            "type": "占病用神旬空",
            "description": "病况能短期痊愈或暂见好转, 但非最终趋势",
            "note": "近病者痊愈概率较大, 久病者暂见好转",
        })

    # 2. 求财兄弟持世空亡
    if question_type == "cai" and shi_line:
        if shi_line.liu_qin == "兄弟" and shi_line.is_xun_kong:
            specials.append({
                "type": "求财兄弟持世空亡",
                "description": "短期得财, 不利长久之财, 先盈后亏",
                "note": "有小利及时收手, 否则得不偿失",
            })

    # 3. 行人世空/用神空
    if question_type == "xingRen":
        if shi_line and shi_line.is_xun_kong:
            specials.append({
                "type": "行人世空",
                "description": "行人即将归来, 出空必填相见",
                "note": "世爻空亡代表行人将至",
            })
        if yong_kong_lines:
            specials.append({
                "type": "行人用神空",
                "description": "行人即将归来, 出空必填相见",
                "note": "用神空亡代表行人将至",
            })

    # 4. 占仕途子孙持世旬空
    if question_type == "guan" and shi_line:
        if shi_line.liu_qin == "子孙" and shi_line.is_xun_kong:
            specials.append({
                "type": "占仕途子孙持世旬空",
                "description": "短期或有功名, 但功名难持久维系",
                "note": "有得官而终难到任; 有得位却半途被削",
            })

    # 5. 忧患子孙逢空
    if question_type == "youHuan":
        zisun_kong = [l for l in hexagram.lines
                      if l.liu_qin == "子孙" and l.is_xun_kong]
        if zisun_kong:
            specials.append({
                "type": "忧患子孙逢空",
                "description": "忧郁短期内无法了结, 事主将长期忧心忡忡",
                "note": "子孙最终会填空, 事态趋势终将无恙, 非真凶卦",
            })

    return specials


def get_chu_kong_method(line):
    """
    获取旬空爻出空的三种方法。

    三种出空方式:
    1. 填空: 待到值空的时日到来(地支相同)
    2. 冲空: 待到冲空的时日出空(六冲)
    3. 出旬: 待到出了当前旬的时段

    Args:
        line: YaoLine对象

    Returns:
        dict: {
            'tian_kong': str,  # 填空地支
            'chong_kong': str,  # 冲空地支
            'chu_xun': str,  # 出旬说明
        }
    """
    if not line.is_xun_kong:
        return {"tian_kong": "", "chong_kong": "", "chu_xun": "非旬空爻"}

    tian_zhi = line.di_zhi  # 填空: 逢值
    chong_zhi = LIU_CHONG.get(line.di_zhi, "")  # 冲空: 逢冲

    return {
        "tian_kong": f"逢{tian_zhi}日/月填空",
        "chong_kong": f"逢{chong_zhi}日/月冲空",
        "chu_xun": "出旬即出空(过了本旬十天)",
    }


def analyze_xunkong(hexagram, yong_shen_liu_qin, question_type,
                    wangshuai_results):
    """
    旬空综合分析入口。

    Args:
        hexagram: Hexagram对象
        yong_shen_liu_qin: 用神六亲
        question_type: 问事类型
        wangshuai_results: 旺衰分析结果

    Returns:
        dict: 综合旬空分析结果
    """
    # 找所有旬空爻
    kong_lines = [l for l in hexagram.lines if l.is_xun_kong]

    line_analyses = []
    for line in kong_lines:
        ws = wangshuai_results[line.position - 1]

        jia_kong_result = is_jia_kong(line, hexagram, ws)
        chu_kong = get_chu_kong_method(line)

        # 判断是用神还是世爻
        is_yong = (line.liu_qin == yong_shen_liu_qin)
        is_shi = line.is_shi

        zhen_kong_result = None
        if is_yong:
            zhen_kong_result = is_zhen_kong_yongshen(
                line, hexagram, wangshuai_results)
        elif is_shi:
            zhen_kong_result = is_zhen_kong_shiyao(
                line, hexagram, wangshuai_results)

        line_analyses.append({
            "position": line.position,
            "di_zhi": line.di_zhi,
            "liu_qin": line.liu_qin,
            "is_shi": is_shi,
            "is_yong": is_yong,
            "jia_kong": jia_kong_result,
            "zhen_kong": zhen_kong_result,
            "chu_kong": chu_kong,
        })

    # 特殊应用
    specials = analyze_xunkong_special(
        hexagram, yong_shen_liu_qin, question_type, wangshuai_results)

    return {
        "kong_lines": line_analyses,
        "specials": specials,
        "has_kong": len(kong_lines) > 0,
    }
