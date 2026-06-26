# -*- coding: utf-8 -*-
"""用忌互化规则最小回归测试。"""

import pytest

from liuyao.application.use_cases.analysis import run_analysis
from liuyao.domain.hexagram import Hexagram


@pytest.mark.parametrize(
    ("question_type", "yao_values", "expected_pattern"),
    [
        ("shengchan", [6, 8, 7, 8, 9, 9], "子鬼互化"),
        ("kaoshi", [6, 6, 7, 6, 7, 8], "父子互化"),
        ("cai", [6, 6, 6, 6, 6, 7], "财鬼互化"),
    ],
)
def test_yong_ji_mutual_transform_rule(question_type, yao_values, expected_pattern):
    """子鬼/父子/财鬼互化在明确问事语境中应命中统一 P1 规则。"""
    hexagram = Hexagram.from_ganzhi(
        yao_values,
        month_zhi="子",
        day_zhi="子",
        day_gan="甲",
    )

    report = run_analysis(hexagram, question_type=question_type)
    result = report.jixiong_result

    assert result["rule_id"] == "P1_YONG_JI_MUTUAL_TRANSFORM"
    assert result["pattern"] == expected_pattern
    assert result["ji_xiong"] == "凶"
