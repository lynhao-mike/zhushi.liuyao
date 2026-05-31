"""
理论、规则、案例映射表。

用于追踪教案理论是否已经落地为可执行规则和回归案例。

状态说明:
  implemented_p0            — 规则已实现且案例已解锁进基线
  implemented_p0_fixture_mismatch_pending
                            — 规则已实现但对应案例 fixture 数据与理论描述不符,
                              案例仍在 KNOWN_MISMATCH, 待原书核实后修正 fixture
  implemented_p0_partial_regression_unlocked
                            — 规则已实现, 部分案例已解锁, 部分仍待 fixture 修正
  pending_rule_detail       — 理论已识别, 规则尚未实现
  pending_fixture_fix       — 规则已实现, 但所有对应案例均为 fixture_mismatch,
                              需先修正 fixture 才能验证规则
"""

THEORY_RULE_CASE_MAP = {
    # ── 已实现 P0 规则 ────────────────────────────────────────────────────────
    "特殊日月组合_废爻型": {
        "rules": ["P0_FEI_YAO_RIYUE"],
        "cases": ["例3", "例22"],
        "status": "implemented_p0_fixture_mismatch_pending",
        "notes": "例22 已进基线; 例3 fixture_mismatch(实际世爻非亥水), 待原书核实",
    },
    "时效卦_月令时效": {
        "rules": ["P0_YUE_LING_SHIXIAO"],
        "cases": ["例9"],
        "status": "implemented_p0",
        "notes": "例9 已解锁进基线",
    },
    "三合局优先": {
        "rules": ["P0_SAN_HE_JU_PRIORITY"],
        "cases": ["例5", "例10", "例218"],
        "status": "implemented_p0_partial_regression_unlocked",
        "notes": "例10/例218 已进基线; 例5 fixture_mismatch(实际用神非未土), 待原书核实",
    },
    "内重外轻_自变终局": {
        "rules": ["P0_SELF_CHANGE_TERMINAL"],
        "cases": ["例11", "例15", "例54"],
        "status": "implemented_p0_partial_regression_unlocked",
        "notes": (
            "例11 已进基线; "
            "例15 fixture_mismatch(实际世爻亥水静爻非午火自变), 待原书核实; "
            "例54 规则缺口: 化进神+月破并存时应取化进为真、化破为假(内重外轻细化), "
            "当前规则只看趋衰未考虑趋旺优先"
        ),
    },
    "动兆胜日月_回头生救": {
        "rules": ["P0_HUI_TOU_SHENG_RESCUE"],
        "cases": ["例4"],
        "status": "implemented_p0_fixture_mismatch_pending",
        "notes": "例4 fixture_mismatch(实际动爻辰土化亥水非丑土化午火), 待原书核实",
    },

    # ── 规则缺口: 理论已识别, 尚未实现 ──────────────────────────────────────
    "真绊假绊": {
        "rules": [],
        "cases": ["例1", "例14", "例23", "例101"],
        "status": "pending_rule_detail",
        "notes": (
            "例23/例101 已进基线(引擎恰好判对); "
            "例1 fixture_mismatch(yao_types顺序错误), 待原书核实; "
            "例14 fixture_mismatch(实际动爻辰土化丑土非午火化未土), 待原书核实"
        ),
    },
    "变爻用神": {
        "rules": [],
        "cases": ["例2"],
        "status": "pending_rule_detail",
        "notes": (
            "例2 fixture_mismatch(yao_types与描述不符, 实际初爻子水非巳火), "
            "待原书核实; 理论: 动爻化出变爻为用神, 变爻生世为吉"
        ),
    },
    "假化散_中转站动爻": {
        "rules": [],
        "cases": ["例41"],
        "status": "pending_rule_detail",
        "notes": (
            "例41 fixture yao_types 为 FIXME 待原书核实; "
            "理论: 动爻化出回头克但变爻非能量终点(中转站), 则回头克无效, 动爻仍有用"
        ),
    },
    "内重外轻_化进优先月破": {
        "rules": [],
        "cases": ["例54"],
        "status": "pending_rule_detail",
        "notes": (
            "例54 fixture yao_types 为 FIXME 待原书核实; "
            "理论: 动爻化进神同时变爻遭月破, 化进为真、化破为假; "
            "需在 SelfChangeTerminalRule 或新规则中: "
            "当趋旺含化进神且趋衰仅含化退神/月破时, 取化进为主不判凶"
        ),
    },

    # ── 待 fixture 修正后可验证 ───────────────────────────────────────────────
    "特殊日月组合_金刚型": {
        "rules": [],
        "cases": ["例18", "例20"],
        "status": "pending_fixture_fix",
        "notes": (
            "例18 已进基线(引擎恰好判对); "
            "例20 fixture_mismatch(yao_types构出的卦无官鬼爻), 待原书核实巽宫纳甲"
        ),
    },
    "特殊日月组合_月冲日冲非衰败": {
        "rules": [],
        "cases": ["例205"],
        "status": "pending_fixture_fix",
        "notes": (
            "例205 fixture_mismatch(yao_types构出的卦无妻财爻), 待原书核实卦图; "
            "理论: 月破+日冲不属于衰败式特殊日月组合, 用神逢动生仍受益"
        ),
    },
    "元神独发变废定凶": {
        "rules": [],
        "cases": ["例108"],
        "status": "pending_fixture_fix",
        "notes": (
            "例108 fixture_error(亥日不可能以亥为旬空), 当前无法构卦; "
            "理论: 元神独发却动化回头克/化绝等变废, 养命之源断绝则凶"
        ),
    },
}
