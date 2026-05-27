"""
拓扑用神选择模块 - Tuo-Pu Yong-Shen (Topological Use-Spirit Selection)

当标准六亲用神法找不到可用爻时, 采用以下替代方法:
1. 五行类象法: 根据问题关键词匹配五行, 选取对应五行的爻
2. 星煞法: 根据年支/日干计算星煞, 选取带有特定星煞的爻
3. 六神法: 根据问题语境选取带有特定六神的爻
4. 综合选取: 按优先级逐级尝试

主要入口: determine_tuopu_yongshen()
"""

from .data import (
    DI_ZHI_WU_XING,
    get_ma_xing, get_tao_hua, get_wen_chang,
    get_lu_shen, get_jiang_xing,
)
from .jixiong import find_yong_shen_lines, determine_yong_shen


# =============================================================================
# 五行类象 Wu Xing Lei Xiang (Five-Element Class Imagery)
# =============================================================================
# 问题关键词 -> 对应五行

WU_XING_LEI_XIANG = {
    # 金类
    "金融": "金", "金属": "金", "银行": "金", "刀": "金",
    "车": "金", "机械": "金", "五金": "金", "珠宝": "金",
    "矿": "金", "钢": "金", "铁": "金",
    # 木类
    "木材": "木", "家具": "木", "花草": "木", "树木": "木",
    "纸": "木", "书": "木", "教育": "木", "中药": "木",
    "服装": "木", "纺织": "木",
    # 水类
    "水产": "水", "运输": "水", "物流": "水", "航运": "水",
    "酒": "水", "饮料": "水", "旅游": "水", "漂泊": "水",
    "流动": "水", "贸易": "水",
    # 火类
    "电": "火", "电子": "火", "网络": "火", "IT": "火",
    "餐饮": "火", "灯": "火", "能源": "火", "石油": "火",
    "化工": "火", "美容": "火",
    # 土类
    "房": "土", "地产": "土", "建筑": "土", "土地": "土",
    "农业": "土", "陶瓷": "土", "石材": "土", "砖": "土",
    "水泥": "土", "仓储": "土",
}

# 问题关键词 -> 建议星煞类型
XING_SHA_KEYWORDS = {
    "出行": "ma_xing", "旅行": "ma_xing", "远行": "ma_xing",
    "搬家": "ma_xing", "调动": "ma_xing", "出差": "ma_xing",
    "感情": "tao_hua", "桃花": "tao_hua", "恋爱": "tao_hua",
    "暧昧": "tao_hua", "外遇": "tao_hua",
    "考试": "wen_chang", "文书": "wen_chang", "学业": "wen_chang",
    "论文": "wen_chang", "合同": "wen_chang",
    "升职": "lu_shen", "加薪": "lu_shen", "俸禄": "lu_shen",
    "权力": "jiang_xing", "权威": "jiang_xing", "领导": "jiang_xing",
    "军事": "jiang_xing", "竞争": "jiang_xing",
}

# 问题关键词 -> 建议六神
LIU_SHEN_KEYWORDS = {
    "隐秘": "玄武", "暗中": "玄武", "盗窃": "玄武", "欺骗": "玄武",
    "口舌": "朱雀", "官司": "朱雀", "沟通": "朱雀", "消息": "朱雀",
    "伤害": "白虎", "手术": "白虎", "血光": "白虎", "丧事": "白虎",
    "喜事": "青龙", "吉庆": "青龙", "贵人": "青龙",
    "担忧": "螣蛇", "噩梦": "螣蛇", "虚惊": "螣蛇", "怪异": "螣蛇",
    "阻碍": "勾陈", "田土": "勾陈", "牵绊": "勾陈",
}


def select_by_wuxing_leixiang(hexagram, target_wuxing):
    """
    根据目标五行, 从卦中选取地支五行匹配的爻作为替代用神。

    Args:
        hexagram: Hexagram对象
        target_wuxing: 目标五行 (如 "金", "木", "水", "火", "土")

    Returns:
        list: 匹配的爻列表
    """
    results = []
    for line in hexagram.lines:
        if DI_ZHI_WU_XING[line.di_zhi] == target_wuxing:
            results.append(line)
    return results


