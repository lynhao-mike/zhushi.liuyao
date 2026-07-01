"""经典象法资料库测试。

这些测试只约束《易冒》象法候选资料的可追溯与报告展示，不把象法直接升级为核心吉凶规则。
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from liuyao.application.use_cases.analysis import run_analysis
from liuyao.domain.classic_imagery import (
    clear_classic_imagery_caches,
    load_classic_imagery,
    search_classic_imagery,
)
from liuyao.domain.hexagram import Hexagram
from liuyao.interfaces.cli.reporting import format_readable_report
from scripts.extract_classic_imagery import build_records, match_section

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "classic_imagery.jsonl"
REQUIRED_FIELDS = {
    "id",
    "source",
    "source_file",
    "line_start",
    "line_end",
    "section",
    "raw_text",
    "imagery_type",
    "keywords",
    "question_types",
    "usage",
    "review_status",
    "notes",
}


def _raw_records() -> list[dict]:
    with DATA_PATH.open("r", encoding="utf-8") as file:
        return [json.loads(line) for line in file if line.strip()]


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


def _classic_imagery_block(text: str) -> str:
    start = text.find("  《易冒》经典象法参考（细节层，不改判）：")
    assert start != -1
    end = text.find("▌ 八、", start)
    assert end != -1
    return text[start:end]


def test_classic_imagery_jsonl_exists_and_has_minimum_volume():
    assert DATA_PATH.exists()
    records = _raw_records()
    assert len(records) >= 1000


def test_classic_imagery_have_required_fields_and_candidate_status():
    for record in _raw_records():
        assert REQUIRED_FIELDS <= set(record)
        assert record["id"].startswith("imagery_yimao_")
        assert record["source"] == "yimao"
        assert record["source_file"].startswith("docs/reference/yimao/")
        assert record["raw_text"]
        assert record["line_start"] >= 1
        assert record["line_end"] >= record["line_start"]
        assert record["review_status"] == "candidate"
        assert record["usage"] == "report_imagery_reference_only"
        assert record["question_types"]
        assert isinstance(record["keywords"], list)


def test_classic_imagery_source_lines_are_traceable():
    for record in _raw_records()[:120]:
        source_path = ROOT / record["source_file"]
        assert source_path.exists()
        source_lines = source_path.read_text(encoding="utf-8").splitlines()
        line_text = source_lines[record["line_start"] - 1]
        assert record["raw_text"] in line_text


def test_extract_classic_imagery_build_records_matches_quality_baseline():
    records = build_records()
    sections = {record["section"] for record in records}

    assert len(records) >= 1000
    assert all(record["source"] == "yimao" for record in records)
    assert all(record["usage"] == "report_imagery_reference_only" for record in records)
    for expected_section in ("五行", "六亲", "六神"):
        assert expected_section in sections


def test_extract_classic_imagery_section_matching():
    assert match_section("五行章第五") == "五行"
    assert match_section("六亲章第六") == "六亲"
    assert match_section("易冒卷之一") == "易冒卷之一"


def test_classic_imagery_cover_key_sections_by_statistics():
    records = _raw_records()
    sections = Counter(record["section"] for record in records)

    assert sections["五行"] >= 10
    assert sections["六亲"] >= 10
    assert sections["六神"] >= 10


def test_load_classic_imagery_returns_typed_records():
    records = load_classic_imagery(DATA_PATH)
    assert records
    first = records[0]
    assert first.id.startswith("imagery_yimao_")
    assert first.source == "yimao"
    assert first.raw_text
    assert first.review_status == "candidate"
    assert first.usage == "report_imagery_reference_only"
    assert isinstance(first.keywords, tuple)


def test_search_classic_imagery_by_liuqin_keywords():
    results = search_classic_imagery(["父母", "官鬼"], limit=5)
    assert results
    assert len(results) <= 5
    assert all(result.source == "yimao" for result in results)
    assert any("父母" in result.raw_text or "官鬼" in result.raw_text for result in results)


def test_search_classic_imagery_can_filter_question_type_and_exclude_candidate_records():
    assert search_classic_imagery(["财"], question_type="cai", limit=5)
    assert search_classic_imagery(["财"], limit=5, include_candidate=False) == []


def test_clear_classic_imagery_caches_keeps_search_available():
    assert search_classic_imagery(["财"], question_type="cai", limit=5)
    clear_classic_imagery_caches()
    results = search_classic_imagery(["财"], question_type="cai", limit=5)
    assert results
    assert len(results) <= 5


def test_readable_report_adds_classic_imagery_without_changing_judgement():
    report, text = _investment_gold_report_text()
    original_jixiong = dict(report.jixiong_result)

    assert report.jixiong_result == original_jixiong
    assert "《易冒》经典象法参考（细节层，不改判）" in text
    assert "《易冒》" in text
    assert "来源：docs/reference/yimao/" in text
    assert "仅作象法参考" in text


def test_readable_report_separates_judgement_and_imagery_sources():
    _, text = _investment_gold_report_text()
    judgement_start = text.find("  《黄金策》经典断语印证（不改判）：")
    imagery_start = text.find("  《易冒》经典象法参考（细节层，不改判）：")
    assert judgement_start != -1
    assert imagery_start != -1
    judgement_block = text[judgement_start:imagery_start]
    imagery_block = _classic_imagery_block(text)

    assert "《黄金策》" in judgement_block
    assert "《易冒》" not in judgement_block
    assert "《易冒》" in imagery_block
    assert "《黄金策》" not in imagery_block
    assert "仅作报告参考" in judgement_block
    assert "仅作象法参考" in imagery_block


def test_readable_report_classic_imagery_count_and_trace_format():
    _, text = _investment_gold_report_text()
    block = _classic_imagery_block(text)
    reference_lines = [line for line in block.splitlines() if line.startswith("  · 《")]
    source_lines = [line.strip() for line in block.splitlines() if line.strip().startswith("来源：")]

    assert len(reference_lines) == 2
    assert len(source_lines) == 2
    assert all(line.startswith("来源：docs/reference/yimao/") for line in source_lines)
    assert all("类型：" in line for line in source_lines)
    assert all(line.endswith("；仅作象法参考。") for line in source_lines)
