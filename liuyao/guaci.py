"""
卦辞寓意模块 - Gua-Ci Yu-Yi (Hexagram Text Significance)

实现变卦(bian-gua)的卦辞寓意分析, 包括:
1. 六十四卦卦名寓意字典
2. 六冲卦(Liu-Chong)检测与分析
3. 六合卦(Liu-He)检测与分析
4. 变卦指导建议
5. 反吟/伏吟检测
"""

from typing import Dict, Optional, List

from .data import (
    BA_GUA, BINARY_TO_GUA, HEXAGRAM_BY_NAME,
    LIU_HE, LIU_CHONG, NA_JIA, DI_ZHI_WU_XING,
)


# =============================================================================
# 卦辞寓意字典 - 64卦卦名象征含义
# =============================================================================

GUA_CI_YUYI = {
    # 乾宫
    "乾为天": {"keywords": ["启始", "刚健", "进取"], "guidance": "宜主动进取, 刚健有力", "polarity": "positive"},
    "天风姤": {"keywords": ["邂逅", "相遇", "不期而遇"], "guidance": "宜随缘而动, 不宜强求", "polarity": "neutral"},
    "天山遁": {"keywords": ["退避", "隐遁", "退让"], "guidance": "宜暂避退让, 不宜冒进", "polarity": "negative"},
    "天地否": {"keywords": ["闭塞", "受阻", "不通"], "guidance": "宜静待时变, 暂不可为", "polarity": "negative"},
    "风地观": {"keywords": ["观察", "留意", "审视"], "guidance": "宜继续观察, 不宜急于行动", "polarity": "neutral"},
    "山地剥": {"keywords": ["剥落", "损耗", "衰败"], "guidance": "宜收敛自保, 不宜扩张", "polarity": "negative"},
    "火地晋": {"keywords": ["晋升", "进展", "光明"], "guidance": "宜积极进取, 前途光明", "polarity": "positive"},
    "火天大有": {"keywords": ["丰盛", "收获", "大吉"], "guidance": "宜大胆行动, 收获丰盛", "polarity": "positive"},

    # 兑宫
    "兑为泽": {"keywords": ["言谈", "争讼", "口舌"], "guidance": "宜谨慎言辞, 防口舌之争", "polarity": "neutral"},
    "泽水困": {"keywords": ["围困", "受制", "困窘"], "guidance": "宜忍耐等待, 暂处困境", "polarity": "negative"},
    "泽地萃": {"keywords": ["聚集", "汇合", "萃聚"], "guidance": "宜团结合力, 聚众成事", "polarity": "positive"},
    "泽山咸": {"keywords": ["感应", "交感", "相吸"], "guidance": "宜以诚感人, 彼此呼应", "polarity": "positive"},
    "水山蹇": {"keywords": ["艰难", "险阻", "行路难"], "guidance": "宜知难而退, 暂缓前行", "polarity": "negative"},
    "地山谦": {"keywords": ["谦逊", "退让", "低调"], "guidance": "宜谦虚待人, 低调行事", "polarity": "positive"},
    "雷山小过": {"keywords": ["小过", "稍有不当", "小事"], "guidance": "宜小心行事, 勿犯小错", "polarity": "neutral"},
    "雷泽归妹": {"keywords": ["婚嫁", "归宿", "归附"], "guidance": "宜顺势而为, 寻求归属", "polarity": "neutral"},

    # 离宫
    "离为火": {"keywords": ["艳丽", "显露", "光明"], "guidance": "宜展示自我, 但防虚华", "polarity": "neutral"},
    "火山旅": {"keywords": ["旅行", "往来", "漂泊"], "guidance": "宜外出走动, 不宜久留", "polarity": "neutral"},
    "火风鼎": {"keywords": ["革新", "鼎立", "变革"], "guidance": "宜革故鼎新, 除旧布新", "polarity": "positive"},
    "火水未济": {"keywords": ["未成", "尚需努力", "未完成"], "guidance": "宜继续努力, 事尚未成", "polarity": "neutral"},
    "山水蒙": {"keywords": ["蒙昧", "启蒙", "不明"], "guidance": "宜虚心求教, 开启智慧", "polarity": "neutral"},
    "风水涣": {"keywords": ["涣散", "离散", "化解"], "guidance": "宜疏导化解, 不宜强聚", "polarity": "neutral"},
    "天水讼": {"keywords": ["争讼", "纷争", "对立"], "guidance": "宜和解退让, 不宜争讼", "polarity": "negative"},
    "天火同人": {"keywords": ["同心", "协力", "合作"], "guidance": "宜团结协作, 同心同德", "polarity": "positive"},

    # 震宫
    "震为雷": {"keywords": ["动态", "出行", "震动"], "guidance": "宜果断行动, 但防惊变", "polarity": "neutral"},
    "雷地豫": {"keywords": ["犹豫", "欢愉", "安乐"], "guidance": "宜适度享乐, 不宜过度放纵", "polarity": "neutral"},
    "雷水解": {"keywords": ["解除", "释放", "化解"], "guidance": "宜积极化解, 困难可解", "polarity": "positive"},
    "雷风恒": {"keywords": ["恒久", "持续", "不变"], "guidance": "宜坚持不变, 持之以恒", "polarity": "positive"},
    "地风升": {"keywords": ["上升", "提升", "进步"], "guidance": "宜稳步提升, 循序渐进", "polarity": "positive"},
    "水风井": {"keywords": ["井养", "供给", "资源"], "guidance": "宜深挖资源, 养精蓄锐", "polarity": "neutral"},
    "泽风大过": {"keywords": ["过度", "超限", "承受不住"], "guidance": "宜量力而行, 防过犹不及", "polarity": "negative"},
    "泽雷随": {"keywords": ["跟随", "随顺", "顺应"], "guidance": "宜随机应变, 顺势而行", "polarity": "neutral"},

    # 巽宫
    "巽为风": {"keywords": ["诚信", "跟风", "柔顺"], "guidance": "宜以柔克刚, 诚信待人", "polarity": "neutral"},
    "风天小畜": {"keywords": ["小积蓄", "暂蓄", "力量微薄"], "guidance": "宜小步积累, 暂不可大为", "polarity": "neutral"},
    "风火家人": {"keywords": ["守家", "护财", "家庭"], "guidance": "宜管好钱袋, 守家护财", "polarity": "positive"},
    "风雷益": {"keywords": ["增益", "利益", "进益"], "guidance": "宜大胆进取, 有所增益", "polarity": "positive"},
    "天雷无妄": {"keywords": ["无妨", "无大害", "天真"], "guidance": "宜顺其自然, 无妨碍", "polarity": "positive"},
    "火雷噬嗑": {"keywords": ["咬合", "决断", "去除障碍"], "guidance": "宜果断处理, 除去阻碍", "polarity": "neutral"},
    "山雷颐": {"keywords": ["颐养", "调养", "养生"], "guidance": "宜修身养性, 调养身心", "polarity": "neutral"},
    "山风蛊": {"keywords": ["整治", "腐败", "革除弊端"], "guidance": "宜整顿改革, 除旧迎新", "polarity": "neutral"},

    # 坎宫
    "坎为水": {"keywords": ["陷入", "凹进", "险阻"], "guidance": "宜谨慎小心, 防陷险境", "polarity": "negative"},
    "水泽节": {"keywords": ["限制", "约束", "节制"], "guidance": "宜有节有度, 不宜过分", "polarity": "negative"},
    "水雷屯": {"keywords": ["屯难", "初创", "艰难起步"], "guidance": "宜坚忍不拔, 初创维艰", "polarity": "neutral"},
    "水火既济": {"keywords": ["完成", "已成", "圆满"], "guidance": "宜守成防变, 事已成功", "polarity": "positive"},
    "泽火革": {"keywords": ["变革", "改变", "革命"], "guidance": "宜顺应变革, 改旧图新", "polarity": "neutral"},
    "雷火丰": {"keywords": ["丰盛", "盛大", "鼎盛"], "guidance": "宜趁势而为, 正值丰盛", "polarity": "positive"},
    "地火明夷": {"keywords": ["晦暗", "受伤", "隐藏"], "guidance": "宜韬光养晦, 暂避锋芒", "polarity": "negative"},
    "地水师": {"keywords": ["深入", "追究", "统领"], "guidance": "宜继续深入, 统帅全局", "polarity": "neutral"},

    # 艮宫
    "艮为山": {"keywords": ["阻停", "堆积", "静止"], "guidance": "宜暂时停止, 静待时机", "polarity": "negative"},
    "山火贲": {"keywords": ["礼仪", "粉饰", "装饰"], "guidance": "宜注重礼仪, 但防表面功夫", "polarity": "neutral"},
    "山天大畜": {"keywords": ["大积蓄", "储备", "积累"], "guidance": "宜大力积蓄, 厚积薄发", "polarity": "positive"},
    "山泽损": {"keywords": ["减损", "付出", "舍弃"], "guidance": "宜有所舍弃, 损上益下", "polarity": "neutral"},
    "火泽睽": {"keywords": ["背离", "分歧", "乖离"], "guidance": "宜求同存异, 化解分歧", "polarity": "negative"},
    "天泽履": {"keywords": ["践行", "履行", "如履薄冰"], "guidance": "宜小心履行, 谨慎前行", "polarity": "neutral"},
    "风泽中孚": {"keywords": ["诚信", "中正", "信任"], "guidance": "宜以诚待人, 守信中正", "polarity": "positive"},
    "风山渐": {"keywords": ["渐进", "稳步", "循序"], "guidance": "宜稳步前进, 循序渐进", "polarity": "positive"},

    # 坤宫
    "坤为地": {"keywords": ["包容", "承载", "顺从"], "guidance": "宜柔顺包容, 厚德载物", "polarity": "positive"},
    "地雷复": {"keywords": ["反复", "重复", "回归"], "guidance": "宜反复确认, 回归本源", "polarity": "neutral"},
    "地泽临": {"keywords": ["亲临", "监临", "接近"], "guidance": "宜亲自参与, 临近目标", "polarity": "positive"},
    "地天泰": {"keywords": ["安泰", "通畅", "亨通"], "guidance": "宜大胆行动, 万事亨通", "polarity": "positive"},
    "雷天大壮": {"keywords": ["鼎盛", "成熟", "壮大"], "guidance": "宜乘势而上, 正当壮年", "polarity": "positive"},
    "泽天夬": {"keywords": ["决断", "果决", "突破"], "guidance": "宜果断决策, 当断则断", "polarity": "neutral"},
    "水天需": {"keywords": ["等待", "静观", "需要"], "guidance": "宜静观其变, 耐心等待", "polarity": "neutral"},
    "水地比": {"keywords": ["亲近", "比较", "辅助"], "guidance": "宜亲近合作, 比肩而行", "polarity": "neutral"},
}


