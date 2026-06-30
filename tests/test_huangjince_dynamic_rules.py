"""《黄金策》动态候选规则闭环测试。

这些测试验证候选规则可校验、可执行、可附加证据, 且不会覆盖既有 P0/一般吉凶主判。
"""

from types import SimpleNamespace

from liuyao.domain.dongbian import analyze_dongbian
from liuyao.domain.hexagram import Hexagram, YaoLine
from liuyao.domain.jixiong import judge_jixiong
from liuyao.domain.rules.classic_rule_schema import validate_classic_rules
from liuyao.domain.rules.context import RuleContext
from liuyao.domain.rules.dynamic_rules import (
    DEFAULT_HUANGJINCE_RULES_PATH,
    DynamicClassicRule,
    evaluate_condition,
    evaluate_dynamic_classic_rules,
    load_dynamic_classic_rule_records,
)
from liuyao.domain.rules.fact_extractor import extract_classic_rule_facts
from liuyao.domain.wangshuai import analyze_hexagram_wangshuai
from liuyao.interfaces.cli.reporting import format_readable_report, format_report


def _line(
    position,
    di_zhi,
    wu_xing,
    liu_qin,
    *,
    is_shi=False,
    is_ying=False,
    is_moving=False,
    is_empty=False,
):
    return YaoLine(
        position=position,
        yao_type=9 if is_moving else 7,
        yin_yang=1,
        is_moving=is_moving,
        tian_gan="甲",
        di_zhi=di_zhi,
        wu_xing=wu_xing,
        liu_qin=liu_qin,
        liu_shen="青龙",
        is_shi=is_shi,
        is_ying=is_ying,
        is_xun_kong=is_empty,
    )


def _candidate_context():
    shi = _line(1, "子", "水", "妻财", is_shi=True)
    ying = _line(4, "丑", "土", "官鬼", is_ying=True)
    extra_lines = [
        _line(2, "寅", "木", "父母"),
        _line(3, "卯", "木", "父母"),
        _line(5, "巳", "火", "子孙"),
        _line(6, "午", "火", "子孙"),
    ]
    lines = [shi, *extra_lines[:2], ying, *extra_lines[2:]]
    hexagram = SimpleNamespace(
        lines=lines,
        lines_by_position={line.position: line for line in lines},
        lines_by_liu_qin={"妻财": [shi], "官鬼": [ying]},
        shi_line=shi,
        ying_line=ying,
    )
    wangshuai_results = [
        {"overall": "旺", "month_wang": ["临月令"], "month_shuai": [], "day_wang": [], "day_shuai": [], "details": "测试旺相"},
        {"overall": "平", "month_wang": [], "month_shuai": [], "day_wang": [], "day_shuai": [], "details": "测试平相"},
        {"overall": "平", "month_wang": [], "month_shuai": [], "day_wang": [], "day_shuai": [], "details": "测试平相"},
        {"overall": "平", "month_wang": [], "month_shuai": [], "day_wang": ["日令合"], "day_shuai": [], "details": "测试平相"},
        {"overall": "平", "month_wang": [], "month_shuai": [], "day_wang": [], "day_shuai": [], "details": "测试平相"},
        {"overall": "平", "month_wang": [], "month_shuai": [], "day_wang": [], "day_shuai": [], "details": "测试平相"},
    ]
    return RuleContext(
        hexagram=hexagram,
        yong_shen_liu_qin="妻财",
        wangshuai_results=wangshuai_results,
        dongbian_results={"moving_analyses": {}, "useful_moving": [], "interactions": {}},
        question_type="cai",
        shi_line=shi,
        primary_yong=shi,
        yong_lines=[shi],
        month_zhi="子",
        day_zhi="丑",
    )


