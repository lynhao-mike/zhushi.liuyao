# -*- coding: utf-8 -*-
"""郭丙李 PDF 候选理论案例测试。

候选理论测试只验证元数据、重建批次来源、候选提示和非污染约束, 不把 PDF 候选理论直接
升级为核心吉凶规则。
"""

import pytest

from tests.fixtures.candidate_gbl_cases import (
    CANDIDATE_GBL_ALLOWED_INTENTS,
    CANDIDATE_GBL_ALLOWED_QUALITY,
    CANDIDATE_GBL_CASES,
    CANDIDATE_GBL_CASES_BY_ID,
)


REQUIRED_CANDIDATE_FIELDS = {
    "case_id",
    "source",
    "source_pdf",
    "source_rebuild_doc",
    "source_rebuild_batch",
    "source_page_range",
    "source_page",
    "source_title",
    "question",
    "question_type",
    "question_intent",
    "candidate_theory_ids",
    "gua_complete_level",
    "feedback_quality",
    "expected_outcome",
    "expected_candidate_pattern",
    "should_affect_core_judgement",
    "validation_status",
    "candidate_hints",
    "notes",
}


@pytest.mark.parametrize("case", CANDIDATE_GBL_CASES, ids=[case["case_id"] for case in CANDIDATE_GBL_CASES])
def test_candidate_gbl_cases_have_quality_metadata(case):
    """郭丙李 PDF 候选案例必须记录质量、来源与问念元数据。"""
    assert REQUIRED_CANDIDATE_FIELDS <= set(case)
    assert case["case_id"].startswith("gbl_pdf_p")
    assert case["source"] == "gbl_pdf_candidate"
    assert case["source_page"] > 0
    assert case["source_pdf"].endswith("郭丙李六爻实战案例汇总_20260421更新.pdf")
    assert "docs/reference/new/郭丙李六爻实战案例汇总_重建批次_" in case["source_rebuild_doc"]
    assert case["source_rebuild_doc"].endswith(f"_页{case['source_page_range']}.md")
    assert case["source_rebuild_batch"] in {"01", "02", "03", "04", "05", "06", "07"}
    start_page, end_page = (int(page) for page in case["source_page_range"].split("-"))
    assert start_page <= case["source_page"] <= end_page
    assert case["question_intent"] in CANDIDATE_GBL_ALLOWED_INTENTS
    assert case["feedback_quality"] in CANDIDATE_GBL_ALLOWED_QUALITY
    assert case["gua_complete_level"] in {"full", "partial", "text_only"}
    assert case["validation_status"] in {"candidate", "fixture_ready", "validated", "rejected"}
    assert case["candidate_theory_ids"]
    assert all(theory_id.startswith("T-GBL-") for theory_id in case["candidate_theory_ids"])
    assert case["expected_outcome"]
    assert case["expected_candidate_pattern"]


@pytest.mark.parametrize("case", CANDIDATE_GBL_CASES, ids=[case["case_id"] for case in CANDIDATE_GBL_CASES])
def test_candidate_theory_hints_do_not_override_core_rules(case):
    """候选理论提示不得覆盖既有核心规则。"""
    assert case["should_affect_core_judgement"] is False
    assert case["validation_status"] == "candidate"
    assert "expected_ji_xiong" not in case
    assert "expected_rule_id" not in case
    assert "expected_pattern" not in case


@pytest.mark.parametrize("case", CANDIDATE_GBL_CASES, ids=[case["case_id"] for case in CANDIDATE_GBL_CASES])
def test_candidate_gbl_cases_emit_non_empty_candidate_hints(case):
    """候选案例应提供可用于报告层展示的候选理论提示。"""
    assert isinstance(case["candidate_hints"], list)
    assert len(case["candidate_hints"]) >= 2
    assert all(isinstance(hint, str) and hint for hint in case["candidate_hints"])


def test_candidate_competitive_cases_emit_competition_context():
    """竞争类候选案例应能识别竞争/名额/间爻阻隔语境。"""
    cases = [case for case in CANDIDATE_GBL_CASES if case["question_intent"] == "competitive"]
    assert cases
    for case in cases:
        assert "T-GBL-002" in case["candidate_theory_ids"]
        assert any(hint in case["candidate_hints"] for hint in {"competitive_context", "quota_race"})
        assert "竞争" in case["expected_candidate_pattern"] or "抢票" in case["expected_candidate_pattern"]


def test_candidate_truth_check_cases_separate_category_from_life_death():
    """疾病真假类候选案例必须把疾病类别判断与生死吉凶区分开。"""
    cases = [case for case in CANDIDATE_GBL_CASES if case["question_intent"] == "truth_check"]
    assert cases
    for case in cases:
        assert "T-GBL-025" in case["candidate_theory_ids"]
        assert "disease_category_not_life_death" in case["candidate_hints"]
        assert case["should_affect_core_judgement"] is False


def test_candidate_location_detail_cases_are_detail_only():
    """寻物/寻宠候选案例当前只作为定位细节样本, 不参与核心吉凶。"""
    cases = [case for case in CANDIDATE_GBL_CASES if case["question_intent"] == "location_detail"]
    assert cases
    for case in cases:
        assert "T-GBL-026" in case["candidate_theory_ids"]
        assert any(hint in case["candidate_hints"] for hint in {"lost_pet_location", "lost_item_location"})
        assert case["should_affect_core_judgement"] is False


def test_candidate_gbl_cases_cover_all_rebuild_batches():
    """所有重建批次都应至少有一个候选案例纳入产出。"""
    expected_batches = {"01", "02", "03", "04", "05", "06", "07"}
    actual_batches = {case["source_rebuild_batch"] for case in CANDIDATE_GBL_CASES}
    assert actual_batches == expected_batches


def test_candidate_gbl_case_id_index_is_complete():
    """候选案例 ID 索引必须覆盖全部候选样本。"""
    assert set(CANDIDATE_GBL_CASES_BY_ID) == {case["case_id"] for case in CANDIDATE_GBL_CASES}
