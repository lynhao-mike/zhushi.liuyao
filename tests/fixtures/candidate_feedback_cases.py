"""用户反馈候选校准案例 fixture。

这些案例来自用户真实反馈, 但当前只作为候选校准样本:
- 记录反馈对系统的学习价值;
- 验证卦象与反馈事实可追踪;
- 明确不直接污染核心吉凶规则;
- 等同类案例积累后再升级为正式黄金回归样本或规则。
"""

CANDIDATE_FEEDBACK_CASE_RELATIONSHIP_TIMING_001 = {
    "case_id": "candidate_feedback_relationship_timing_001",
    "source": "user_feedback_candidate",
    "source_report": "examples/reports/20260602_测老婆昨天生气今天能否和好_六爻报告.txt",
    "question": "测老婆昨天与卦主生气了, 今天能和好吗?",
    "question_type": "hun_male",
    "question_intent": "timing_calibration",
    "month_zhi": "巳",
    "day_gan": "丁",
    "day_zhi": "未",
    "xun_kong": ["寅", "卯"],
    # 初爻 -> 上爻: 初少阳、二少阴、三少阴、四少阴、五少阳、上少阳。
    "yao_types": [7, 8, 8, 8, 7, 7],
    "ben_gua": "风雷益",
    "bian_gua": "风雷益",
    "gua_type": "静卦",
    "feedback_quality": "objective_medium",
    "expected_direction": "吉",
    "actual_outcome": "到6月5日晚已经和好, 6月6日带妻子去天津购物。",
    "original_judgement": "今天能和好, 但以小和、缓和为主; 明后天可进一步转暖。",
    "calibration_point": "方向正确但应期偏早; 应爻卯木旬空时, 当天可缓, 真正恢复多在出空或数日内。",
    "expected_candidate_pattern": "感情静卦方向吉而应爻旬空, 应将即时缓和与真正恢复分层表达。",
    "expected_evidence": {
        "shi_position": 3,
        "shi_zhi": "辰",
        "ying_position": 6,
        "ying_zhi": "卯",
        "ying_is_xun_kong": True,
        "empty_lines": [2, 6],
    },
    "should_affect_core_judgement": False,
    "validation_status": "candidate",
    "candidate_hints": [
        "relationship_timing",
        "ying_line_xun_kong_delay",
        "direction_timing_separation",
    ],
    "notes": "用于提示报告层与未来应期算法: 感情类静卦若应爻旬空, 不宜把真正和好压缩到当天晚上。",
}


CANDIDATE_FEEDBACK_CASE_LOST_JEWELRY_EXPRESSION_001 = {
    "case_id": "candidate_feedback_lost_jewelry_expression_001",
    "source": "user_feedback_candidate",
    "source_report": "examples/reports/20260525_金首饰丢失能否找回_可读性报告.txt",
    "secondary_source_report": "examples/reports/20260525_金首饰丢失能否找回_技术报告.txt",
    "question": "金首饰丢失, 能否找回?",
    "question_type": "shiwu",
    "question_intent": "expression_calibration",
    "month_zhi": "巳",
    "day_gan": "己",
    "day_zhi": "亥",
    "xun_kong": ["辰", "巳"],
    # 初爻 -> 上爻: 初老阳、二少阴、三少阳、四老阳、五老阴、上老阴。
    "yao_types": [9, 8, 7, 9, 6, 6],
    "ben_gua": "雷火丰",
    "bian_gua": "风山渐",
    "gua_type": "动卦",
    "feedback_quality": "objective_medium",
    "expected_direction": "凶",
    "actual_outcome": "卦主在家里和工作单位寻找, 最终未能找回。",
    "original_judgement": "短期仍有找回机会; 迟则难回。",
    "calibration_point": "技术报告双视角为凶且最终未找回; 可读报告应区分线索象与找回结论, 降低短期机会表达强度。",
    "expected_candidate_pattern": "失物卦有近身或线索象但技术层双视角偏凶时, 可读报告不应把线索象直接等同可找回。",
    "expected_evidence": {
        "shi_position": 5,
        "shi_zhi": "申",
        "ying_position": 2,
        "ying_zhi": "丑",
        "ying_is_xun_kong": False,
        "empty_lines": [],
        "moving_positions": [1, 4, 5, 6],
        "primary_value_line": 4,
        "primary_value_zhi": "午",
        "object_body_line": 5,
        "object_body_zhi": "申",
        "technical_dual_direction": "凶",
    },
    "should_affect_core_judgement": False,
    "validation_status": "candidate",
    "candidate_hints": [
        "lost_item_expression",
        "clue_not_recovery",
        "dual_perspective_negative",
    ],
    "notes": "用于提示报告层: 失物卦中近身、低处、原路线等线索象只能作为查找建议, 不能在技术层双视角偏凶时直接强化为短期可找回结论。",
}


CANDIDATE_FEEDBACK_CASES = [
    CANDIDATE_FEEDBACK_CASE_RELATIONSHIP_TIMING_001,
    CANDIDATE_FEEDBACK_CASE_LOST_JEWELRY_EXPRESSION_001,
]

CANDIDATE_FEEDBACK_CASES_BY_ID = {case["case_id"]: case for case in CANDIDATE_FEEDBACK_CASES}

CANDIDATE_FEEDBACK_ALLOWED_INTENTS = {
    "timing_calibration",
    "expression_calibration",
    "rule_gap_candidate",
}

CANDIDATE_FEEDBACK_ALLOWED_QUALITY = {
    "objective_high",
    "objective_medium",
    "subjective_low",
}
