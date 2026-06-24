"""《易冒》金钱卦象法摘要。

ponytail: 只做报告层象法摘要, 不参与吉凶裁决; 以后若要自动断细节再拆规则。
"""

from __future__ import annotations

from typing import Any, Dict, List

from .data import HEXAGRAM_BY_NAME


WU_XING_IMAGE = {
    "木": "东方、青润、生发、文教、舟车、园林、肝胆筋骨",
    "火": "南方、赤燥、文明、火光、市井、眼目心血",
    "土": "中央、黄厚、田宅、坟墓、墙垣、脾胃、迟滞",
    "金": "西方、白肃、刀兵、金玉、刑罚、肺肠、硬物",
    "水": "北方、黑湿、江河、酒食、盗贼、耳肾、流动",
}

LIU_QIN_IMAGE = {
    "父母": "文书、房屋、车船、衣冠、证据、长辈、庇护",
    "官鬼": "职位、疾病、官非、盗贼、压力、丈夫、祸患",
    "兄弟": "同辈、竞争、夺财、阻隔、朋友、墙垣",
    "子孙": "福德、医药、子女、技艺、动物、解厄、享乐",
    "妻财": "财物、妻妾、饮食、货物、仓库、经营资源",
}

LIU_SHEN_IMAGE = {
    "青龙": "喜庆、贵气、文雅、酒色、生发",
    "朱雀": "言语、文书、消息、口舌、诉讼",
    "勾陈": "田土、迟滞、牵连、稳重、跌扑",
    "螣蛇": "虚惊、怪异、缠绕、浮诈、梦幻",
    "白虎": "伤灾、丧服、刀兵、强硬、血光",
    "玄武": "暗昧、盗贼、隐私、酒色、谋略",
}

YAO_WEI_IMAGE = {
    1: "地基、井、足下、近处、幼小、足脚",
    2: "宅内、灶、床、妻妾、臣位、腿腹",
    3: "门内、房、内外交界、兄弟、腰股",
    4: "门外、门户、邻里、母位、心腹胸膈",
    5: "道路、君位、尊位、父位、喉咽脏腑",
    6: "天、屋顶、坟墓、远处、老人祖上、头面",
}

BA_GUA_IMAGE = {
    "乾": "西北、父老、官贵、头肺、寺庙官府城垣马车",
    "坤": "西南、母老妇、腹脾、田野坟墓乡村牛地",
    "震": "东方、长男、足肝、舟车雷动林木道路",
    "巽": "东南、长女妇人、股风、园林花果鸡鹅",
    "坎": "北方、中男盗贼、耳肾、江河井泉陷地",
    "离": "南方、中女文人、目心、市井炉灶火光文书",
    "艮": "东北、少男童仆、手背、山冈坟塚门阙狗虎",
    "兑": "西方、少女口舌、口肺、池泽酒食庵堂说言",
}


def _gua_parts(gua_name: str) -> Dict[str, str]:
    return HEXAGRAM_BY_NAME.get(gua_name, {})


def _line_roles(line: Any, yong_lines: List[Any]) -> List[str]:
    roles = []
    if any(line.position == y.position for y in yong_lines):
        roles.append("用神")
    if getattr(line, "is_shi", False):
        roles.append("世")
    if getattr(line, "is_ying", False):
        roles.append("应")
    if getattr(line, "is_moving", False):
        roles.append("动")
    if getattr(line, "is_xun_kong", False):
        roles.append("空")
    return roles


def analyze_yimao_imagery(hexagram, yong_lines=None, wangshuai_results=None, dongbian_results=None) -> Dict[str, Any]:
    """生成《易冒》象法摘要, 仅供细节分析与报告展示。"""
    yong_lines = yong_lines or []
    wangshuai_results = wangshuai_results or []
    dongbian_results = dongbian_results or {}
    moving_analyses = dongbian_results.get("moving_analyses", {})

    ben = _gua_parts(hexagram.ben_gua_name)
    palace = getattr(hexagram, "palace_name", "")
    trigram_images = []
    for label, gua in (("上卦", ben.get("upper")), ("下卦", ben.get("lower")), ("宫", palace)):
        if gua in BA_GUA_IMAGE:
            trigram_images.append({"label": label, "gua": gua, "image": BA_GUA_IMAGE[gua]})

    line_images = []
    for line in hexagram.lines:
        roles = _line_roles(line, yong_lines)
        if not roles and not line.is_moving:
            continue
        ws = wangshuai_results[line.position - 1] if len(wangshuai_results) >= line.position else {}
        moving = moving_analyses.get(line.position, {})
        line_images.append({
            "position": line.position,
            "roles": roles,
            "liu_qin": line.liu_qin,
            "liu_qin_image": LIU_QIN_IMAGE.get(line.liu_qin, ""),
            "liu_shen": line.liu_shen,
            "liu_shen_image": LIU_SHEN_IMAGE.get(line.liu_shen, ""),
            "wu_xing": line.wu_xing,
            "wu_xing_image": WU_XING_IMAGE.get(line.wu_xing, ""),
            "yao_wei_image": YAO_WEI_IMAGE.get(line.position, ""),
            "wangshuai": ws.get("overall", ""),
            "moving": {
                "bian_zhi": moving.get("bian_zhi"),
                "qu_wang": moving.get("趋旺", []),
                "qu_shuai": moving.get("趋衰", []),
            } if moving else {},
        })

    return {
        "source": "docs/reference/yimao",
        "principle": "用神定吉凶, 象法定细节; 日月定旺衰, 动变定来去; 五行定物类, 六亲定人事, 六神定情状, 爻位/八宫定方所。",
        "trigram_images": trigram_images,
        "line_images": line_images,
    }
