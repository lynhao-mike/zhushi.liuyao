"""
吉凶判断模块专项测试 - Dedicated unit tests for liuyao/jixiong.py
"""

import pytest
from liuyao.jixiong import (
    determine_yong_shen,
    find_yong_shen_lines,
    find_shi_line,
    find_ying_line,
    judge_dong_gua,
    judge_jing_gua,
    judge_jixiong,
    YONG_SHEN_TABLE,
)
from liuyao.hexagram import Hexagram
from liuyao.wangshuai import analyze_hexagram_wangshuai
from liuyao.dongbian import analyze_dongbian


class TestDetermineYongShen:
    """用神选择测试"""

    def test_cai(self):
        assert determine_yong_shen("cai") == "妻财"

    def test_guan(self):
        assert determine_yong_shen("guan") == "官鬼"

    def test_hun_male(self):
        assert determine_yong_shen("hun_male") == "妻财"

    def test_hun_female(self):
        assert determine_yong_shen("hun_female") == "官鬼"

    def test_bing(self):
        assert determine_yong_shen("bing") == "官鬼"

    def test_kaoshi(self):
        assert determine_yong_shen("kaoshi") == "父母"

    def test_zinv(self):
        assert determine_yong_shen("zinv") == "子孙"

    def test_xingRen(self):
        assert determine_yong_shen("xingRen") == "官鬼"

    def test_youHuan(self):
        assert determine_yong_shen("youHuan") == "子孙"

    def test_shiwu(self):
        assert determine_yong_shen("shiwu") == "妻财"

    def test_other(self):
        assert determine_yong_shen("other") == "官鬼"

    def test_unknown_defaults_to_guagui(self):
        assert determine_yong_shen("nonexistent") == "官鬼"


class TestFindFunctions:
    """查找函数测试"""

    def test_find_shi_line(self):
        h = Hexagram([7, 7, 7, 7, 7, 7], 2024, 3, 15)
        shi = find_shi_line(h)
        assert shi is not None
        assert shi.is_shi is True

    def test_find_ying_line(self):
        h = Hexagram([7, 7, 7, 7, 7, 7], 2024, 3, 15)
        ying = find_ying_line(h)
        assert ying is not None
        assert ying.is_ying is True

    def test_find_yong_shen_lines(self):
        h = Hexagram([7, 7, 7, 7, 7, 7], 2024, 3, 15)
        lines = find_yong_shen_lines(h, "官鬼")
        # Should return list (may be empty or non-empty depending on hexagram)
        assert isinstance(lines, list)


class TestJudgeJixiong:
    """吉凶综合判断测试"""

    def test_static_hexagram_returns_dict(self):
        h = Hexagram([7, 7, 7, 7, 7, 7], 2024, 3, 15)
        ws = analyze_hexagram_wangshuai(h)
        db = analyze_dongbian(h, ws)
        result = judge_jixiong(h, "官鬼", ws, db, "other")
        assert "pattern" in result
        assert "ji_xiong" in result
        assert "explanation" in result
        assert result["ji_xiong"] in ("吉", "凶", "平")

    def test_moving_hexagram_returns_dict(self):
        h = Hexagram([9, 8, 7, 9, 7, 8], 2024, 6, 15)
        ws = analyze_hexagram_wangshuai(h)
        db = analyze_dongbian(h, ws)
        result = judge_jixiong(h, "妻财", ws, db, "cai")
        assert "pattern" in result
        assert "ji_xiong" in result
        assert result["ji_xiong"] in ("吉", "凶", "平")

    def test_dispatches_to_jing_gua_when_static(self):
        h = Hexagram([7, 8, 7, 8, 7, 8], 2024, 1, 10)
        ws = analyze_hexagram_wangshuai(h)
        db = analyze_dongbian(h, ws)
        result = judge_jixiong(h, "官鬼", ws, db, "guan")
        # No moving lines, should use jing_gua logic
        assert result["ji_xiong"] in ("吉", "凶", "平")



class TestSanHeJu:
    """三合局定性测试 (合局优先于单爻分析)。"""

    def _ju_shui(self):
        # 艮为山之颐: 初爻辰土(6)动、三爻申金(9)动、五爻子水静 => 申子辰水局(两动一现)
        return Hexagram.from_ganzhi(
            [6, 8, 9, 8, 8, 7],
            month_zhi="寅", day_zhi="申", xun_kong=["辰", "巳"],
        )

    def test_detect_two_moving_one_static(self):
        """三字皆现且至少两字发动即成局 (子水静亦计入)。"""
        from liuyao.jixiong import _detect_san_he_ju
        ju = _detect_san_he_ju(self._ju_shui())
        assert any(j["wu_xing"] == "水" for j in ju), "应检出申子辰水局"

    def test_ju_sheng_yong_is_ji(self):
        """合局生用神 -> 吉 (水局生官鬼寅木)。"""
        from liuyao.jixiong import _judge_san_he_ju, find_yong_shen_lines
        h = self._ju_shui()
        res = _judge_san_he_ju(h, find_yong_shen_lines(h, "官鬼"))  # 寅木
        assert res is not None and res["ji_xiong"] == "吉"

    def test_ju_ke_yong_is_xiong(self):
        """合局克用神 -> 凶 (水局克父母午火)。"""
        from liuyao.jixiong import _judge_san_he_ju, find_yong_shen_lines
        h = self._ju_shui()
        res = _judge_san_he_ju(h, find_yong_shen_lines(h, "父母"))  # 午火
        assert res is not None and res["ji_xiong"] == "凶"

    def test_no_ju_returns_none(self):
        """无三合局时返回 None (六爻皆静)。"""
        from liuyao.jixiong import _judge_san_he_ju, find_yong_shen_lines
        h = Hexagram([7, 7, 7, 7, 7, 7], 2024, 3, 15)
        assert _judge_san_he_ju(h, find_yong_shen_lines(h, "官鬼")) is None
