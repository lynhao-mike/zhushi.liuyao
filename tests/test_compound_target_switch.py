# -*- coding: utf-8 -*-
"""复合之动最终目标爻分流测试。"""

from types import SimpleNamespace

from liuyao.domain.dongbian import _determine_compound_final_target


def test_compound_target_switch_shi_yong_unified():
    hexagram = SimpleNamespace(
        shi_line=SimpleNamespace(position=4),
    )
    result = _determine_compound_final_target(
        hexagram,
        primary_yong_position=4,
        question_type="fumu",
    )
    assert result["kind"] == "shi_yong"
    assert result["position"] == 4


def test_compound_target_switch_self_case_defaults_to_shi():
    hexagram = SimpleNamespace(
        shi_line=SimpleNamespace(position=3),
    )
    result = _determine_compound_final_target(
        hexagram,
        primary_yong_position=5,
        question_type="cai",
    )
    assert result["kind"] == "shi"
    assert result["position"] == 3


def test_compound_target_switch_delegate_case_to_yong():
    hexagram = SimpleNamespace(
        shi_line=SimpleNamespace(position=2),
    )
    result = _determine_compound_final_target(
        hexagram,
        primary_yong_position=6,
        question_type="xingren_gui",
    )
    assert result["kind"] == "yong"
    assert result["position"] == 6
