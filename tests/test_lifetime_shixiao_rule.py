"""终身时效卦规则最小回归测试。"""

import pytest

from liuyao.application.use_cases.analysis import run_analysis
from liuyao.domain.hexagram import Hexagram


@pytest.mark.parametrize(
    ("question_type", "yao_values", "expected_pattern", "expected_ji_xiong"),
    [
        ("zhongshen_gongming", [6, 6, 6, 8, 7, 6], "终身时效卦(官鬼持世)", "吉"),
        ("zhongshen_gongming", [6, 6, 6, 6, 8, 8], "终身时效卦(子孙持世)", "凶"),
        ("zhongshen_caifu", [6, 6, 6, 7, 7, 7], "终身时效卦(妻财持世)", "吉"),
        ("zhongshen_caifu", [6, 6, 6, 7, 6, 7], "终身时效卦(兄弟持世)", "凶"),
    ],
)
def test_lifetime_shixiao_rule(question_type, yao_values, expected_pattern, expected_ji_xiong):
    """明确终身问事中，持世六亲应主导吉凶。"""
    hexagram = Hexagram.from_ganzhi(
        yao_values,
        month_zhi="子",
        day_zhi="子",
        day_gan="甲",
    )

    report = run_analysis(hexagram, question_type=question_type)
    result = report.jixiong_result

    assert result["rule_id"] == "P1_LIFETIME_SHIXIAO"
    assert result["pattern"] == expected_pattern
    assert result["ji_xiong"] == expected_ji_xiong
