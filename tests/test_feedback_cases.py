"""用户反馈案例回归测试。

目标不是只验证“能跑通”, 而是把一次明确误断沉淀为黄金反馈样本:
- 固化案例结构事实;
- 固化反馈后的吉凶结论;
- 固化应命中的规则 ID / pattern / evidence;
- 防止后续规则迭代重新退回普通考试单路径误断。
"""

import pytest

from liuyao.application.use_cases.analysis import run_analysis
from liuyao.domain.hexagram import Hexagram
from liuyao.domain.rules import P0_RULES
from tests.fixtures.feedback_cases import FEEDBACK_CASES

BASELINE_FEEDBACK_RULE_HITS = {
    "feedback_kaoyan_fushi_001": {
        "rule_id": "P1_COMPETITIVE_SELECTION_OPPONENT_FAILS",
        "pattern": "竞争者化破",
    },
    "feedback_investment_gold_risk_001": {
        "rule_id": "P1_INVESTMENT_WEALTH_TURNS_GHOST_RISK",
        "pattern": "财动化鬼风控",
    },
    "feedback_cup_broken_external_omen_001": {
        "rule_id": "PARENT_BAIHU_WANG_INJURY_AND_FUCAI_XUNKONG_LOSS",
        "pattern": "父母白虎旺相主长辈伤灾，财伏旬空主破财",
    },
}

RULE_FEEDBACK_CASES = [case for case in FEEDBACK_CASES if "expected_ji_xiong" in case]
SHEFU_FEEDBACK_CASES = [case for case in FEEDBACK_CASES if case.get("question_type") == "shefu"]


def _build_hexagram(case: dict) -> Hexagram:
    """以反馈案例记录的真实日月干支构建卦象。"""
    return Hexagram.from_ganzhi(
        case["yao_types"],
        month_zhi=case["month_zhi"],
        day_zhi=case["day_zhi"],
        day_gan=case.get("day_gan"),
        xun_kong=case.get("xun_kong"),
    )


@pytest.mark.parametrize("case", FEEDBACK_CASES, ids=[case["id"] for case in FEEDBACK_CASES])
def test_feedback_case_structure(case):
    """反馈案例构卦结构必须与用户给出的卦象一致。"""
    h = _build_hexagram(case)
    assert h.ben_gua_name == case["ben_gua"]
    assert h.bian_gua_name == case["bian_gua"]
    assert h.gan_zhi["month_zhi"] == case["month_zhi"]
    assert h.gan_zhi["day_zhi"] == case["day_zhi"]

    expected = case["expected_evidence"]
    assert h.shi_line.position == expected["shi_position"]

    if "opponent_position" in expected:
        opponent = h.lines_by_position[expected["opponent_position"]]
        assert opponent.is_moving is True
        assert opponent.di_zhi == expected["opponent_zhi"]
        assert opponent.bian_di_zhi == expected["transformed_zhi"]
        assert h.shi_line.di_zhi == expected["shi_zhi"]

    if "moving_positions" in expected:
        moving_positions = [line.position for line in h.moving_lines]
        assert moving_positions == expected["moving_positions"]
        assert h.ben_gua_name == expected["unexpected_hexagram"]
        assert h.bian_gua_name == expected["resolved_hexagram"]