def get_guaci_interpretation(bian_gua_name, question_type=None):
    """
    获取变卦的卦辞寓意解读。

    Args:
        bian_gua_name: 变卦名称
        question_type: 问事类型 (可选, 用于上下文解读)

    Returns:
        dict or None: 卦辞寓意信息
    """
    return GUA_CI_YUYI.get(bian_gua_name)


# =============================================================================
# 六冲卦 (Liu-Chong Hexagram) 检测
# =============================================================================

# 八纯卦即六冲卦 (上下卦相同)
LIU_CHONG_GUA_LIST = [
    "乾为天", "坤为地", "坎为水", "离为火",
    "震为雷", "巽为风", "艮为山", "兑为泽",
]


def _is_liuchong_gua(gua_name):
    """判断是否为六冲卦"""
    return gua_name in LIU_CHONG_GUA_LIST


def _is_liuhe_gua(gua_name):
    """
    判断是否为六合卦。
    六合卦: 卦中六爻的地支两两形成六合关系 (1&4, 2&5, 3&6)。
    常见六合卦包括: 地天泰, 天地否, 雷风恒, 风雷益, 水火既济, 火水未济,
    山泽损, 泽山咸, 地泽临, 泽地萃, 水雷屯, 雷水解 等。
    """
    info = HEXAGRAM_BY_NAME.get(gua_name)
    if not info:
        return False

    upper = info["upper"]
    lower = info["lower"]

    # 获取六爻地支
    lower_na_jia = NA_JIA[lower]
    upper_na_jia = NA_JIA[upper]

    # 内卦三爻地支 (位置1,2,3)
    inner_zhis = lower_na_jia[1]  # [初爻, 二爻, 三爻]
    # 外卦三爻地支 (位置4,5,6)
    outer_zhis = upper_na_jia[2]  # [四爻, 五爻, 六爻] (外卦用index 2)

    # 检查三对是否都形成六合
    for i in range(3):
        inner_zhi = inner_zhis[i]
        outer_zhi = outer_zhis[i]
        he_pair = LIU_HE.get(inner_zhi)
        if not he_pair or he_pair[0] != outer_zhi:
            return False

    return True


