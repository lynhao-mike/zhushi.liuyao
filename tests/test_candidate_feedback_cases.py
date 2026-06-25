# -*- coding: utf-8 -*-
"""用户反馈候选校准案例测试。

候选反馈测试只验证元数据、卦象复现与校准提示, 不把单个反馈直接升级为核心规则。
"""

import pytest

from liuyao.application.use_cases.analysis import run_analysis, run_dual_analysis
from liuyao.domain.hexagram import Hexagram
from liuyao.interfaces.cli.reporting import format_readable_report
from tests.fixtures.candidate_feedback_cases import (
    CANDIDATE_FEEDBACK_ALLOWED_INTENTS,
    CANDIDATE_FEEDBACK_ALLOWED_QUALITY,
    CANDIDATE_FEEDBACK_CASES,
    CANDIDATE_FEEDBACK_CASES_BY_ID,
)


REQUIRED_CANDIDATE_FEEDBACK_FIELDS = {
    "case_id",
    "source",
    "source_report",
    "question",
    "question_type",
    "question_intent",
    "month_zhi",
    "day_gan",
    "day_zhi",
    "xun_kong",
    "yao_types",
    "ben_gua",
    "bian_gua",
    "gua_type",
    "feedback_quality",
    "expected_direction",
    "actual_outcome",
    "original_judgement",
    "calibration_point",
    "expected_candidate_pattern",
    "expected_evidence",
    "should_affect_core_judgement",
    "validation_status",
    "candidate_hints",
    "notes",
}


def _build_hexagram(case: dict) -> Hexagram:
    """以用户反馈案例记录的真实日月干支构建卦象。"""
    return Hexagram.from_ganzhi(
        case["yao_types"],
        month_zhi=case["month_zhi"],
        day_zhi=case["day_zhi"],
        day_gan=case.get("day_gan"),
        xun_kong=case.get("xun_kong"),
    )


@pytest.mark.parametrize("case", CANDIDATE_FEEDBACK_CASES, ids=[case["case_id"] for case in CANDIDATE_FEEDBACK_CASES])
def test_candidate_feedback_cases_have_quality_metadata(case):
    """用户反馈候选案例必须记录质量、来源与校准元数据。"""
    assert REQUIRED_CANDIDATE_FEEDBACK_FIELDS <= set(case)
    assert case["case_id"].startswith("candidate_feedback_")
    assert case["source"] == "user_feedback_candidate"
    assert case["source_report"].startswith("examples/reports/")
    assert case["feedback_quality"] in CANDIDATE_FEEDBACK_ALLOWED_QUALITY
    assert case["question_intent"] in CANDIDATE_FEEDBACK_ALLOWED_INTENTS
    assert case["validation_status"] == "candidate"
    assert case["actual_outcome"]
    assert case["calibration_point"]
    assert len(case["candidate_hints"]) >= 2


@pytest.mark.parametrize("case", CANDIDATE_FEEDBACK_CASES, ids=[case["case_id"] for case in CANDIDATE_FEEDBACK_CASES])
def test_candidate_feedback_cases_do_not_override_core_rules(case):
    """候选反馈样本不得直接污染核心吉凶规则。"""
    assert case["should_affect_core_judgement"] is False
    assert "expected_rule_id" not in case
    assert "expected_pattern" not in case


@pytest.mark.parametrize("case", CANDIDATE_FEEDBACK_CASES, ids=[case["case_id"] for case in CANDIDATE_FEEDBACK_CASES])
def test_candidate_feedback_case_hexagram_structure_is_reproducible(case):
    """候选反馈案例的卦象结构必须可机器复现。"""
    h = _build_hexagram(case)
    expected = case["expected_evidence"]

    assert h.ben_gua_name == case["ben_gua"]
    assert h.bian_gua_name == case["bian_gua"]
    assert h.gan_zhi["month_zhi"] == case["month_zhi"]
    assert h.gan_zhi["day_zhi"] == case["day_zhi"]
    assert h.shi_line is not None
    assert h.ying_line is not None
    assert h.shi_line.position == expected["shi_position"]
    assert h.shi_line.di_zhi == expected["shi_zhi"]
    assert h.ying_line.position == expected["ying_position"]
    assert h.ying_line.di_zhi == expected["ying_zhi"]
    assert h.ying_line.is_xun_kong is expected["ying_is_xun_kong"]

    empty_positions = [line.position for line in h.lines if line.is_xun_kong]
    assert empty_positions == expected["empty_lines"]


