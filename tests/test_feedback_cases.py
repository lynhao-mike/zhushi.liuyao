# -*- coding: utf-8 -*-
"""用户反馈案例回归测试。

目标不是只验证“能跑通”, 而是把一次明确误断沉淀为黄金反馈样本:
- 固化案例结构事实;
- 固化反馈后的吉凶结论;
- 固化应命中的规则 ID / pattern / evidence;
- 防止后续规则迭代重新退回普通考试单路径误断。
"""

import pytest

from liuyao.analyzer import run_analysis
from liuyao.hexagram import Hexagram
from tests.fixtures.feedback_cases import FEEDBACK_CASES


BASELINE_FEEDBACK_RULE_HITS = {
    "feedback_kaoyan_fushi_001": {
        "rule_id": "P1_COMPETITIVE_SELECTION_OPPONENT_FAILS",
        "pattern": "竞争者化破",
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

    evidence = ji.get("evidence") or []
    assert evidence, "反馈规则应输出 evidence, 用于解释角色映射与成败路径"
    first = evidence[0]
    expected_evidence = case["expected_evidence"]
    assert first["position"] == expected_evidence["opponent_position"]
    assert first["ben_zhi"] == expected_evidence["opponent_zhi"]
    assert first["bian_zhi"] == expected_evidence["transformed_zhi"]
    assert first["shi_position"] == expected_evidence["shi_position"]
    assert first["shi_zhi"] == expected_evidence["shi_zhi"]
    assert expected_evidence["decline_sign"] in first["decline_reasons"]
    assert first["decision_path"] == "competitive_selection_review"
    assert "counter_signals" in first


def test_feedback_case_report_contains_dual_path_review():
    """技术报告与可读报告都应暴露常规取用/竞争选拔双路径复核。"""
    from liuyao.report import format_readable_report, format_report

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