def analyze_liuchong_gua(ben_gua_name, bian_gua_name):
    """
    六冲卦分析。

    检测本卦和变卦是否为六冲卦, 并判断六冲变六合/六合变六冲的特殊模式。

    Args:
        ben_gua_name: 本卦名称
        bian_gua_name: 变卦名称

    Returns:
        dict: {
            ben_is_liuchong: bool,
            bian_is_liuchong: bool,
            liuchong_gua: str or None,
            implications: {short_term: str, long_term: str},
            special_pattern: str or None  # 'chong_bian_he' or 'he_bian_chong' or None
        }
    """
    ben_is_lc = _is_liuchong_gua(ben_gua_name)
    bian_is_lc = _is_liuchong_gua(bian_gua_name)

    # 确定是哪个六冲卦
    liuchong_gua = None
    if ben_is_lc:
        liuchong_gua = ben_gua_name
    elif bian_is_lc:
        liuchong_gua = bian_gua_name

    # 六冲卦含义
    implications = {"short_term": "", "long_term": ""}
    if ben_is_lc or bian_is_lc:
        implications["short_term"] = "事情变化快, 不持久"
        implications["long_term"] = "不稳定, 难以持续"

    # 特殊模式检测
    special_pattern = None
    ben_is_lh = _is_liuhe_gua(ben_gua_name)
    bian_is_lh = _is_liuhe_gua(bian_gua_name)

    if ben_is_lc and bian_is_lh:
        special_pattern = "chong_bian_he"
        implications["short_term"] = "破后复合, 先散后聚"
        implications["long_term"] = "经历波折后可恢复"
    elif ben_is_lh and bian_is_lc:
        special_pattern = "he_bian_chong"
        implications["short_term"] = "合后散离, 先聚后散"
        implications["long_term"] = "当前合好终将分离"

    return {
        "ben_is_liuchong": ben_is_lc,
        "bian_is_liuchong": bian_is_lc,
        "liuchong_gua": liuchong_gua,
        "implications": implications,
        "special_pattern": special_pattern,
    }