def _context_from_shi_ying(
    shi,
    ying,
    *,
    question_type="cai",
    primary_yong=None,
    wangshuai_by_position=None,
    moving_analyses=None,
):
    extra_lines = [
        _line(2, "寅", "木", "父母"),
        _line(3, "卯", "木", "父母"),
        _line(5, "巳", "火", "子孙"),
        _line(6, "午", "火", "子孙"),
    ]
    lines = [shi, *extra_lines[:2], ying, *extra_lines[2:]]
    hexagram = SimpleNamespace(
        lines=lines,
        lines_by_position={line.position: line for line in lines},
        lines_by_liu_qin={
            "妻财": [line for line in lines if line.liu_qin == "妻财"],
            "官鬼": [line for line in lines if line.liu_qin == "官鬼"],
            "父母": [line for line in lines if line.liu_qin == "父母"],
            "子孙": [line for line in lines if line.liu_qin == "子孙"],
        },
        shi_line=shi,
        ying_line=ying,
    )
    default_wangshuai = {
        "overall": "平",
        "month_wang": [],
        "month_shuai": [],
        "day_wang": [],
        "day_shuai": [],
        "details": "测试平相",
    }
    wangshuai_by_position = wangshuai_by_position or {}
    wangshuai_results = []
    for line in lines:
        result = dict(default_wangshuai)
        result.update(wangshuai_by_position.get(line.position, {}))
        wangshuai_results.append(result)
    return RuleContext(
        hexagram=hexagram,
        yong_shen_liu_qin=(primary_yong or shi).liu_qin,
        wangshuai_results=wangshuai_results,
        dongbian_results={"moving_analyses": moving_analyses or {}, "useful_moving": [], "interactions": {}},
        question_type=question_type,
        shi_line=shi,
        primary_yong=primary_yong or shi,
        yong_lines=[primary_yong or shi],
        month_zhi="子",
        day_zhi="丑",
    )


def _record(rule_id):
    return next(record for record in load_dynamic_classic_rule_records() if record["id"] == rule_id)


def _candidate_jixiong_result():
    return {
        "pattern": "用旺世兴局",
        "ji_xiong": "吉",
        "explanation": "测试主判保持不变",
        "classic_rule_candidates": [
            {
                "pattern": "经典候选：世应相合",
                "ji_xiong": "吉",
                "explanation": "《黄金策》候选证据仅供参考，不覆盖核心吉凶。",
                "rule_id": "classic_huangjince_dynamic_shi_ying_he",
                "theory_id": "classic:huangjince:总断千金赋",
                "evidence": [
                    {
                        "source": "huangjince",
                        "source_file": "docs/reference/huangjince/黄金策.txt_part1.md",
                        "line_start": 46,
                        "review_status": "candidate",
                    }
                ],
            }
        ],
    }


def _candidate_analysis_report():
    hexagram = Hexagram.from_ganzhi(
        [9, 8, 7, 9, 7, 8],
        month_zhi="午",
        day_zhi="子",
        xun_kong=["辰", "巳"],
    )
    wangshuai_results = analyze_hexagram_wangshuai(hexagram)
    dongbian_results = analyze_dongbian(hexagram, wangshuai_results)
    return SimpleNamespace(
        hexagram=hexagram,
        question_type="cai",
        yong_shen_liu_qin="妻财",
        yong_shen_lines=hexagram.lines_by_liu_qin.get("妻财", []),
        shi_line=hexagram.shi_line,
        ying_line=hexagram.ying_line,
        wangshuai_results=wangshuai_results,
        dongbian_results=dongbian_results,
        patterns_results={},
        star_spirits={},
        jixiong_result=_candidate_jixiong_result(),
        yingqi_results=[],
    )


def test_huangjince_candidate_rules_load_and_validate_from_default_path():
    assert DEFAULT_HUANGJINCE_RULES_PATH.exists()
    records = load_dynamic_classic_rule_records()

    assert len(records) >= 17
    assert validate_classic_rules(records) == []
    assert {record["source"] for record in records} == {"huangjince"}
    assert all(record["safety"]["allow_override"] is False for record in records)
    assert all(record["safety"]["p0_safe"] is True for record in records)


def test_fact_extractor_and_condition_evaluator_support_shi_ying_he():
    context = _candidate_context()
    facts = extract_classic_rule_facts(context)

    assert facts.value_for("line.exists", "shi") is True
    assert facts.value_for("line.wangshuai.overall", "primary_yong") == "旺"
    assert facts.relationship("he", "shi", "ying") is True

    condition = {
        "op": "AND",
        "children": [
            {"fact_type": "line.exists", "subject": "shi", "relation": "is_true"},
            {"fact_type": "relationship.he", "subject": "shi", "object": "ying", "relation": "is_true"},
        ],
    }
    assert evaluate_condition(condition, facts) is True


