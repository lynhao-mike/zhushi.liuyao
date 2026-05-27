"""
动变模块专项测试 - Dedicated unit tests for liuyao/dongbian.py
"""

import pytest
from liuyao.dongbian import (
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
from liuyao.hexagram import Hexagram
from liuyao.wangshuai import analyze_hexagram_wangshuai


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
    """化破: 变爻被月令或日令冲 (化月破/化日破)
    
    注: 动爻与变爻相冲是反吟(fan yin), 不是化破.
    化破 = 变爻地支 与 月支相冲 或 日支相冲.
    """

    def test_hua_yue_po(self):
        # 变爻午火被月支子水冲(子月午火变爻 = 化月破)
        assert is_hua_po("寅", "午", "子", "亥") is True  # 变爻午被月子冲

    def test_hua_ri_po(self):
        # 变爻午火被日支子水冲(子日午火变爻 = 化日破)
        assert is_hua_po("寅", "午", "卯", "子") is True  # 变爻午被日子冲

    def test_not_hua_po_when_bian_not_broken(self):
        # 变爻丑土不被月日冲 = 不化破
        assert is_hua_po("子", "丑", "巳", "午") is False

    def test_fan_yin_is_not_hua_po(self):
        # 动爻子与变爻午相冲 = 化反吟, 但如果月日不冲午 则不是化破
        assert is_hua_po("子", "午", "卯", "亥") is False  # 月卯日亥均不冲午


class TestIsFanYin:
    """化反吟: 动爻与变爻地支相冲"""

    def test_zi_wu_fan_yin(self):
        from liuyao.dongbian import is_fan_yin
        assert is_fan_yin("子", "午") is True

    def test_yin_shen_fan_yin(self):
        from liuyao.dongbian import is_fan_yin
        assert is_fan_yin("寅", "申") is True

    def test_negative(self):
        from liuyao.dongbian import is_fan_yin
        assert is_fan_yin("子", "丑") is False


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



class TestHuaPoVsFanYin:
    """
    关键理论修复测试: 化破 ≠ 化反吟

    化破 = 变爻被月令或日令冲破 (化月破/化日破)
    化反吟 = 动爻与变爻地支相冲 (动变相冲)
    """

    def test_fan_yin_is_not_hua_po(self):
        """动变相冲(反吟)但变爻未被月日冲 → 不是化破"""
        from liuyao.dongbian import is_fan_yin
        # 寅申相冲 = 化反吟
        assert is_fan_yin("寅", "申") is True
        # 变爻申未被月(卯)日(午)冲 → 不化破
        assert is_hua_po("寅", "申", "卯", "午") is False

    def test_hua_yue_po_correct(self):
        """变爻被月令冲 = 化月破"""
        # 卯月, 月支卯冲酉. 变爻酉 = 化月破
        assert is_hua_po("寅", "酉", "卯", "午") is True

    def test_hua_ri_po_correct(self):
        """变爻被日令冲 = 化日破"""
        # 卯日, 日支卯冲酉. 变爻酉 = 化日破
        assert is_hua_po("寅", "酉", "巳", "卯") is True

    def test_dynamic_line_classification(self):
        """化反吟的动爻在没有其他趋衰因素时不应被标记为无用动爻"""
        # 构建一个有动爻的卦 (2024-03-15 = 卯月)
        h = Hexagram([9, 7, 7, 7, 7, 7], 2024, 3, 15)
        ws = analyze_hexagram_wangshuai(h)
        result = analyze_dongbian(h, ws)
        # 查看第1爻的动变分析 - 应该有"化反吟"标记但不一定是无用
        if 1 in result["moving_analyses"]:
            ma = result["moving_analyses"][1]
            # 化反吟本身不是无用动爻的充分条件
            if "化反吟" in ma.get("趋衰", []):
                # 只有回头克才让动爻无用
                assert "回头克" in ma.get("趋衰", []) == ma["is_useless"]


class TestJinShenTuiShen:
    """
    进退神方向正确性测试

    据《古筮真诠》知识点总结:
    进神: 亥→子, 寅→卯, 巳→午, 申→酉, 丑→辰, 辰→未, 未→戌
    退神: 子→亥, 卯→寅, 午→巳, 酉→申, 辰→丑, 未→辰, 戌→未
    """

    def test_shui_jin(self):
        assert is_hua_jin_shen("亥", "子") is True
        assert is_hua_tui_shen("子", "亥") is True

    def test_mu_jin(self):
        assert is_hua_jin_shen("寅", "卯") is True
        assert is_hua_tui_shen("卯", "寅") is True

    def test_huo_jin(self):
        assert is_hua_jin_shen("巳", "午") is True
        assert is_hua_tui_shen("午", "巳") is True

    def test_jin_jin(self):
        assert is_hua_jin_shen("申", "酉") is True
        assert is_hua_tui_shen("酉", "申") is True

    def test_tu_jin_1(self):
        assert is_hua_jin_shen("丑", "辰") is True
        assert is_hua_tui_shen("辰", "丑") is True

    def test_tu_jin_2(self):
        assert is_hua_jin_shen("辰", "未") is True
        assert is_hua_tui_shen("未", "辰") is True

    def test_tu_jin_3(self):
        assert is_hua_jin_shen("未", "戌") is True
        assert is_hua_tui_shen("戌", "未") is True

    def test_direction_not_reversed(self):
        """确认方向没有颠倒 (修复前的错误方向)"""
        # 旧错误: 辰→丑 为进, 丑→戌 为进 (实为退)
        assert is_hua_jin_shen("辰", "丑") is False   # 辰化丑是退神不是进神
        assert is_hua_jin_shen("丑", "戌") is False   # 丑化戌不是进神
        assert is_hua_tui_shen("丑", "辰") is False   # 丑化辰是进神不是退神
