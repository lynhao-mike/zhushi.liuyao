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

FEEDBACK_CASES = [
    FEEDBACK_CASE_KAOYAN_FUSHI_001,
]