def test_dynamic_classic_rule_outputs_candidate_result_without_terminal_stop():
    context = _candidate_context()
    records = load_dynamic_classic_rule_records()
    shi_ying_record = next(record for record in records if record["id"] == "classic_huangjince_dynamic_shi_ying_he")

    result = DynamicClassicRule(shi_ying_record).evaluate(context)

    assert result is not None
    assert result.matched is True
    assert result.stop is False
    assert result.rule_id == "classic_huangjince_dynamic_shi_ying_he"
    assert result.pattern == "经典候选：世应相合"
    assert result.ji_xiong == "吉"
    assert any(item.get("source") == "huangjince" for item in result.evidence)


def test_auto_compiled_primary_yong_moving_decline_matches_only_bing_context():
    shi = _line(1, "子", "水", "妻财", is_shi=True, is_moving=True)
    ying = _line(4, "丑", "土", "官鬼", is_ying=True)
    context = _context_from_shi_ying(
        shi,
        ying,
        question_type="bing",
        primary_yong=shi,
        wangshuai_by_position={1: {"overall": "衰", "details": "测试衰弱"}},
        moving_analyses={1: {"趋衰": ["化绝"]}},
    )

    result = DynamicClassicRule(_record("classic_huangjince_dynamic_primary_yong_moving_decline")).evaluate(context)
    non_bing_context = _context_from_shi_ying(
        shi,
        ying,
        question_type="cai",
        primary_yong=shi,
        wangshuai_by_position={1: {"overall": "衰", "details": "测试衰弱"}},
        moving_analyses={1: {"趋衰": ["化绝"]}},
    )

    assert result is not None
    assert result.stop is False
    assert result.rule_id == "classic_huangjince_dynamic_primary_yong_moving_decline"
    assert result.ji_xiong == "凶"
    assert DynamicClassicRule(_record("classic_huangjince_dynamic_primary_yong_moving_decline")).evaluate(non_bing_context) is None



def test_auto_compiled_shi_ying_empty_he_matches_cai_context():
    shi = _line(1, "子", "水", "妻财", is_shi=True, is_empty=True)
    ying = _line(4, "丑", "土", "官鬼", is_ying=True)
    context = _context_from_shi_ying(shi, ying, question_type="cai")

    result = DynamicClassicRule(_record("classic_huangjince_dynamic_shi_ying_empty_he")).evaluate(context)

    assert result is not None
    assert result.stop is False
    assert result.pattern == "经典候选：世应空合虚约"
    assert result.ji_xiong == "平"



def test_auto_compiled_chuxing_ying_ke_shi_and_ying_empty_match_contexts():
    shi = _line(1, "子", "水", "妻财", is_shi=True)
    ying_ke_shi = _line(4, "丑", "土", "官鬼", is_ying=True)
    ke_context = _context_from_shi_ying(shi, ying_ke_shi, question_type="chuxing")
    ying_empty = _line(4, "丑", "土", "官鬼", is_ying=True, is_empty=True)
    empty_context = _context_from_shi_ying(shi, ying_empty, question_type="chuxing")

    ke_result = DynamicClassicRule(_record("classic_huangjince_dynamic_chuxing_ying_ke_shi")).evaluate(ke_context)
    empty_result = DynamicClassicRule(_record("classic_huangjince_dynamic_chuxing_ying_empty")).evaluate(empty_context)

    assert ke_result is not None
    assert ke_result.rule_id == "classic_huangjince_dynamic_chuxing_ying_ke_shi"
    assert ke_result.ji_xiong == "凶"
    assert empty_result is not None
    assert empty_result.rule_id == "classic_huangjince_dynamic_chuxing_ying_empty"
    assert empty_result.stop is False



def test_auto_compiled_hun_shi_ying_relationships_match_only_hun_context():
    shi_ke_ying = _line(1, "未", "土", "妻财", is_shi=True)
    ying = _line(4, "子", "水", "官鬼", is_ying=True)
    context = _context_from_shi_ying(shi_ke_ying, ying, question_type="hun_male")
    non_hun_context = _context_from_shi_ying(shi_ke_ying, ying, question_type="cai")

    result = DynamicClassicRule(_record("classic_huangjince_dynamic_hun_shi_ying_relationships")).evaluate(context)

    assert result is not None
    assert result.rule_id == "classic_huangjince_dynamic_hun_shi_ying_relationships"
    assert result.stop is False
    assert result.ji_xiong == "平"
    assert DynamicClassicRule(_record("classic_huangjince_dynamic_hun_shi_ying_relationships")).evaluate(non_hun_context) is None