# =============================================================================
# 六合卦 (Liu-He Hexagram) 检测
# =============================================================================

def analyze_liuhe_gua(ben_gua_name, bian_gua_name):
    """
    六合卦分析。

    检测本卦和变卦是否为六合卦, 并判断特殊含义。

    Args:
        ben_gua_name: 本卦名称
        bian_gua_name: 变卦名称

    Returns:
        dict: {
            ben_is_liuhe: bool,
            bian_is_liuhe: bool,
            implications: {short_term: str, long_term: str},
            special_pattern: str or None
        }
    """
    ben_is_lh = _is_liuhe_gua(ben_gua_name)
    bian_is_lh = _is_liuhe_gua(bian_gua_name)

    implications = {"short_term": "", "long_term": ""}
    if ben_is_lh or bian_is_lh:
        # 某些六合卦带有负面含义
        negative_he_gua = ["天地否", "泽水困", "水泽节"]
        target_gua = ben_gua_name if ben_is_lh else bian_gua_name

        if target_gua in negative_he_gua:
            implications["short_term"] = "纠缠拖延, 陷入困局"
            implications["long_term"] = "久困难解, 需等转机"
        else:
            implications["short_term"] = "事情纠缠, 短期难见分晓"
            implications["long_term"] = "持久稳固, 可以长久"

    # 特殊模式: 六合变六冲 / 六冲变六合
    special_pattern = None
    ben_is_lc = _is_liuchong_gua(ben_gua_name)
    bian_is_lc = _is_liuchong_gua(bian_gua_name)

    if ben_is_lh and bian_is_lc:
        special_pattern = "he_bian_chong"
        implications["short_term"] = "合后散离, 先聚后散"
        implications["long_term"] = "当前合好终将分离"
    elif ben_is_lc and bian_is_lh:
        special_pattern = "chong_bian_he"
        implications["short_term"] = "破后复合, 先散后聚"
        implications["long_term"] = "经历波折后可恢复"

    return {
        "ben_is_liuhe": ben_is_lh,
        "bian_is_liuhe": bian_is_lh,
        "implications": implications,
        "special_pattern": special_pattern,
    }


# =============================================================================
# 变卦指导建议
# =============================================================================

def get_bian_gua_guidance(hexagram, jixiong_result, dongbian_results):
    """
    根据变卦的卦辞寓意和吉凶结果, 给出指导建议。

    规则:
    - 凶 + 变卦为六合 -> 宜暂缓搁置
    - 凶 + 变卦为六冲 -> 宜中止放弃
    - 变卦有特定指导含义 -> 返回该指导
    - 吉 -> 不提供指导 (变卦用于客观描述)

    Args:
        hexagram: Hexagram对象
        jixiong_result: 吉凶判断结果 dict
        dongbian_results: 动变分析结果 dict

    Returns:
        str or None: 指导建议文本, 无建议时返回None
    """
    ji_xiong = jixiong_result.get("ji_xiong", "平")
    bian_gua_name = hexagram.bian_gua_name

    # 吉则不提供指导
    if ji_xiong == "吉":
        return None

    # 凶 + 变卦六合
    if ji_xiong == "凶" and _is_liuhe_gua(bian_gua_name):
        return "卦变六合, 宜暂缓搁置, 不宜急进"

    # 凶 + 变卦六冲
    if ji_xiong == "凶" and _is_liuchong_gua(bian_gua_name):
        return "卦变六冲, 宜中止放弃, 不宜继续"

    # 变卦卦辞有特定指导
    guaci = GUA_CI_YUYI.get(bian_gua_name)
    if guaci and guaci.get("guidance"):
        return guaci["guidance"]

    return None