@pytest.mark.parametrize("case", RULE_FEEDBACK_CASES, ids=[case["id"] for case in RULE_FEEDBACK_CASES])
def test_feedback_case_rule_hit_snapshot(case):
    """反馈案例必须命中反馈修正后的规则快照。"""
    h = _build_hexagram(case)
    report = run_analysis(
        h,
        question_type=case.get("question_type", "other"),
        yong_shen_override=case.get("yong_shen"),
    )
    ji = report.jixiong_result or {}
    expected = BASELINE_FEEDBACK_RULE_HITS[case["id"]]

    assert ji.get("ji_xiong") == case["expected_ji_xiong"]
    assert ji.get("rule_id") == expected["rule_id"]
    assert ji.get("pattern") == expected["pattern"]

    calibration = ji.get("calibration") or {}
    assert calibration["promotion"] == "feedback_to_core"
    assert calibration["rule_id"] == expected["rule_id"]

    evidence = ji.get("evidence") or []
    assert evidence, "反馈规则应输出 evidence, 用于解释角色映射与成败路径"
    first = evidence[0]
    expected_evidence = case["expected_evidence"]

    if case["id"] == "feedback_kaoyan_fushi_001":
        assert first["position"] == expected_evidence["opponent_position"]
        assert first["ben_zhi"] == expected_evidence["opponent_zhi"]
        assert first["bian_zhi"] == expected_evidence["transformed_zhi"]
        assert first["shi_position"] == expected_evidence["shi_position"]
        assert first["shi_zhi"] == expected_evidence["shi_zhi"]
        assert expected_evidence["decline_sign"] in first["decline_reasons"]
        assert first["decision_path"] == "competitive_selection_review"
        assert "counter_signals" in first
    elif case["id"] == "feedback_investment_gold_risk_001":
        assert first["position"] == expected_evidence["moving_position"]
        assert first["ben_zhi"] == expected_evidence["moving_zhi"]
        assert first["bian_zhi"] == expected_evidence["transformed_zhi"]
        assert first["bian_liu_qin"] == expected_evidence["transformed_liu_qin"]
        assert first["shi_position"] == expected_evidence["shi_position"]
        assert first["shi_zhi"] == expected_evidence["shi_zhi"]
        for signal in expected_evidence["risk_signals"]:
            assert signal in first["risk_signals"]
        assert first["decision_path"] == expected_evidence["decision_path"]
        assert "counter_signals" in first
    elif case["id"] == "feedback_cup_broken_external_omen_001":
        assert first["position"] == expected_evidence["parent_baihu_position"]
        assert first["ben_zhi"] == expected_evidence["parent_baihu_zhi"]
        assert first["liu_shen"] == expected_evidence["parent_baihu_liu_shen"]
        assert first["shi_position"] == expected_evidence["shi_position"]
        assert first["shi_zhi"] == expected_evidence["shi_zhi"]
        assert "财爻不现/藏伏" in first["wealth_signals"]
        assert first["decision_path"] == "external_omen_broken_object_review"
        assert "counter_signals" in first


def test_feedback_case_report_contains_dual_path_review():
    """技术报告与可读报告都应暴露常规取用/竞争选拔双路径复核。"""
    from liuyao.interfaces.cli.reporting import format_readable_report, format_report

    case = FEEDBACK_CASES[0]
    h = _build_hexagram(case)
    report = run_analysis(
        h,
        question_type=case.get("question_type", "other"),
        yong_shen_override=case.get("yong_shen"),
    )

    technical = format_report(report)
    readable = format_readable_report(report, meta={"question": case["description"]})
    for text in (technical, readable):
        assert "双路径复核" in text
        assert "竞争选拔路径" in text
        assert "角色映射" in text
        assert "成败证据" in text


    assert "细节取象（《易冒》古法）" in readable
    assert "不覆盖上面的吉凶判断" in readable


@pytest.mark.parametrize("case", SHEFU_FEEDBACK_CASES, ids=[case["id"] for case in SHEFU_FEEDBACK_CASES])
def test_shefu_feedback_case_outputs_concrete_imagery(case):
    """射覆反馈案例应输出具象候选, 而不是只给抽象吉凶。"""
    from liuyao.domain.dongbian import analyze_dongbian
    from liuyao.domain.shefu import analyze_shefu_imagery
    from liuyao.domain.wangshuai import analyze_hexagram_wangshuai

    h = _build_hexagram(case)
    ws = analyze_hexagram_wangshuai(h)
    db = analyze_dongbian(h, ws)
    result = analyze_shefu_imagery(h, db)

    assert result["pattern"] == case["expected_pattern"]
    keywords = {candidate["keyword"] for candidate in result["event_candidates"]}
    for keyword in case["expected_imagery_keywords"]:
        assert keyword in keywords
    assert result["evidence"]["decision_path"] == "shefu_concrete_imagery"
    assert result["evidence"]["moving_positions"] == case["expected_evidence"]["moving_positions"]


@pytest.mark.parametrize("case", FEEDBACK_CASES, ids=[case["id"] for case in FEEDBACK_CASES])
def test_feedback_case_fixture_records_learning_loop(case):
    """反馈 fixture 必须保留误断、反馈、修正断法, 构成可追踪学习闭环。"""
    original_misread = case.get("original_misread", {})
    assert original_misread.get("ji_xiong") or original_misread.get("focus")
    assert case.get("feedback")
    assert case.get("corrected_method")
    assert len(case.get("theory_points", [])) >= 3


def test_promoted_feedback_rules_have_unique_calibration_contracts():
    """晋升为主判的反馈规则必须声明唯一场景仲裁身份, 防止大量反馈互相抢判。"""
    promoted = [rule for rule in P0_RULES if getattr(rule, "promoted_from_feedback", False)]
    contracts = [(rule.calibration_scope, rule.decision_path) for rule in promoted]

    assert promoted, "至少应有反馈晋升规则承接黄金反馈样本"
    assert len(contracts) == len(set(contracts))
    for rule in promoted:
        assert rule.calibration_scope
        assert rule.decision_path
        assert rule.priority < 900 or rule.rule_id == "P1_YUANSHEN_DUFA_BIANFEI"