def test_auto_compiled_hun_shi_ying_he_and_empty_rules_match_contexts():
    shi = _line(1, "子", "水", "妻财", is_shi=True, is_empty=True)
    ying_he = _line(4, "丑", "土", "官鬼", is_ying=True)
    he_context = _context_from_shi_ying(shi, ying_he, question_type="hun_male")
    ying_empty = _line(4, "丑", "土", "官鬼", is_ying=True, is_empty=True)
    both_empty_context = _context_from_shi_ying(shi, ying_empty, question_type="hun_male")

    he_result = DynamicClassicRule(_record("classic_huangjince_dynamic_hun_shi_ying_he")).evaluate(he_context)
    both_empty_result = DynamicClassicRule(_record("classic_huangjince_dynamic_hun_shi_ying_both_empty")).evaluate(both_empty_context)

    assert he_result is not None
    assert he_result.pattern == "经典候选：婚姻世应相合"
    assert he_result.ji_xiong == "吉"
    assert both_empty_result is not None
    assert both_empty_result.rule_id == "classic_huangjince_dynamic_hun_shi_ying_both_empty"
    assert both_empty_result.ji_xiong == "凶"


def test_auto_compiled_hun_ying_unstable_bing_ghost_and_chuxing_shi_empty_match_contexts():
    shi = _line(1, "子", "水", "妻财", is_shi=True, is_empty=True)
    moving_ying = _line(4, "丑", "土", "官鬼", is_ying=True, is_moving=True)
    hun_context = _context_from_shi_ying(shi, moving_ying, question_type="hun_male")
    ghost_shi = _line(1, "丑", "土", "官鬼", is_shi=True)
    bing_context = _context_from_shi_ying(ghost_shi, moving_ying, question_type="bing")
    chuxing_context = _context_from_shi_ying(shi, moving_ying, question_type="chuxing")

    hun_result = DynamicClassicRule(_record("classic_huangjince_dynamic_hun_ying_moving_or_empty")).evaluate(hun_context)
    bing_result = DynamicClassicRule(_record("classic_huangjince_dynamic_bing_shi_ghost")).evaluate(bing_context)
    chuxing_result = DynamicClassicRule(_record("classic_huangjince_dynamic_chuxing_shi_empty")).evaluate(chuxing_context)

    assert hun_result is not None
    assert hun_result.pattern == "经典候选：婚姻应动应空不宜"
    assert bing_result is not None
    assert bing_result.ji_xiong == "凶"
    assert chuxing_result is not None
    assert chuxing_result.rule_id == "classic_huangjince_dynamic_chuxing_shi_empty"
    assert chuxing_result.ji_xiong == "吉"