@pytest.mark.parametrize("case", CANDIDATE_FEEDBACK_CASES, ids=[case["case_id"] for case in CANDIDATE_FEEDBACK_CASES])
def test_relationship_timing_candidate_keeps_direction_but_marks_delay(case):
    """夫妻和好反馈候选应固化“方向正确、应期延后”的学习点。"""
    if case["question_intent"] != "timing_calibration":
        pytest.skip("仅校验应期校准候选样本")

    h = _build_hexagram(case)
    report = run_analysis(
        h,
        question_type=case["question_type"],
        yong_shen_override="妻财",
    )

    assert report.jixiong_result["ji_xiong"] == case["expected_direction"]
    assert report.ying_line is not None
    assert getattr(report.ying_line, "is_xun_kong") is True
    assert "应爻" in case["calibration_point"]
    assert "旬空" in case["calibration_point"]
    assert "真正恢复" in case["calibration_point"]
    assert "direction_timing_separation" in case["candidate_hints"]


@pytest.mark.parametrize("case", CANDIDATE_FEEDBACK_CASES, ids=[case["case_id"] for case in CANDIDATE_FEEDBACK_CASES])
def test_lost_item_expression_candidate_separates_clue_from_recovery(case):
    """失物反馈候选应固化“线索象不等于找回结论”的表达校准点。"""
    if case["question_intent"] != "expression_calibration":
        pytest.skip("仅校验表达校准候选样本")

    h = _build_hexagram(case)
    expected = case["expected_evidence"]
    moving_positions = [line.position for line in h.lines if line.is_moving]

    assert case["question_type"] == "shiwu"
    assert case["expected_direction"] == "凶"
    assert moving_positions == expected["moving_positions"]
    assert "clue_not_recovery" in case["candidate_hints"]
    assert "dual_perspective_negative" in case["candidate_hints"]
    assert "线索" in case["calibration_point"]
    assert "找回" in case["calibration_point"]
    assert "降低短期机会" in case["calibration_point"]
    assert "线索象" in case["expected_candidate_pattern"]
    assert "可找回" in case["expected_candidate_pattern"]
    assert case["should_affect_core_judgement"] is False
    assert expected["technical_dual_direction"] == case["expected_direction"]


@pytest.mark.parametrize("case", CANDIDATE_FEEDBACK_CASES, ids=[case["case_id"] for case in CANDIDATE_FEEDBACK_CASES])
def test_readable_report_applies_candidate_feedback_calibration(case):
    """可读报告应吸收候选反馈的表达校准点, 但不改变核心吉凶。"""
    h = _build_hexagram(case)

    if case["question_intent"] == "expression_calibration":
        report = run_dual_analysis(h, case["question_type"])
        text = format_readable_report(report, meta={"question": case["question"]})

        ji_set = {p.jixiong_result.get("ji_xiong") for p in report.perspectives}

        assert "反馈校准提示" in text
        assert "线索象" in text
        assert "不应把线索象直接等同于可找回" in text
        assert case["expected_direction"] in ji_set
        assert ji_set != {"吉"}
    elif case["question_intent"] == "timing_calibration":
        report = run_analysis(h, case["question_type"], yong_shen_override="妻财")
        text = format_readable_report(report, meta={"question": case["question"]})

        assert "反馈校准提示" in text
        assert "应爻旬空" in text
        assert "即时缓和与真正恢复" in text
        assert report.jixiong_result["ji_xiong"] == case["expected_direction"]


def test_candidate_feedback_case_id_index_is_complete():
    """候选反馈案例 ID 索引必须覆盖全部候选样本。"""
    assert set(CANDIDATE_FEEDBACK_CASES_BY_ID) == {case["case_id"] for case in CANDIDATE_FEEDBACK_CASES}
