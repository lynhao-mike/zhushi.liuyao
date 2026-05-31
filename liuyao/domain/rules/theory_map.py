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
        "status": "implemented_p0",
        "notes": "例3 已按原书《大过之鼎》修正 fixture, 世爻父母亥水月破日克; 例22 已进基线",
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
        "status": "implemented_p0",
        "notes": "例5 已按原书《萃之同人》修正 fixture, 亥卯未木局克父母未土用神; 例10/例218 已进基线",
    },
    "内重外轻_自变终局": {
        "rules": ["P0_SELF_CHANGE_TERMINAL"],
        "cases": ["例11", "例15"],
        "status": "implemented_p0",
        "notes": (
            "例15 已按原书《遁之姤》修正 fixture, 世爻官鬼午火自变亥水子孙回头克/化绝; "
            "例11 已进基线"
        ),
    },
    "动兆胜日月_回头生救": {
        "rules": ["P0_DAY_MONTH_KE_MOVING_RESCUE", "P0_HUI_TOU_SHENG_RESCUE"],
        "cases": ["例4"],
        "status": "implemented_p0",
        "notes": "例4 已按原书《复之震》修正 fixture, 兄弟丑土用神虽受卯月卯日同克, 自发动化午火回头生, 动兆胜日月克",
    },

    # ── 规则缺口: 理论已识别, 尚未实现 ──────────────────────────────────────
    "真绊假绊": {
        "rules": ["P0_MOVING_KE_YONG", "P0_JINGANG_MOVING_KE_SHI"],
        "cases": ["例1", "例14", "例23", "例54", "例101"],
        "status": "implemented_p0",
        "notes": (
            "例14 已按原书《履之中孚》修正 fixture, 午火动化未土为化绊, 吉凶层面假绊不废其克申金子孙用神; "
            "例1/例23/例54/例101 已进基线; 假绊/假空等虚象在吉凶层面不废有用动爻, 动爻照常生克"
        ),
    },
    "变爻用神": {
        "rules": ["P0_TRANSFORMED_YONG_MEDIATOR"],
        "cases": ["例2"],
        "status": "implemented_p0",
        "notes": (
            "例2 fixture 已按原书《兑之解》卦图核实: 初爻巳火官鬼动化寅木妻财, "
            "五爻酉金兄弟动化申金, 三爻丑土应、上爻未土世; "
            "规则落地变爻寅木为用神, 通过动爻巳火为媒间接生世爻未土, 已解锁进基线"
        ),
    },
    "假化散_中转站动爻": {
        "rules": ["P0_TRANSFORMED_YONG_MEDIATOR"],
        "cases": ["例41"],
        "status": "implemented_p0",
        "notes": (
            "例41 已按原书核实为卯月壬寅日《革之既济》占寻地: 世爻兄弟亥水动化父母申金回头生; "
            "占寻地取父母为用神, 变爻父母申金虽被寅日冲破为化散, "
            "但在回头生结构中变爻只是能量中转站而非趋势终点, 吉凶层面属于假化散, "
            "由 P0_TRANSFORMED_YONG_MEDIATOR 判为用神生世之吉并解锁进基线"
        ),
    },
    "动空化空_假空": {
        "rules": ["P0_MOVING_KE_YONG"],
        "cases": ["例54"],
        "status": "implemented_p0",
        "notes": (
            "例54 已按原书核实为卯月庚戌日《益之中孚》: 二爻兄弟寅木动化卯木, "
            "动爻寅与变爻卯同落旬空, 但动空化空在吉凶层面皆为假空; "
            "兄弟忌神化进克世用妻财辰土, 由 P0_MOVING_KE_YONG 判为凶并解锁进基线"
        ),
    },

    # ── 待 fixture 修正后可验证 ───────────────────────────────────────────────
    "特殊日月组合_金刚型": {
        "rules": ["P0_JINGANG_MOVING_KE_SHI"],
        "cases": ["例18", "例20"],
        "status": "implemented_p0_partial_regression_unlocked",
        "notes": (
            "例20 已按原书《巽之涣》修正 fixture, 官鬼酉金得未月生与辰日合为金刚型, "
            "虽化午火回头克亦不废, 动克世爻卯木定凶并进基线; 例18 已进基线"
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
