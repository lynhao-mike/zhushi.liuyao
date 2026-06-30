"""复合之动最终目标爻规则最小回归测试。"""

from types import SimpleNamespace

from liuyao.application.use_cases.analysis import run_analysis
from liuyao.domain.dongbian import analyze_compound_movement
from liuyao.domain.hexagram import Hexagram
from liuyao.domain.rules.context import RuleContext
from liuyao.domain.rules.p0_rules import CompoundMovementFinalTargetRule
from tests.fixtures.zengshan_230_cases import CASE_10


class _FakeLine(SimpleNamespace):
    pass


def _ctx(compound_movement, shi_position=2):
    hexagram = SimpleNamespace(
        shi_line=SimpleNamespace(position=shi_position, di_zhi="丑", wu_xing="土"),
        moving_lines=[],
    )
    return RuleContext(
        hexagram=hexagram,
        yong_shen_liu_qin="妻财",
        wangshuai_results=[],
        dongbian_results={"compound_movement": compound_movement},
        question_type="cai",
        patterns_results={},
        shi_line=hexagram.shi_line,
        primary_yong=SimpleNamespace(position=4, di_zhi="辰", wu_xing="土", liu_qin="妻财"),
        yong_lines=[],
        month_zhi="卯",
        day_zhi="子",
    )


def test_compound_movement_output_marks_invalid_when_chain_misses_target():
    hexagram = SimpleNamespace(
        shi_line=SimpleNamespace(position=3, di_zhi="丑", wu_xing="土"),
        moving_lines=[
            _FakeLine(position=1, di_zhi="寅", wu_xing="木"),
            _FakeLine(position=2, di_zhi="巳", wu_xing="火"),
        ],
    )
    result = analyze_compound_movement(hexagram, {}, [1, 2], san_he_ju=None)
    assert result
    assert result[0]["mode"] == "chain_sheng"
    assert result[0]["valid"] is False
    assert result[0]["acts_on_target"] == "none"


def test_compound_rule_hits_sheng_shi():
    ctx = _ctx([
        {
            "mode": "chain_sheng",
            "final_target_kind": "shi",
            "final_target_position": 2,
            "path": [1, 2],
            "aggregated_to_position": 2,
            "acts_on_target": "sheng",
            "valid": True,
            "reason": "测试",
            "source_positions": [1, 2],
        }
    ])
    result = CompoundMovementFinalTargetRule().evaluate(ctx)
    assert result is not None
    assert result.rule_id == "P0_COMPOUND_MOVEMENT_FINAL_TARGET"
    assert result.pattern == "复合动生世"
    assert result.ji_xiong == "吉"


def test_compound_rule_hits_block_yong():
    ctx = _ctx([
        {
            "mode": "chain_ke_cancel",
            "final_target_kind": "yong",
            "final_target_position": 4,
            "path": [5, 4],
            "aggregated_to_position": 4,
            "acts_on_target": "block",
            "valid": True,
            "reason": "测试",
            "source_positions": [5, 4],
        }
    ])
    result = CompoundMovementFinalTargetRule().evaluate(ctx)
    assert result is not None
    assert result.rule_id == "P0_COMPOUND_MOVEMENT_FINAL_TARGET"
    assert result.pattern == "复合动阻断用神"
    assert result.ji_xiong == "凶"


def test_compound_rule_yields_to_san_he_mode():
    ctx = _ctx([
        {
            "mode": "san_he",
            "final_target_kind": "shi",
            "final_target_position": 2,
            "path": [],
            "aggregated_to_position": None,
            "acts_on_target": "none",
            "valid": True,
            "reason": "三合局优先于单爻连动",
            "source_positions": [],
            "ju": {"wu_xing": "木", "members": ["亥", "卯", "未"]},
        }
    ])
    result = CompoundMovementFinalTargetRule().evaluate(ctx)
    assert result is None


def test_case_10_still_yields_san_he_priority_rule_on_real_fixture():
    hexagram = Hexagram.from_ganzhi(
        CASE_10["yao_types"],
        month_zhi=CASE_10["month_zhi"],
        day_zhi=CASE_10["day_zhi"],
        xun_kong=CASE_10["xun_kong"],
    )
    report = run_analysis(hexagram, question_type=CASE_10["question_type"], yong_shen_override=CASE_10["yong_shen"])
    result = report.jixiong_result
    assert result["rule_id"] == "P0_SAN_HE_JU_PRIORITY"
    assert result["pattern"] == "三合局生世"
