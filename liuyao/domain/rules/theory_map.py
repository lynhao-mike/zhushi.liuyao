"""
理论、规则、案例映射表。

用于追踪教案理论是否已经落地为可执行规则和回归案例。
"""

THEORY_RULE_CASE_MAP = {
    "特殊日月组合_废爻型": {
        "rules": ["P0_FEI_YAO_RIYUE"],
        "cases": ["例3", "例22"],
        "status": "implemented_p0_fixture_mismatch_pending",
    },
    "时效卦_月令时效": {
        "rules": ["P0_YUE_LING_SHIXIAO"],
        "cases": ["例9"],
        "status": "implemented_p0",
    },
    "三合局优先": {
        "rules": ["P0_SAN_HE_JU_PRIORITY"],
        "cases": ["例5", "例10", "例218"],
        "status": "implemented_p0_partial_regression_unlocked",
    },
    "内重外轻": {
        "rules": ["P0_SELF_CHANGE_TERMINAL"],
        "cases": ["例11", "例15", "例54"],
        "status": "implemented_p0_regression_unlocked",
    },
    "动兆胜日月": {
        "rules": ["P0_HUI_TOU_SHENG_RESCUE"],
        "cases": ["例4"],
        "status": "implemented_p0_fixture_mismatch_pending",
    },
    "真绊假绊": {
        "rules": [],
        "cases": ["例1", "例14", "例23", "例101"],
        "status": "pending_rule_detail",
    },
    "变爻用神": {
        "rules": [],
        "cases": ["例2"],
        "status": "pending_rule_detail",
    },
}
