"""经典断语资料库测试。

这些测试只约束数据可追溯与检索可用性，不把古籍断语直接升级为核心吉凶规则。
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from liuyao.application.use_cases.analysis import run_analysis
from liuyao.domain.classic_judgements import (
    clear_classic_judgements_caches,
    load_classic_judgements,
    search_classic_judgements,
)
from liuyao.domain.hexagram import Hexagram
from liuyao.interfaces.cli.reporting import format_readable_report
from scripts.extract_classic_judgements import build_records, match_section

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "classic_judgements.jsonl"
REQUIRED_FIELDS = {
    "id",
    "source",
    "source_file",
    "line_start",
    "line_end",
    "section",
    "raw_text",
    "explanation",
    "keywords",
    "conditions_text",
    "result_text",
    "polarity",
    "question_types",
    "review_status",
    "notes",
}


def _raw_records() -> list[dict]:
    with DATA_PATH.open("r", encoding="utf-8") as file:
        return [json.loads(line) for line in file if line.strip()]


def test_classic_judgements_jsonl_exists_and_has_minimum_volume():
    assert DATA_PATH.exists()
    records = _raw_records()
    assert len(records) >= 200


def test_classic_judgements_have_required_fields_and_candidate_status():
    for record in _raw_records():
        assert REQUIRED_FIELDS <= set(record)
        assert record["id"].startswith("classic_huangjince_")
        assert record["source"] == "huangjince"
        assert record["raw_text"]
        assert record["line_start"] >= 1
        assert record["line_end"] >= record["line_start"]
        assert record["review_status"] == "candidate"
        assert record["polarity"] in {"吉", "凶", "中性", "待审"}
        assert record["question_types"]
        assert isinstance(record["keywords"], list)


def test_classic_judgements_source_lines_are_traceable():
    for record in _raw_records()[:120]:
        source_path = ROOT / record["source_file"]
        assert source_path.exists()
        source_lines = source_path.read_text(encoding="utf-8").splitlines()
        line_text = source_lines[record["line_start"] - 1]
        assert record["raw_text"] in line_text


def test_classic_judgements_skip_preface_lines():
    records = _raw_records()
    first_huangjince = next(record for record in records if record["source"] == "huangjince")
    assert first_huangjince["line_start"] > 6
    assert "题明" not in first_huangjince["raw_text"]
    assert first_huangjince["section"] == "总断千金赋"


def test_classic_judgements_are_deduplicated_by_raw_text():
    records = _raw_records()
    raw_texts = [record["raw_text"] for record in records]
    assert len(raw_texts) == len(set(raw_texts))


def test_extract_script_shortens_long_numbered_section_titles():
    assert match_section("19、求财居货曰贾，行货曰商。总为资生之计") == "求财"
    assert match_section("3、年时（存赋不注）阴暗晴暑，天道之常") == "年时"
    assert match_section("12、种作农为国本，食乃民天。五谷不同") == "种作"


def test_extract_script_build_records_matches_quality_baseline():
    records = build_records()
    sections = {record["section"] for record in records}

    assert len(records) >= 200
    assert all(not record["raw_text"].startswith("（") for record in records)
    for expected_section in ("求财", "婚姻", "失脱附盗贼、捕贼民苦饥寒", "医药病不求医", "出行"):
        assert expected_section in sections


def test_classic_judgements_cover_key_sections_by_statistics():
    records = _raw_records()
    sections = Counter(record["section"] for record in records)

    assert sections["求财"] >= 8
    assert sections["婚姻"] >= 8
    assert sections["医药病不求医"] >= 5
    assert sections["出行"] >= 5


def test_load_classic_judgements_returns_typed_records():
    records = load_classic_judgements(DATA_PATH)
    assert records
    first = records[0]
    assert first.id.startswith("classic_")
    assert first.raw_text
    assert first.review_status == "candidate"
    assert isinstance(first.keywords, tuple)


def test_search_classic_judgements_by_world_response_keywords():
    results = search_classic_judgements(["世", "应"], limit=3)
    assert results
    assert len(results) <= 3
    assert any("世" in result.raw_text and "应" in result.raw_text for result in results)


def test_search_classic_judgements_can_filter_question_type():
    results = search_classic_judgements(["妻", "财"], question_type="hun_male", limit=5)
    assert results
    assert all("other" in result.question_types or "hun_male" in result.question_types for result in results)


def test_search_classic_judgements_filters_multiple_question_types():
    cases = [
        ("cai", ["财", "利"]),
        ("shiwu", ["失", "物"]),
        ("bing", ["病", "鬼"]),
        ("kaoshi", ["父母", "文书"]),
        ("chuxing", ["行", "归"]),
    ]

    for question_type, keywords in cases:
        results = search_classic_judgements(keywords, question_type=question_type, limit=8)

        assert results
        assert all(
            "other" in result.question_types or question_type in result.question_types
            for result in results
        )


def test_search_classic_judgements_can_exclude_candidate_records():
    assert search_classic_judgements(["世", "应"], limit=5, include_candidate=True)
    assert search_classic_judgements(["世", "应"], limit=5, include_candidate=False) == []


def test_clear_classic_judgements_caches_keeps_search_available():
    assert search_classic_judgements(["世", "应"], limit=3)
    clear_classic_judgements_caches()
    results = search_classic_judgements(["世", "应"], limit=3)
    assert results
    assert len(results) <= 3


def _investment_gold_report_text():
    h = Hexagram.from_ganzhi(
        [7, 8, 8, 6, 8, 7],
        month_zhi="巳",
        day_zhi="巳",
        day_gan="乙",
        xun_kong=["寅", "卯"],
    )
    report = run_analysis(h, question_type="cai", yong_shen_override="妻财")
    text = format_readable_report(report, meta={"question": "问是否能投资黄金交易获利"})
    return report, text


def _classic_reference_block(text: str) -> str:
    start = text.find("  《黄金策》经典断语印证（不改判）：")
    assert start != -1
    imagery_start = text.find("  《易冒》经典象法参考（细节层，不改判）：", start)
    end = imagery_start if imagery_start != -1 else text.find("▌ 八、", start)
    assert end != -1
    return text[start:end]


def test_readable_report_adds_classic_reference_without_changing_judgement():
    report = run_analysis(
        Hexagram.from_ganzhi(
            [7, 8, 8, 6, 8, 7],
            month_zhi="巳",
            day_zhi="巳",
            day_gan="乙",
            xun_kong=["寅", "卯"],
        ),
        question_type="cai",
        yong_shen_override="妻财",
    )
    original_jixiong = dict(report.jixiong_result)
    text = format_readable_report(report, meta={"question": "问是否能投资黄金交易获利"})

    assert report.jixiong_result == original_jixiong
    assert "《黄金策》经典断语印证（不改判）" in text
    assert "来源：docs/reference/" in text
    assert "状态：candidate" in text
    assert "仅作报告参考" in text


def test_classic_judgements_do_not_extract_parenthetical_comments_as_raw_text():
    records = _raw_records()
    assert all(not record["raw_text"].startswith("（") for record in records)


def test_readable_report_filters_classic_reference_to_relevant_sections():
    _, text = _investment_gold_report_text()
    block = _classic_reference_block(text)

    assert "《黄金策》·求财" in block
    for irrelevant_section in ("天时", "年时", "种作", "蚕桑", "丁产", "甲子"):
        assert irrelevant_section not in block


def test_readable_report_filters_common_question_type_sections():
    h = Hexagram.from_ganzhi(
        [7, 8, 8, 6, 8, 7],
        month_zhi="巳",
        day_zhi="巳",
        day_gan="乙",
        xun_kong=["寅", "卯"],
    )
    cases = [
        ("hun_male", "测老婆昨天生气今天能否和好", "婚姻"),
        ("shiwu", "金首饰丢失能否找回", "失脱"),
        ("bing", "问病情能否好转", "医药"),
        ("chuxing", "问出行是否顺利", "出行"),
        ("kaoshi", "问考试能否通过", "求"),
    ]

    for question_type, question, expected_section in cases:
        report = run_analysis(h, question_type=question_type)
        text = format_readable_report(report, meta={"question": question})
        block = _classic_reference_block(text)

        assert expected_section in block
        for irrelevant_section in ("天时", "年时", "丁产", "甲子"):
            assert irrelevant_section not in block


def test_readable_report_shortens_classic_reference_text():
    _, text = _investment_gold_report_text()
    block = _classic_reference_block(text)
    reference_lines = [line for line in block.splitlines() if line.startswith("  · 《")]

    assert reference_lines
    assert all(len(line) <= 140 for line in reference_lines)


def test_readable_report_classic_reference_count_and_trace_format():
    _, text = _investment_gold_report_text()
    block = _classic_reference_block(text)
    reference_lines = [line for line in block.splitlines() if line.startswith("  · 《")]
    source_lines = [line.strip() for line in block.splitlines() if line.strip().startswith("来源：")]

    assert len(reference_lines) == 3
    assert len(source_lines) == 3
    assert all(line.startswith("来源：docs/reference/") for line in source_lines)
    assert all(".md:" in line for line in source_lines)
    assert all(line.endswith("；状态：candidate；仅作报告参考。") for line in source_lines)


def test_readable_report_advice_matches_question_type():
    _, text = _investment_gold_report_text()

    assert "求财风险偏高" in text
    assert "寻回可能性极低" not in text
    assert "不宜轻信" not in text


def test_readable_report_classic_reference_alias_question_types():
    h = Hexagram.from_ganzhi(
        [7, 8, 8, 6, 8, 7],
        month_zhi="巳",
        day_zhi="巳",
        day_gan="乙",
        xun_kong=["寅", "卯"],
    )
    cases = [
        ("shengyi", "问生意经营能否获利", "求财"),
        ("hun_female", "女问婚姻关系能否缓和", "婚姻"),
    ]

    for question_type, question, expected_section in cases:
        report = run_analysis(h, question_type=question_type)
        text = format_readable_report(report, meta={"question": question})
        block = _classic_reference_block(text)

        assert expected_section in block
        assert "仅作报告参考" in block
        for irrelevant_section in ("天时", "年时", "丁产", "甲子"):
            assert irrelevant_section not in block


def test_readable_report_classic_reference_unknown_question_type_is_still_traceable():
    h = Hexagram.from_ganzhi(
        [7, 8, 8, 6, 8, 7],
        month_zhi="巳",
        day_zhi="巳",
        day_gan="乙",
        xun_kong=["寅", "卯"],
    )
    report = run_analysis(h, question_type="other")
    text = format_readable_report(report, meta={"question": "综合占问"})
    block = _classic_reference_block(text)

    assert "来源：docs/reference/" in block
    assert "状态：candidate" in block
    assert "仅作报告参考" in block
