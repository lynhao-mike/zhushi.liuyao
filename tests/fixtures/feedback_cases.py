# -*- coding: utf-8 -*-
"""用户反馈案例 fixture。

这些案例来自实际反馈, 用于把“误断 -> 反馈 -> 修正规则”固化为可回归的
黄金样本。与古籍卦例不同, 本文件显式记录原断偏差、反馈事实与期望规则命中,
防止系统在后续迭代中再次回到单一路径误断。
"""

FEEDBACK_CASE_KAOYAN_FUSHI_001 = {
    "id": "feedback_kaoyan_fushi_001",
    "description": "卯月癸巳日占考研复试能否通过, 山雷颐之山火贲。",
    "source": "user_feedback",
    "month_zhi": "卯",
    "day_gan": "癸",
    "day_zhi": "巳",
    "xun_kong": ["午", "未"],
    # 初爻 -> 上爻: 初少阳、二少阴、三老阴、四少阴、五少阴、上少阳。
    "yao_types": [7, 8, 6, 8, 8, 7],
    "ben_gua": "山雷颐",
    "bian_gua": "山火贲",
    "question_type": "kaoshi",
    "yong_shen": "父母",
    "expected_ji_xiong": "吉",
    "expected_rule_id": "P1_COMPETITIVE_SELECTION_OPPONENT_FAILS",
    "expected_pattern": "竞争者化破",
    "expected_evidence": {
        "opponent_position": 3,
        "opponent_zhi": "辰",
        "transformed_zhi": "亥",
        "shi_position": 4,
        "shi_zhi": "戌",
        "decline_sign": "变爻逢日冲破",
    },
    "original_misread": {
        "ji_xiong": "凶",
        "reason": "按普通考试/父母用神与忌神持世单一路径, 过度放大压力和用神受制。",
    },
    "feedback": "卦主顺利考出。",
    "corrected_method": "考研复试为短期差额选拔, 三爻间爻妻财辰土代表竞争者; 辰动化亥, 亥被巳日冲破, 竞争者自败, 反给世爻脱颖而出的机会。",
    "theory_points": [
        "考研复试属于短期差额选拔, 应引入竞争卦复核路径。",
        "卯月克世体现复试压力与难度, 不可直接等同失败。",
        "主卦颐主交流、咨询、问答, 符合复试准备与面试语境。",
        "变卦贲主展示、包装、呈现, 符合面试展示语境。",
        "三爻为世应之间的间爻, 妻财辰土又与世爻妻财戌土同类相冲, 可代入竞争者。",
        "竞争者发动化父母亥水, 亥水被巳日冲破, 竞争者自败。",
    ],
}

FEEDBACK_CASE_SHEFU_WASP_STING_001 = {
    "id": "feedback_shefu_wasp_sting_001",
    "description": "未月丁酉日射覆辰时经历, 火泽睽之风泽中孚。",
    "source": "user_feedback",
    "month_zhi": "未",
    "day_gan": "丁",
    "day_zhi": "酉",
    "xun_kong": ["辰", "巳"],
    # 初爻 -> 上爻: 初少阳、二少阳、三少阴、四老阳、五老阴、上少阳。
    "yao_types": [7, 7, 8, 9, 6, 7],
    "ben_gua": "火泽睽",
    "bian_gua": "风泽中孚",
    "question_type": "shefu",
    "yong_shen": "子孙",
    "expected_rule_id": "SHEFU_CONCRETE_EVENT_WASP_STING",
    "expected_pattern": "高处设施遇蜂蛰伤得药助",
    "expected_imagery_keywords": [
        "高处设施",
        "管道泄露",
        "隐蔽蜂虫",
        "蜂虫蛰刺小伤",
        "旁人帮助生世",
        "外用药处理",
    ],
    "expected_evidence": {
        "shi_position": 4,
        "helper_position": 5,
        "unexpected_hexagram": "火泽睽",
        "resolved_hexagram": "风泽中孚",
        "moving_positions": [4, 5],
        "hidden_or_leak_spirit": "玄武",
        "sting_line_zhi": "酉",
        "treatment_line_zhi": "巳",
    },
    "original_misread": {
        "focus": "消息/通知/虚惊",
        "reason": "按普通问事抽象为消息沟通, 未按射覆要求还原人物、地点、动作、物件、身体感受。",
    },
    "feedback": "早上刚上班, 单位门卫喊卦主帮忙查看大门高处压缩器管道泄露; 卦主登高后碰到马蜂窝, 被蛰几下; 隔壁办公室女士给卦主抹风油精。",
    "corrected_method": "射覆应优先取具象。睽为事与愿违; 四爻世动为本人登高介入且酉金有尖刺蛰咬象; 五爻玄武动为高处暗处、泄露、设施管线及旁人介入; 五爻动化父母巳火生世, 为求医治疗、外用药帮助。",
    "theory_points": [
        "射覆类占问目标是还原经历/物象, 不是优先判吉凶。",
        "睽卦主乖离、事与愿违, 本为查看管道, 实遇马蜂窝。",
        "四爻世爻发动在高位, 主卦主亲自登高处理。",
        "子孙酉金临日发动, 可类象蜂虫、小动物、尖锐蛰刺及小伤后化解。",
        "五爻兄弟未土临玄武发动, 主门卫/同事帮助、高处隐蔽、水液泄露、管线设施。",
        "五爻化父母巳火生世, 父母为治疗物、药膏、风油精一类外用处理。",
    ],
}

FEEDBACK_CASES = [
    FEEDBACK_CASE_KAOYAN_FUSHI_001,
    FEEDBACK_CASE_SHEFU_WASP_STING_001,
]
