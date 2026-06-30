"""行人占规则最小回归测试。"""

import pytest

from liuyao.application.use_cases.analysis import run_analysis
from liuyao.domain.hexagram import Hexagram


@pytest.mark.parametrize(
    ("question_type", "yao_values", "expected_pattern", "expected_ji_xiong"),
    [
        ("xingren", [6, 7, 7, 7, 6, 8], "行人化进神", "吉"),
    ],
)
def test_traveler_return_rule(question_type, yao_values, expected_pattern, expected_ji_xiong):
    """问行人出行/归期，用神化进/退应按行人方向信号而非旺衰定性。"""
    hexagram = Hexagram.from_ganzhi(
        yao_values,
        month_zhi="子",
        day_zhi="子",
        day_gan="甲",
    )
    report = run_analysis(hexagram, question_type=question_type)
    result = report.jixiong_result

    assert result["rule_id"] == "P1_TRAVELER_RETURN"
    assert result["pattern"] == expected_pattern
    assert result["ji_xiong"] == expected_ji_xiong