# =============================================================================
# 反吟/伏吟检测
# =============================================================================

# 经卦对冲关系 (二进制全部取反)
# 乾(111)<->坤(000), 兑(110)<->艮(001), 离(101)<->坎(010), 震(100)<->巽(011)
TRIGRAM_OPPOSITES = {
    "乾": "坤", "坤": "乾",
    "兑": "艮", "艮": "兑",
    "离": "坎", "坎": "离",
    "震": "巽", "巽": "震",
}


def detect_gua_fanyin_fuyin(hexagram):
    """
    检测卦象反吟和伏吟。

    反吟(Fan-Yin): 本卦与变卦上下卦分别对冲 (经卦取反)。
    伏吟(Fu-Yin): 本卦与变卦相同 (无实质变化)。

    Args:
        hexagram: Hexagram对象

    Returns:
        dict: {
            fan_yin: bool,
            fu_yin: bool,
            fan_yin_type: 'gua' / 'yao' / None,
            implications: str
        }
    """
    ben_info = HEXAGRAM_BY_NAME.get(hexagram.ben_gua_name)
    bian_info = HEXAGRAM_BY_NAME.get(hexagram.bian_gua_name)

    if not ben_info or not bian_info:
        return {
            "fan_yin": False,
            "fu_yin": False,
            "fan_yin_type": None,
            "implications": "",
        }

    ben_upper = ben_info["upper"]
    ben_lower = ben_info["lower"]
    bian_upper = bian_info["upper"]
    bian_lower = bian_info["lower"]

    # 伏吟检测: 本卦 == 变卦
    fu_yin = (hexagram.ben_gua_name == hexagram.bian_gua_name)

    # 反吟检测: 上下卦分别对冲
    fan_yin = False
    fan_yin_type = None

    upper_opposite = TRIGRAM_OPPOSITES.get(ben_upper)
    lower_opposite = TRIGRAM_OPPOSITES.get(ben_lower)

    if upper_opposite == bian_upper and lower_opposite == bian_lower:
        fan_yin = True
        fan_yin_type = "gua"

    # 爻级反吟: 检查动爻是否全部形成六冲
    if not fan_yin:
        moving_lines = [l for l in hexagram.lines if l.is_moving]
        if moving_lines:
            all_chong = all(
                LIU_CHONG.get(l.di_zhi) == l.bian_di_zhi
                for l in moving_lines
            )
            if all_chong and len(moving_lines) >= 2:
                fan_yin = True
                fan_yin_type = "yao"

    # 含义
    implications = ""
    if fan_yin:
        implications = "反吟: 事情反复不定, 来回折腾"
    elif fu_yin:
        implications = "伏吟: 事情停滞不前, 呻吟不动"

    return {
        "fan_yin": fan_yin,
        "fu_yin": fu_yin,
        "fan_yin_type": fan_yin_type,
        "implications": implications,
    }


# =============================================================================
# 综合分析入口
# =============================================================================

def analyze_guaci(hexagram, jixiong_result, dongbian_results):
    """
    执行完整的卦辞寓意分析。

    Args:
        hexagram: Hexagram对象
        jixiong_result: 吉凶判断结果
        dongbian_results: 动变分析结果

    Returns:
        dict: {
            guaci_interpretation: dict or None,
            liuchong: dict,
            liuhe: dict,
            guidance: str or None,
            fanyin_fuyin: dict,
        }
    """
    bian_gua_name = hexagram.bian_gua_name
    ben_gua_name = hexagram.ben_gua_name

    return {
        "guaci_interpretation": get_guaci_interpretation(bian_gua_name),
        "liuchong": analyze_liuchong_gua(ben_gua_name, bian_gua_name),
        "liuhe": analyze_liuhe_gua(ben_gua_name, bian_gua_name),
        "guidance": get_bian_gua_guidance(hexagram, jixiong_result, dongbian_results),
        "fanyin_fuyin": detect_gua_fanyin_fuyin(hexagram),
    }