def test_auto_compiled_bing_fumu_hun_wang_kaoshi_empty_and_chuxing_both_empty_match_contexts():
    bing_fumu_shi = _line(1, "子", "水", "父母", is_shi=True)
    bing_fumu_ying = _line(4, "丑", "土", "官鬼", is_ying=True)
    bing_fumu_context = _context_from_shi_ying(bing_fumu_shi, bing_fumu_ying, question_type="bing")

    hun_wang_shi = _line(1, "子", "水", "妻财", is_shi=True)
    hun_wang_ying = _line(4, "丑", "土", "官鬼", is_ying=True)
    hun_wang_context = _context_from_shi_ying(
        hun_wang_shi,
        hun_wang_ying,
        question_type="hun_male",
        wangshuai_by_position={1: {"overall": "旺", "details": "测试旺相"}},
    )

    kaoshi_shi = _line(1, "子", "水", "妻财", is_shi=True, is_empty=True)
    kaoshi_ying = _line(4, "丑", "土", "官鬼", is_ying=True)
    kaoshi_context = _context_from_shi_ying(kaoshi_shi, kaoshi_ying, question_type="kaoshi")

    chuxing_both_empty_shi = _line(1, "子", "水", "妻财", is_shi=True, is_empty=True)
    chuxing_both_empty_ying = _line(4, "丑", "土", "官鬼", is_ying=True, is_empty=True)
    chuxing_both_empty_context = _context_from_shi_ying(
        chuxing_both_empty_shi,
        chuxing_both_empty_ying,
        question_type="chuxing",
    )

    bing_fumu_result = DynamicClassicRule(_record("classic_huangjince_dynamic_bing_shi_fumu")).evaluate(bing_fumu_context)
    hun_wang_result = DynamicClassicRule(_record("classic_huangjince_dynamic_hun_shi_wang")).evaluate(hun_wang_context)
    kaoshi_result = DynamicClassicRule(_record("classic_huangjince_dynamic_kaoshi_shi_empty")).evaluate(kaoshi_context)
    chuxing_both_empty_result = DynamicClassicRule(_record("classic_huangjince_dynamic_chuxing_shi_ying_both_empty")).evaluate(chuxing_both_empty_context)

    assert bing_fumu_result is not None
    assert bing_fumu_result.rule_id == "classic_huangjince_dynamic_bing_shi_fumu"
    assert bing_fumu_result.ji_xiong == "凶"
    assert hun_wang_result is not None
    assert hun_wang_result.rule_id == "classic_huangjince_dynamic_hun_shi_wang"
    assert hun_wang_result.ji_xiong == "吉"
    assert kaoshi_result is not None
    assert kaoshi_result.rule_id == "classic_huangjince_dynamic_kaoshi_shi_empty"
    assert kaoshi_result.ji_xiong == "凶"
    assert chuxing_both_empty_result is not None
    assert chuxing_both_empty_result.rule_id == "classic_huangjince_dynamic_chuxing_shi_ying_both_empty"
    assert chuxing_both_empty_result.ji_xiong == "凶"



def test_dynamic_rule_adapter_returns_all_matching_candidates_sorted_by_priority():
    context = _candidate_context()

    results = evaluate_dynamic_classic_rules(context)

    rule_ids = [result.rule_id for result in results]
    assert "classic_huangjince_dynamic_shi_ying_he" in rule_ids
    assert "classic_huangjince_dynamic_yong_healthy" in rule_ids
    assert [result.priority for result in results] == sorted((result.priority for result in results), reverse=True)
    assert all(result.stop is False for result in results)


def test_jixiong_attaches_classic_candidates_without_overriding_core_judgement():
    hexagram = Hexagram.from_ganzhi(
        [9, 8, 7, 9, 7, 8],
        month_zhi="午",
        day_zhi="子",
        xun_kong=["辰", "巳"],
    )
    wangshuai_results = analyze_hexagram_wangshuai(hexagram)
    dongbian_results = analyze_dongbian(hexagram, wangshuai_results)

    result = judge_jixiong(hexagram, "妻财", wangshuai_results, dongbian_results, "cai")
    comparable = {key: result[key] for key in ("pattern", "ji_xiong", "explanation")}
    without_candidates = dict(result)
    without_candidates.pop("classic_rule_candidates", None)

    assert comparable == {key: without_candidates[key] for key in ("pattern", "ji_xiong", "explanation")}
    if "classic_rule_candidates" in result:
        assert result["classic_rule_candidates"]
        candidates = result["classic_rule_candidates"]
        assert isinstance(candidates, list)
        assert all(candidate.get("rule_id", "").startswith("classic_huangjince_dynamic_") for candidate in candidates)


def test_technical_report_displays_classic_candidate_rules_without_changing_judgement():
    report = _candidate_analysis_report()
    original_jixiong = dict(report.jixiong_result)

    text = format_report(report)

    assert report.jixiong_result == original_jixiong
    assert "经典候选规则参考（不改判）" in text
    assert "classic_huangjince_dynamic_shi_ying_he" in text
    assert "来源：docs/reference/huangjince/黄金策.txt_part1.md:46" in text
    assert "卦局: 用旺世兴局" in text
    assert "判断: 【吉】" in text


def test_readable_report_displays_classic_candidate_rules_without_changing_judgement():
    report = _candidate_analysis_report()
    original_jixiong = dict(report.jixiong_result)

    text = format_readable_report(report, meta={"question": "测试《黄金策》候选规则展示"})

    assert report.jixiong_result == original_jixiong
    assert "经典候选规则参考（不改判）" in text
    assert "classic_huangjince_dynamic_shi_ying_he" in text
    assert "仅作候选证据" in text
    assert "卦局：用旺世兴局" in text
    assert "判断：✓ 吉" in text
