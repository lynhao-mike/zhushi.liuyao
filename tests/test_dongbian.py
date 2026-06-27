"""
动变模块专项测试 - Dedicated unit tests for liuyao/dongbian.py
"""

import pytest
from liuyao.domain.dongbian import (
    is_hui_tou_sheng,
    is_hui_tou_ke,
    is_hua_jin_shen,
    is_hua_tui_shen,
    is_hua_jue,
    is_hua_po,
    analyze_moving_line,
    detect_an_dong,
    analyze_dongbian,
)
from liuyao.domain.hexagram import Hexagram
from liuyao.domain.wangshuai import analyze_hexagram_wangshuai


class TestIsHuiTouSheng:
    """回头生: 变爻五行生本爻五行"""

    def test_positive_water_generates_wood(self):
        # 亥水生寅木
        assert is_hui_tou_sheng("寅", "亥") is True

    def test_positive_fire_generates_earth(self):
        # 午火生丑土
        assert is_hui_tou_sheng("丑", "午") is True

    def test_negative_wood_does_not_generate_metal(self):
        assert is_hui_tou_sheng("酉", "寅") is False

    def test_same_element_not_sheng(self):
        # 寅木 <- 卯木 (同五行不是生)
        assert is_hui_tou_sheng("寅", "卯") is False


class TestIsHuiTouKe:
    """回头克: 变爻五行克本爻五行"""

    def test_positive_metal_overcomes_wood(self):
        # 申金克寅木
        assert is_hui_tou_ke("寅", "申") is True

    def test_positive_fire_overcomes_metal(self):
        # 午火克酉金
        assert is_hui_tou_ke("酉", "午") is True

    def test_negative(self):
        assert is_hui_tou_ke("寅", "亥") is False


class TestIsHuaJinShen:
    """化进神: 同五行前进"""

    def test_yin_to_mao(self):
        assert is_hua_jin_shen("寅", "卯") is True

    def test_si_to_wu(self):
        assert is_hua_jin_shen("巳", "午") is True

    def test_shen_to_you(self):
        assert is_hua_jin_shen("申", "酉") is True

    def test_hai_to_zi(self):
        assert is_hua_jin_shen("亥", "子") is True

    def test_negative(self):
        assert is_hua_jin_shen("卯", "寅") is False


class TestIsHuaTuiShen:
    """化退神: 同五行后退"""

    def test_mao_to_yin(self):
        assert is_hua_tui_shen("卯", "寅") is True

    def test_wu_to_si(self):
        assert is_hua_tui_shen("午", "巳") is True

    def test_negative(self):
        assert is_hua_tui_shen("寅", "卯") is False


class TestIsHuaJue:
    """化绝: 本爻五行在变爻处于绝地"""

    def test_metal_jue_at_yin(self):
        # 酉金绝在寅
        assert is_hua_jue("酉", "寅") is True

    def test_water_jue_at_si(self):
        # 子水绝在巳
        assert is_hua_jue("子", "巳") is True

    def test_negative(self):
        assert is_hua_jue("寅", "亥") is False


class TestIsHuaPo:
    """化破: 本爻与变爻互冲"""

    def test_zi_wu(self):
        assert is_hua_po("子", "午") is True

    def test_yin_shen(self):
        assert is_hua_po("寅", "申") is True

    def test_negative(self):
        assert is_hua_po("子", "丑") is False


class TestAnalyzeDongbian:
    """完整动变分析"""

    def test_static_hexagram(self):
        h = Hexagram([7, 7, 7, 7, 7, 7], 2024, 3, 15)
        ws = analyze_hexagram_wangshuai(h)
        result = analyze_dongbian(h, ws)
        assert result["moving_analyses"] == {}
        assert result["useful_moving"] == []
        assert result["useless_moving"] == []

    def test_moving_hexagram_has_analyses(self):
        h = Hexagram([9, 7, 7, 7, 7, 7], 2024, 3, 15)
        ws = analyze_hexagram_wangshuai(h)
        result = analyze_dongbian(h, ws)
        assert 1 in result["moving_analyses"]

    def test_useful_useless_classification(self):
        # 9=老阳动, create a hexagram with moving lines
        h = Hexagram([9, 8, 7, 9, 7, 8], 2024, 6, 15)
        ws = analyze_hexagram_wangshuai(h)
        result = analyze_dongbian(h, ws)
        total = len(result["useful_moving"]) + len(result["useless_moving"])
        assert total == len(result["moving_analyses"])