def select_by_xingsha(hexagram, star_type):
    """
    根据星煞类型, 从卦中选取带有该星煞的爻。

    Args:
        hexagram: Hexagram对象
        star_type: 星煞类型 ("ma_xing"/"tao_hua"/"wen_chang"/"lu_shen"/"jiang_xing")

    Returns:
        list: 匹配的爻列表
    """
    year_zhi = hexagram.gan_zhi.get("year_zhi", "")
    day_gan = hexagram.gan_zhi.get("day_gan", "")

    # 根据星煞类型获取目标地支
    target_zhi = ""
    if star_type == "ma_xing":
        target_zhi = get_ma_xing(year_zhi)
    elif star_type == "tao_hua":
        target_zhi = get_tao_hua(year_zhi)
    elif star_type == "wen_chang":
        target_zhi = get_wen_chang(day_gan)
    elif star_type == "lu_shen":
        target_zhi = get_lu_shen(day_gan)
    elif star_type == "jiang_xing":
        target_zhi = get_jiang_xing(year_zhi)

    if not target_zhi:
        return []

    results = []
    for line in hexagram.lines:
        if line.di_zhi == target_zhi:
            results.append(line)
    return results


def select_by_liushen(hexagram, target_liushen):
    """
    根据六神, 从卦中选取带有该六神的爻。

    Args:
        hexagram: Hexagram对象
        target_liushen: 目标六神 (如 "玄武", "朱雀", "白虎", "青龙", "螣蛇", "勾陈")

    Returns:
        list: 匹配的爻列表
    """
    results = []
    for line in hexagram.lines:
        if line.liu_shen == target_liushen:
            results.append(line)
    return results


def _match_keywords(keywords, mapping):
    """
    从关键词列表中匹配映射表, 返回第一个匹配结果。

    Args:
        keywords: 关键词列表
        mapping: 关键词->值 的映射字典

    Returns:
        匹配的值, 或 None
    """
    for kw in keywords:
        for map_key, map_val in mapping.items():
            if map_key in kw or kw in map_key:
                return map_val
    return None


def determine_tuopu_yongshen(hexagram, question_type, question_keywords=None):
    """
    拓扑用神选择主入口。

    当标准六亲用神法找不到可用爻时, 按优先级尝试替代方法:
    1. 五行类象法
    2. 星煞法
    3. 六神法

    Args:
        hexagram: Hexagram对象
        question_type: 问事类型
        question_keywords: 问事关键词列表 (如 ["金融", "投资", "出行"])

    Returns:
        dict: {
            "method": str,      # 选择方法 ("liu_qin"/"wuxing"/"xingsha"/"liushen"/"none")
            "lines": list,      # 选取的爻列表
            "details": str,     # 说明
        }
    """
    if question_keywords is None:
        question_keywords = []

    # 先尝试标准六亲法
    yong_shen_liu_qin = determine_yong_shen(question_type)
    standard_lines = find_yong_shen_lines(hexagram, yong_shen_liu_qin)

    # 过滤掉旬空的爻
    usable_lines = [l for l in standard_lines if not l.is_xun_kong]

    if usable_lines:
        return {
            "method": "liu_qin",
            "lines": usable_lines,
            "details": f"标准六亲法: {yong_shen_liu_qin}",
        }

    # 标准法无可用爻, 尝试替代方法

    # 1. 五行类象法
    target_wx = _match_keywords(question_keywords, WU_XING_LEI_XIANG)
    if target_wx:
        wx_lines = select_by_wuxing_leixiang(hexagram, target_wx)
        if wx_lines:
            return {
                "method": "wuxing",
                "lines": wx_lines,
                "details": f"五行类象法: 关键词匹配{target_wx}行",
            }

    # 2. 星煞法
    target_star = _match_keywords(question_keywords, XING_SHA_KEYWORDS)
    if target_star:
        star_lines = select_by_xingsha(hexagram, target_star)
        if star_lines:
            return {
                "method": "xingsha",
                "lines": star_lines,
                "details": f"星煞法: 匹配{target_star}",
            }

    # 3. 六神法
    target_liushen = _match_keywords(question_keywords, LIU_SHEN_KEYWORDS)
    if target_liushen:
        liushen_lines = select_by_liushen(hexagram, target_liushen)
        if liushen_lines:
            return {
                "method": "liushen",
                "lines": liushen_lines,
                "details": f"六神法: 匹配{target_liushen}",
            }

    # 所有方法均未匹配
    return {
        "method": "none",
        "lines": [],
        "details": "所有替代方法均未找到可用爻",
    }
