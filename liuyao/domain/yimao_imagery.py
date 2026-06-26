"""《易冒》金钱卦象法摘要。

ponytail: 只做报告层象法摘要, 不参与吉凶裁决; 以后若要自动断细节再拆规则。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .data import HEXAGRAM_BY_NAME


WU_XING_IMAGE = {
    "木": {"image": "东方、青润、生发、文教、舟车、园林、肝胆筋骨", "source": "易冒·五行章第五", "relevant_to": None},
    "火": {"image": "南方、赤燥、文明、火光、市井、眼目心血", "source": "易冒·五行章第五", "relevant_to": None},
    "土": {"image": "中央、黄厚、田宅、坟墓、墙垣、脾胃、迟滞", "source": "易冒·五行章第五", "relevant_to": None},
    "金": {"image": "西方、白肃、刀兵、金玉、刑罚、肺肠、硬物", "source": "易冒·五行章第五", "relevant_to": None},
    "水": {"image": "北方、黑湿、江河、酒食、盗贼、耳肾、流动", "source": "易冒·五行章第五", "relevant_to": None},
}

LIU_QIN_IMAGE = {
    "父母": {"image": "文书、房屋、车船、衣冠、证据、长辈、庇护", "source": "易冒·六亲章第六", "relevant_to": ["kaoshi", "shiwu", "other"]},
    "官鬼": {"image": "职位、疾病、官非、盗贼、压力、丈夫、祸患", "source": "易冒·六亲章第六", "relevant_to": ["guan", "bing", "hun_female", "other"]},
    "兄弟": {"image": "同辈、竞争、夺财、阻隔、朋友、墙垣", "source": "易冒·六亲章第六", "relevant_to": None},
    "子孙": {"image": "福德、医药、子女、技艺、动物、解厄、享乐", "source": "易冒·六亲章第六", "relevant_to": ["zinv", "bing", "youHuan", "other"]},
    "妻财": {"image": "财物、妻妾、饮食、货物、仓库、经营资源", "source": "易冒·六亲章第六", "relevant_to": ["cai", "shengyi", "shiwu", "hun_male", "other"]},
}

LIU_SHEN_IMAGE = {
    "青龙": {"image": "喜庆、贵气、文雅、酒色、生发", "source": "易冒·六神章第七", "relevant_to": None},
    "朱雀": {"image": "言语、文书、消息、口舌、诉讼", "source": "易冒·六神章第七", "relevant_to": None},
    "勾陈": {"image": "田土、迟滞、牵连、稳重、跌扑", "source": "易冒·六神章第七", "relevant_to": None},
    "螣蛇": {"image": "虚惊、怪异、缠绕、浮诈、梦幻", "source": "易冒·六神章第七", "relevant_to": None},
    "白虎": {"image": "伤灾、丧服、刀兵、强硬、血光", "source": "易冒·六神章第七", "relevant_to": None},
    "玄武": {"image": "暗昧、盗贼、隐私、酒色、谋略", "source": "易冒·六神章第七", "relevant_to": None},
}

YAO_WEI_IMAGE = {
    1: {"image": "地基、井、足下、近处、幼小、足脚", "source": "易冒·间爻章第十"},
    2: {"image": "宅内、灶、床、妻妾、臣位、腿腹", "source": "易冒·间爻章第十"},
    3: {"image": "门内、房、内外交界、兄弟、腰股", "source": "易冒·间爻章第十"},
    4: {"image": "门外、门户、邻里、母位、心腹胸膈", "source": "易冒·间爻章第十"},
    5: {"image": "道路、君位、尊位、父位、喉咽脏腑", "source": "易冒·间爻章第十"},
    6: {"image": "天、屋顶、坟墓、远处、老人祖上、头面", "source": "易冒·间爻章第十"},
}

BA_GUA_IMAGE = {
    "乾": {"image": "西北、父老、官贵、头肺、寺庙官府城垣马车", "source": "易冒·五行章第五"},
    "坤": {"image": "西南、母老妇、腹脾、田野坟墓乡村牛地", "source": "易冒·五行章第五"},
    "震": {"image": "东方、长男、足肝、舟车雷动林木道路", "source": "易冒·五行章第五"},
    "巽": {"image": "东南、长女妇人、股风、园林花果鸡鹅", "source": "易冒·五行章第五"},
    "坎": {"image": "北方、中男盗贼、耳肾、江河井泉陷地", "source": "易冒·五行章第五"},
    "离": {"image": "南方、中女文人、目心、市井炉灶火光文书", "source": "易冒·五行章第五"},
    "艮": {"image": "东北、少男童仆、手背、山冈坟塚门阙狗虎", "source": "易冒·五行章第五"},
    "兑": {"image": "西方、少女口舌、口肺、池泽酒食庵堂说言", "source": "易冒·五行章第五"},
}

# 各问事类型侧重的六亲象 (ponytail: 只列高频的，不做九十章全量映射)
QUESTION_TYPE_FOCUS: Dict[str, List[str]] = {
    "shiwu":    ["父母", "妻财"],          # 失物: 物件本体+财值
    "bing":     ["官鬼", "子孙"],          # 疾病: 病源+药效
    "cai":      ["妻财", "子孙", "兄弟"],  # 求财: 财+元神+耗神
    "shengyi":  ["妻财", "子孙", "兄弟"],
    "hun_male": ["妻财", "官鬼"],          # 婚姻男: 妻+情敌
    "hun_female":["官鬼", "妻财"],         # 婚姻女: 夫+竞争
    "guan":     ["官鬼", "父母"],          # 功名: 官+文书
    "kaoshi":   ["父母", "官鬼"],          # 考试: 文书+名声
    "zinv":     ["子孙", "父母"],          # 子女: 子孙+抚育
    "youHuan":  ["子孙", "官鬼"],          # 忧患: 解厄+祸源
}


# 高频六神×六亲组合线索句
# ponytail: 硬编码 8 条最高频组合，不做规则引擎；验证效果后再泛化
_COMBO_SENTENCES: List[Dict[str, Any]] = [
    {
        "liu_shen": "白虎", "liu_qin": "官鬼", "is_moving": True,
        "sentence": "白虎临官鬼发动，官非伤灾之象，宜防纠纷病损。",
        "source": "易冒·六神章第七",
        "signal_type": "象法警示",
    },
    {
        "liu_shen": "白虎", "liu_qin": "官鬼", "is_moving": False,
        "sentence": "白虎临官鬼静处，潜在压力之象，注意健康与官事。",
        "source": "易冒·六神章第七",
        "signal_type": "象法警示",
    },
    {
        "liu_shen": "青龙", "liu_qin": "妻财", "wangshuai": "旺",
        "sentence": "青龙持妻财旺相，财禄有望，喜庆之事可期。",
        "source": "易冒·六神章第七",
        "signal_type": "象法印证",
    },
    {
        "liu_shen": "玄武", "liu_qin": "兄弟", "is_moving": True,
        "sentence": "玄武临兄弟发动，暗中耗财阻隔之象，防小人暗损。",
        "source": "易冒·六神章第七",
        "signal_type": "象法警示",
    },
    {
        "liu_shen": "朱雀", "liu_qin": "父母", "is_moving": True,
        "sentence": "朱雀临父母发动，文书口舌之象，合同证件宜仔细核查。",
        "source": "易冒·六神章第七",
        "signal_type": "象法警示",
    },
    {
        "liu_shen": "螣蛇", "liu_qin": "官鬼", "is_moving": True,
        "sentence": "螣蛇临官鬼发动，虚惊怪异或惊恐之事，防精神压力。",
        "source": "易冒·六神章第七",
        "signal_type": "象法警示",
    },
    {
        "liu_shen": "青龙", "liu_qin": "子孙", "wangshuai": "旺",
        "sentence": "青龙临子孙旺相，福德喜庆之象，子嗣或医药有佳兆。",
        "source": "易冒·六神章第七",
        "signal_type": "象法印证",
    },
    {
        "liu_shen": "白虎", "liu_qin": "父母", "is_moving": True,
        "sentence": "白虎临父母发动，文书房产受损或长辈病伤之象，宜关注。",
        "source": "易冒·六神章第七",
        "signal_type": "象法警示",
    },
    # 六亲持世组合（来源：易冒·身命章第四十六）
    {
        "liu_qin": "子孙", "is_shi": True,
        "sentence": "子孙持世，福德当令，百事皆宜趋吉，医药求福有佳兆。",
        "source": "易冒·身命章第四十六",
        "signal_type": "象法印证",
    },
    {
        "liu_qin": "官鬼", "is_shi": True, "is_moving": True,
        "sentence": "官鬼持世又发动，变动压力涌现，求名可期但防多变之劳。",
        "source": "易冒·身命章第四十六",
        "signal_type": "象法警示",
    },
    {
        "liu_qin": "兄弟", "is_shi": True, "is_moving": True,
        "sentence": "兄弟持世发动，竞争阻滞之象，义利相争需持中。",
        "source": "易冒·身命章第四十六",
        "signal_type": "象法警示",
    },
    {
        "liu_qin": "妻财", "is_shi": True, "wangshuai": "旺",
        "sentence": "妻财持世旺相，资财豫足之象，经营谋利可顺势而进。",
        "source": "易冒·身命章第四十六",
        "signal_type": "象法印证",
    },
    {
        "liu_qin": "父母", "is_shi": True,
        "sentence": "父母持世，劳碌操持之象，文书证件为要，宜勤而不宜懈。",
        "source": "易冒·身命章第四十六",
        "signal_type": "象法印证",
    },
    # 青龙/玄武与妻财应爻组合（来源：易冒·婚姻章第五十一）
    {
        "liu_shen": "青龙", "liu_qin": "妻财", "is_ying": True,
        "sentence": "应爻妻财逢青龙，对方富贵喜庆，婚谋财事有良象。",
        "source": "易冒·婚姻章第五十一",
        "signal_type": "象法印证",
    },
    {
        "liu_shen": "玄武", "liu_qin": "妻财", "is_ying": True,
        "sentence": "应爻妻财逢玄武，风流奸巧之嫌，婚谋财事宜多加审慎。",
        "source": "易冒·婚姻章第五十一",
        "signal_type": "象法警示",
    },
    # 朱雀与官鬼组合（来源：易冒·年运章第四十七）
    {
        "liu_shen": "朱雀", "liu_qin": "官鬼", "is_moving": True,
        "sentence": "朱雀临官鬼发动，口舌官非之象，防言语文书引起纠纷。",
        "source": "易冒·年运章第四十七",
        "signal_type": "象法警示",
    },
    # 勾陈与妻财组合
    {
        "liu_shen": "勾陈", "liu_qin": "妻财", "is_moving": True,
        "sentence": "勾陈临妻财发动，田产土地之利，或财事迟滞牵连。",
        "source": "易冒·六神章第七",
        "signal_type": "象法印证",
    },
    # 旬空组合（来源：易冒·旬空章第十七）
    {
        "liu_qin": "妻财", "is_xun_kong": True,
        "sentence": "妻财旬空，财力暂虚，待出空后方见财效，急进反误。",
        "source": "易冒·旬空章第十七",
        "signal_type": "象法警示",
    },
    {
        "liu_qin": "官鬼", "is_xun_kong": True,
        "sentence": "官鬼旬空，官非病忧暂缓，出空后须留意变数。",
        "source": "易冒·旬空章第十七",
        "signal_type": "象法印证",
    },
    {
        "liu_qin": "子孙", "is_xun_kong": True,
        "sentence": "子孙旬空，福神力弱，医药化解之效暂时不显。",
        "source": "易冒·旬空章第十七",
        "signal_type": "象法警示",
    },
    # 用神动变组合（来源：易冒·动变章第十四）
    {
        "liu_qin": "妻财", "is_moving": True, "wangshuai": "旺",
        "sentence": "妻财动而旺相，财机涌现，宜抓住时机主动出击。",
        "source": "易冒·动变章第十四",
        "signal_type": "象法印证",
    },
    {
        "liu_qin": "官鬼", "is_moving": True, "wangshuai": "旺",
        "sentence": "官鬼动而旺相，官威或病气盛发，宜防事态扩大。",
        "source": "易冒·动变章第十四",
        "signal_type": "象法警示",
    },
    {
        "liu_qin": "兄弟", "is_moving": True, "wangshuai": "旺",
        "sentence": "兄弟动而旺相，竞争耗财之力强，财事宜守不宜冒进。",
        "source": "易冒·动变章第十四",
        "signal_type": "象法警示",
    },
    {
        "liu_qin": "父母", "is_moving": True, "wangshuai": "旺",
        "sentence": "父母动而旺相，文书证件有动，长辈事宜留意。",
        "source": "易冒·动变章第十四",
        "signal_type": "象法印证",
    },
    # 世爻六神（来源：易冒·年运章第四十七）
    {
        "liu_shen": "青龙", "is_shi": True,
        "sentence": "世爻逢青龙，身命喜庆有气，问事多有贵人相助。",
        "source": "易冒·年运章第四十七",
        "signal_type": "象法印证",
    },
    {
        "liu_shen": "白虎", "is_shi": True,
        "sentence": "世爻逢白虎，身命有伤灾之象，宜防意外及健康变化。",
        "source": "易冒·年运章第四十七",
        "signal_type": "象法警示",
    },
    {
        "liu_shen": "玄武", "is_shi": True,
        "sentence": "世爻逢玄武，事多暗昧难明，防小人暗中作梗。",
        "source": "易冒·年运章第四十七",
        "signal_type": "象法警示",
    },
    {
        "liu_shen": "螣蛇", "is_shi": True,
        "sentence": "世爻逢螣蛇，心神不宁，多虚惊怪梦，宜稳定情绪。",
        "source": "易冒·年运章第四十七",
        "signal_type": "象法警示",
    },
    # 应爻六神（来源：易冒·婚姻章第五十一）
    {
        "liu_shen": "白虎", "is_ying": True,
        "sentence": "应爻逢白虎，对方有伤灾强硬之气，往来宜谨慎。",
        "source": "易冒·婚姻章第五十一",
        "signal_type": "象法警示",
    },
    {
        "liu_shen": "青龙", "is_ying": True,
        "sentence": "应爻逢青龙，对方喜庆有气，合作谋事有利。",
        "source": "易冒·婚姻章第五十一",
        "signal_type": "象法印证",
    },
    # 子孙动克官鬼（来源：易冒·疾病章第五十八）
    {
        "liu_qin": "子孙", "is_moving": True,
        "sentence": "子孙发动，福神克制官鬼，忧患病患有望化解。",
        "source": "易冒·疾病章第五十八",
        "signal_type": "象法印证",
    },
    # 官鬼临应爻动（来源：易冒·疾病章第五十八）
    {
        "liu_qin": "官鬼", "is_ying": True, "is_moving": True,
        "sentence": "官鬼临应爻发动，对方或外部有病忧压力之象，宜防波及。",
        "source": "易冒·疾病章第五十八",
        "signal_type": "象法警示",
    },
    # 世应关系类（来源：易冒·世应章第八、年运章第四十七）
    {
        "liu_qin": "父母", "is_ying": True,
        "sentence": "应爻父母显现，对方重文书礼节，往来多凭手续名义。",
        "source": "易冒·世应章第八",
        "signal_type": "象法印证",
    },
    {
        "liu_qin": "兄弟", "is_ying": True,
        "sentence": "应爻兄弟显现，对方竞争心重，往来易有分利相争。",
        "source": "易冒·世应章第八",
        "signal_type": "象法警示",
    },
    {
        "liu_qin": "子孙", "is_ying": True,
        "sentence": "应爻子孙显现，对方态度偏松和，事情有缓转余地。",
        "source": "易冒·世应章第八",
        "signal_type": "象法印证",
    },
    {
        "liu_shen": "朱雀", "is_ying": True,
        "sentence": "应爻逢朱雀，对方以言语信息先动，宜防口舌反复。",
        "source": "易冒·六神章第七",
        "signal_type": "象法警示",
    },
    {
        "liu_shen": "玄武", "is_ying": True,
        "sentence": "应爻逢玄武，对方多隐情暗意，表里未必一致。",
        "source": "易冒·六神章第七",
        "signal_type": "象法警示",
    },
    {
        "liu_shen": "勾陈", "is_shi": True,
        "sentence": "世爻逢勾陈，自身心态偏稳但事易拖延，宜防牵连滞缓。",
        "source": "易冒·年运章第四十七",
        "signal_type": "象法警示",
    },
    {
        "liu_shen": "朱雀", "is_shi": True,
        "sentence": "世爻逢朱雀，事由言语文章而起，宜慎口慎文。",
        "source": "易冒·年运章第四十七",
        "signal_type": "象法警示",
    },
    {
        "liu_qin": "妻财", "is_ying": True, "is_moving": True,
        "sentence": "应爻妻财发动，对方因利而动，财事婚事多见现实考量。",
        "source": "易冒·婚姻章第五十一",
        "signal_type": "象法印证",
    },
    # 婚姻专项（来源：易冒·婚姻章第五十一）
    {
        "liu_qin": "妻财", "is_ying": True, "is_xun_kong": True,
        "sentence": "应爻妻财逢空，对方心意未定，男占婚事宜防热度有名无实。",
        "source": "易冒·婚姻章第五十一",
        "signal_type": "象法警示",
    },
    {
        "liu_qin": "官鬼", "is_ying": True, "is_xun_kong": True,
        "sentence": "应爻官鬼逢空，对方名分未定，女占婚事宜防承诺落空。",
        "source": "易冒·婚姻章第五十一",
        "signal_type": "象法警示",
    },
    {
        "liu_qin": "妻财", "is_ying": True, "wangshuai": "旺",
        "sentence": "应爻妻财旺相，男占婚事多见对方条件不弱，婚缘可议。",
        "source": "易冒·婚姻章第五十一",
        "signal_type": "象法印证",
    },
    {
        "liu_qin": "官鬼", "is_ying": True, "wangshuai": "旺",
        "sentence": "应爻官鬼旺相，女占婚事多见对方有主见有担当，但也较强势。",
        "source": "易冒·婚姻章第五十一",
        "signal_type": "象法印证",
    },
    {
        "liu_qin": "妻财", "is_shi": True, "is_moving": True,
        "sentence": "世爻妻财发动，男方自身动念求合，婚事多由己方主动推进。",
        "source": "易冒·婚姻章第五十一",
        "signal_type": "象法印证",
    },
    # 求财/经营专项（来源：易冒·理财章第六十六）
    {
        "liu_qin": "妻财", "is_shi": True,
        "sentence": "世爻持财，自身财念重，求财多靠主动经营与把握时机。",
        "source": "易冒·理财章第六十六",
        "signal_type": "象法印证",
    },
    {
        "liu_qin": "兄弟", "is_moving": True, "is_ying": True,
        "sentence": "应爻兄弟发动，求财路上易遇同业竞争、分利耗财之事。",
        "source": "易冒·理财章第六十六",
        "signal_type": "象法警示",
    },
    {
        "liu_qin": "父母", "is_moving": True, "is_ying": True,
        "sentence": "应爻父母发动，求财多凭票据合同、门路文书，不可粗疏。",
        "source": "易冒·理财章第六十六",
        "signal_type": "象法印证",
    },
    {
        "liu_qin": "子孙", "is_shi": True, "wangshuai": "旺",
        "sentence": "世爻子孙旺相，求财有福气与变通，宜顺势取巧，不宜死守。",
        "source": "易冒·理财章第六十六",
        "signal_type": "象法印证",
    },
    {
        "liu_qin": "兄弟", "is_shi": True, "wangshuai": "旺",
        "sentence": "世爻兄弟旺相，求财心切却易耗财，宜防合伙失利或竞逐过度。",
        "source": "易冒·理财章第六十六",
        "signal_type": "象法警示",
    },
    {
        "liu_qin": "官鬼", "is_moving": True, "is_shi": False,
        "sentence": "官鬼发动临财局，经营途中多见政策、风险、债务或压力干扰。",
        "source": "易冒·理财章第六十六",
        "signal_type": "象法警示",
    },
    {
        "liu_shen": "玄武", "liu_qin": "妻财", "is_moving": True,
        "sentence": "玄武临财发动，财路偏暗，宜防账目不清、暗耗或隐损。",
        "source": "易冒·理财章第六十六",
        "signal_type": "象法警示",
    },
    {
        "liu_shen": "青龙", "liu_qin": "妻财", "is_moving": True,
        "sentence": "青龙临财发动，财机活络，利于顺势交易、喜庆得财。",
        "source": "易冒·理财章第六十六",
        "signal_type": "象法印证",
    },
    {
        "liu_qin": "官鬼", "is_shi": True, "is_moving": True,
        "sentence": "世爻官鬼发动，女方自身心意已动，婚事推进多由己方牵引。",
        "source": "易冒·婚姻章第五十一",
        "signal_type": "象法印证",
    },
    {
        "liu_shen": "白虎", "liu_qin": "妻财", "is_ying": True,
        "sentence": "应爻妻财逢白虎，婚事中易夹杂硬碰硬或现实伤损，宜慎言慎争。",
        "source": "易冒·婚姻章第五十一",
        "signal_type": "象法警示",
    },
    {
        "liu_shen": "朱雀", "liu_qin": "官鬼", "is_ying": True,
        "sentence": "应爻官鬼逢朱雀，婚事多由话语承诺而起，也易因言语生变。",
        "source": "易冒·婚姻章第五十一",
        "signal_type": "象法警示",
    },
    # 旺衰/动静类（来源：易冒·有无章第十七、动变章第十一、长生章第三十一）
    {
        "liu_qin": "妻财", "wangshuai": "衰", "is_moving": False,
        "sentence": "妻财静而衰，财机未显，当前不宜强求厚利。",
        "source": "易冒·有无章第十七",
        "signal_type": "象法警示",
    },
    {
        "liu_qin": "官鬼", "wangshuai": "衰", "is_moving": False,
        "sentence": "官鬼静而衰，忧患之气不盛，所惧之事未必成真。",
        "source": "易冒·有无章第十七",
        "signal_type": "象法印证",
    },
    {
        "liu_qin": "子孙", "wangshuai": "衰", "is_moving": False,
        "sentence": "子孙静而衰，福力未充，化解之机偏弱，宜待时。",
        "source": "易冒·长生章第三十一",
        "signal_type": "象法警示",
    },
    {
        "liu_qin": "父母", "wangshuai": "衰", "is_moving": False,
        "sentence": "父母静而衰，文书长辈之力暂弱，手续资助难足。",
        "source": "易冒·有无章第十七",
        "signal_type": "象法警示",
    },
    {
        "liu_qin": "兄弟", "wangshuai": "衰", "is_moving": False,
        "sentence": "兄弟静而衰，竞争耗财之力不足，阻隔可望渐轻。",
        "source": "易冒·有无章第十七",
        "signal_type": "象法印证",
    },
    {
        "liu_qin": "妻财", "wangshuai": "旺", "is_moving": False,
        "sentence": "妻财静而旺，财物虽在，宜守成待机，不必躁进。",
        "source": "易冒·有无章第十七",
        "signal_type": "象法印证",
    },
    {
        "liu_qin": "官鬼", "wangshuai": "旺", "is_moving": False,
        "sentence": "官鬼静而旺，压力实存但未发动，宜先防后应。",
        "source": "易冒·有无章第十七",
        "signal_type": "象法警示",
    },
    {
        "liu_qin": "子孙", "wangshuai": "旺", "is_moving": False,
        "sentence": "子孙静而旺，福神潜守，缓中有解，不宜自乱阵脚。",
        "source": "易冒·长生章第三十一",
        "signal_type": "象法印证",
    },
]


def _match_combo_sentences(line: Any, wangshuai: str) -> List[Dict[str, Any]]:
    """匹配单爻的高频组合线索句。"""
    results = []
    for combo in _COMBO_SENTENCES:
        if combo.get("liu_shen") and combo["liu_shen"] != line.liu_shen:
            continue
        if combo.get("liu_qin") and combo["liu_qin"] != line.liu_qin:
            continue
        if "is_moving" in combo and combo["is_moving"] != line.is_moving:
            continue
        if "is_shi" in combo and combo["is_shi"] != getattr(line, "is_shi", False):
            continue
        if "is_ying" in combo and combo["is_ying"] != getattr(line, "is_ying", False):
            continue
        if "is_xun_kong" in combo and combo["is_xun_kong"] != getattr(line, "is_xun_kong", False):
            continue
        if "wangshuai" in combo and combo["wangshuai"] != wangshuai:
            continue
        results.append({
            "sentence": combo["sentence"],
            "source": combo["source"],
            "signal_type": combo.get("signal_type", "象法印证"),
            "basis": [line.liu_shen, line.liu_qin],
        })
    return results


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


def _build_structure_sentences(patterns_results: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """从结构模式中提炼少量高频结构句。"""
    if not patterns_results:
        return []

    results: List[Dict[str, Any]] = []
    chong_he = patterns_results.get("chong_he_gua", {}) or {}
    pattern = chong_he.get("pattern")
    if pattern == "六冲变六合":
        results.append({
            "sentence": "卦见六冲变六合，先散后合，眼前虽乱，后势有收拢转圜之机。",
            "source": "易冒·合冲章第三十四",
            "signal_type": "象法印证",
            "basis": [pattern],
            "position": 0,
        })
    elif pattern == "六合变六冲":
        results.append({
            "sentence": "卦见六合变六冲，先合后散，原有局面后续易生破坏反复。",
            "source": "易冒·合冲章第三十四",
            "signal_type": "象法警示",
            "basis": [pattern],
            "position": 0,
        })
    elif pattern in {"主卦六冲", "静卦六冲", "六冲变六冲"}:
        results.append({
            "sentence": "卦带六冲，事态多变不持久，宜防反复折腾、难以长守。",
            "source": "易冒·合冲章第三十四",
            "signal_type": "象法警示",
            "basis": [pattern],
            "position": 0,
        })
    elif pattern in {"主卦六合", "静卦六合", "六合变六合"}:
        results.append({
            "sentence": "卦带六合，事态缠绵牵连，短期不易速决，但有维系与缓和之象。",
            "source": "易冒·合冲章第三十四",
            "signal_type": "象法印证",
            "basis": [pattern],
            "position": 0,
        })

    fan_yin = patterns_results.get("fan_yin", {}) or {}
    if fan_yin.get("卦象反吟") or fan_yin.get("卦宫反吟") or fan_yin.get("爻动反吟") or fan_yin.get("爻化反吟"):
        results.append({
            "sentence": "卦带反吟，主反复折腾、来回冲击，事情多见反复不宁。",
            "source": "易冒·反伏章第十三",
            "signal_type": "象法警示",
            "basis": ["反吟"],
            "position": 0,
        })

    fu_yin = patterns_results.get("fu_yin", {}) or {}
    if fu_yin.get("爻动伏吟") or fu_yin.get("内卦伏吟") or fu_yin.get("外卦伏吟"):
        results.append({
            "sentence": "卦带伏吟，主气滞迟疑、哀怨停顿，宜防拖延与内耗。",
            "source": "易冒·反伏章第十三",
            "signal_type": "象法警示",
            "basis": ["伏吟"],
            "position": 0,
        })

    ru_mu = patterns_results.get("ru_mu", []) or []
    if any(item.get("is_real") for item in ru_mu):
        results.append({
            "sentence": "用象真入墓库，事有闭藏受困之象，宜待冲开或时机转动。",
            "source": "易冒·墓绝章第十八",
            "signal_type": "象法警示",
            "basis": ["真墓"],
            "position": 0,
        })

    san_ban = patterns_results.get("san_ban", []) or []
    if san_ban:
        results.append({
            "sentence": "卦见绊象，事情多有牵住难行，宜防被人被事绊脚。",
            "source": "易冒·合冲章第三十四",
            "signal_type": "象法警示",
            "basis": ["绊"],
            "position": 0,
        })

    san_hui = patterns_results.get("san_hui", []) or []
    if san_hui:
        results.append({
            "sentence": "卦成三会，气势汇聚一方，事情多见同类聚拢、力量成片。",
            "source": "易冒·局会章第三十七",
            "signal_type": "象法印证",
            "basis": ["三会"],
            "position": 0,
        })

    san_xing = patterns_results.get("san_xing", []) or []
    if san_xing:
        results.append({
            "sentence": "卦见三刑，主羞辱内耗或骨肉相伤，宜防事中生怨。",
            "source": "易冒·刑害章第三十八",
            "signal_type": "象法警示",
            "basis": ["三刑"],
            "position": 0,
        })

    liu_hai = patterns_results.get("liu_hai", []) or []
    if liu_hai:
        results.append({
            "sentence": "卦见六害，主面和心背、暗中受损，往来关系宜多设防。",
            "source": "易冒·刑害章第三十八",
            "signal_type": "象法警示",
            "basis": ["六害"],
            "position": 0,
        })

    return results


def analyze_yimao_imagery(
    hexagram,
    yong_lines: Optional[List[Any]] = None,
    wangshuai_results: Optional[List[Dict]] = None,
    dongbian_results: Optional[Dict] = None,
    patterns_results: Optional[Dict] = None,
    question_type: str = "other",
) -> Dict[str, Any]:
    """生成《易冒》象法摘要, 仅供细节分析与报告展示。"""
    yong_lines = yong_lines or []
    wangshuai_results = wangshuai_results or []
    dongbian_results = dongbian_results or {}
    moving_analyses = dongbian_results.get("moving_analyses", {})

    ben = _gua_parts(hexagram.ben_gua_name)
    palace = getattr(hexagram, "palace_name", "")
    trigram_images = []
    for label, gua in (("上卦", ben.get("upper")), ("下卦", ben.get("lower")), ("宫", palace)):
        if gua and gua in BA_GUA_IMAGE:
            entry = BA_GUA_IMAGE[gua]
            trigram_images.append({
                "label": label,
                "gua": gua,
                "image": entry["image"],
                "source": entry["source"],
            })

    # 当前问事类型关注的六亲
    focus_liu_qin = QUESTION_TYPE_FOCUS.get(question_type)

    line_images = []
    for line in hexagram.lines:
        roles = _line_roles(line, yong_lines)
        if not roles and not line.is_moving:
            continue
        ws = wangshuai_results[line.position - 1] if len(wangshuai_results) >= line.position else {}
        moving = moving_analyses.get(line.position, {})

        liu_qin_entry = LIU_QIN_IMAGE.get(line.liu_qin, {})
        liu_shen_entry = LIU_SHEN_IMAGE.get(line.liu_shen, {})
        wu_xing_entry = WU_XING_IMAGE.get(line.wu_xing, {})
        yao_wei_entry = YAO_WEI_IMAGE.get(line.position, {})

        # 是否与当前问事类型相关
        liu_qin_relevant = focus_liu_qin is None or line.liu_qin in focus_liu_qin

        line_images.append({
            "position": line.position,
            "roles": roles,
            "liu_qin": line.liu_qin,
            "liu_qin_image": liu_qin_entry.get("image", ""),
            "liu_qin_source": liu_qin_entry.get("source", ""),
            "liu_qin_relevant": liu_qin_relevant,
            "liu_shen": line.liu_shen,
            "liu_shen_image": liu_shen_entry.get("image", ""),
            "liu_shen_source": liu_shen_entry.get("source", ""),
            "wu_xing": line.wu_xing,
            "wu_xing_image": wu_xing_entry.get("image", ""),
            "wu_xing_source": wu_xing_entry.get("source", ""),
            "yao_wei_image": yao_wei_entry.get("image", ""),
            "yao_wei_source": yao_wei_entry.get("source", ""),
            "wangshuai": ws.get("overall", ""),
            "moving": {
                "bian_zhi": moving.get("bian_zhi"),
                "qu_wang": moving.get("趋旺", []),
                "qu_shuai": moving.get("趋衰", []),
            } if moving else {},
        })

    # 生成高频组合线索句
    sentences = _build_structure_sentences(patterns_results)
    san_he_ju = dongbian_results.get("san_he_ju", []) or []
    if san_he_ju:
        sentences.append({
            "sentence": "卦成三合，气机归一，事情多见同气相感、成局成势。",
            "source": "易冒·局会章第三十七",
            "signal_type": "象法印证",
            "basis": ["三合"],
            "position": 0,
        })
    seen_sentences: set = {item["sentence"] for item in sentences}
    for item in line_images:
        line_obj = hexagram.lines[item["position"] - 1]
        ws_level = item["wangshuai"]
        for s in _match_combo_sentences(line_obj, ws_level):
            if s["sentence"] not in seen_sentences:
                seen_sentences.add(s["sentence"])
                sentences.append({**s, "position": item["position"], "roles": item["roles"]})

        moving = item.get("moving") or {}
        qu_wang = moving.get("qu_wang") or []
        qu_shuai = moving.get("qu_shuai") or []
        trend_specs = [
            ("回头生", "第{position}爻动化回头生，后势有救，应验多在转机之后。", "易冒·变互章第十一", "象法印证"),
            ("回头克", "第{position}爻动化回头克，后势自伤，宜防先动后败。", "易冒·变互章第十一", "象法警示"),
            ("化进神", "第{position}爻化进神，事情有递增推进之象，后势较前更强。", "易冒·进退章第十六", "象法印证"),
            ("化退神", "第{position}爻化退神，事情有递减退让之象，后势不如前势。", "易冒·进退章第十六", "象法警示"),
            ("化绝", "第{position}爻化绝，后路断气，事情易有中断失续之象。", "易冒·长生章第三十一", "象法警示"),
        ]
        for keyword, template, source, signal_type in trend_specs:
            haystack = qu_wang if keyword in {"回头生", "化进神"} else qu_shuai
            if keyword in haystack:
                sentence = template.format(position=item["position"])
                if sentence not in seen_sentences:
                    seen_sentences.add(sentence)
                    sentences.append({
                        "sentence": sentence,
                        "source": source,
                        "signal_type": signal_type,
                        "basis": [keyword],
                        "position": item["position"],
                        "roles": item["roles"],
                    })

    return {
        "source": "docs/reference/yimao",
        "principle": "用神定吉凶, 象法定细节; 日月定旺衰, 动变定来去; 五行定物类, 六亲定人事, 六神定情状, 爻位/八宫定方所。",
        "question_type": question_type,
        "trigram_images": trigram_images,
        "line_images": line_images,
        "sentences": sentences,
    }
