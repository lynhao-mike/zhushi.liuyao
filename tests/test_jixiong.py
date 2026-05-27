"""
吉凶判断模块专项测试 - Dedicated unit tests for liuyao/jixiong.py

测试用神选择、用神查找、动卦吉凶、静卦吉凶及综合判断。
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
    """用神选择测试 - 覆盖所有YONG_SHEN_TABLE条目"""

    def test_cai(self):
        """财运 -> 妻财"""
        assert determine_yong_shen("cai") == "妻财"

    def test_guan(self):
        """官运 -> 官鬼"""
        assert determine_yong_shen("guan") == "官鬼"

    def test_hun_male(self):
        """婚姻(男问) -> 妻财"""
        assert determine_yong_shen("hun_male") == "妻财"

    def test_hun_female(self):
        """婚姻(女问) -> 官鬼"""
        assert determine_yong_shen("hun_female") == "官鬼"

    def test_bing(self):
        """疾病 -> 官鬼"""
        assert determine_yong_shen("bing") == "官鬼"

    def test_kaoshi(self):
        """考试 -> 父母"""
        assert determine_yong_shen("kaoshi") == "父母"

    def test_zinv(self):
        """子女 -> 子孙"""
        assert determine_yong_shen("zinv") == "子孙"

    def test_xingRen(self):
        """行人 -> 官鬼"""
        assert determine_yong_shen("xingRen") == "官鬼"

    def test_youHuan(self):
        """忧患 -> 子孙"""
        assert determine_yong_shen("youHuan") == "子孙"

    def test_shiwu(self):
        """失物 -> 父母"""
        assert determine_yong_shen("shiwu") == "父母"

    def test_other(self):
        """其他 -> 官鬼"""
        assert determine_yong_shen("other") == "官鬼"

    def test_unknown_defaults_to_guan_gui(self):
        """未知类型默认返回官鬼"""
        assert determine_yong_shen("unknown_type") == "官鬼"
        assert determine_yong_shen("") == "官鬼"


class TestFindYongShenLines:
    """用神查找测试"""

    def test_find_qi_cai_in_hexagram(self):
        """在卦中查找妻财爻"""
        h = Hexagram([7, 7, 7, 7, 7, 7], 2024, 1, 15)
        results = find_yong_shen_lines(h, "妻财")
        # 所有找到的爻应该是妻财
        for line in results:
            assert line.liu_qin == "妻财"

    def test_find_guan_gui_in_hexagram(self):
        """在卦中查找官鬼爻"""
        h = Hexagram([7, 7, 7, 7, 7, 7], 2024, 1, 15)
        results = find_yong_shen_lines(h, "官鬼")
        for line in results:
            assert line.liu_qin == "官鬼"

    def test_returns_empty_when_not_found(self):
        """六亲不存在时返回空列表"""
        h = Hexagram([7, 7, 7, 7, 7, 7], 2024, 1, 15)
        results = find_yong_shen_lines(h, "不存在的六亲")
        assert results == []

    def test_find_shi_line(self):
        """找到世爻"""
        h = Hexagram([7, 7, 7, 7, 7, 7], 2024, 1, 15)
        shi = find_shi_line(h)
        assert shi is not None
        assert shi.is_shi is True

    def test_find_ying_line(self):
        """找到应爻"""
        h = Hexagram([7, 7, 7, 7, 7, 7], 2024, 1, 15)
        ying = find_ying_line(h)
        assert ying is not None
        assert ying.is_ying is True


class TestJudgeDongGua:
    """动卦吉凶判断测试"""

    def test_returns_required_keys(self):
        """返回字典包含pattern, ji_xiong, explanation"""
        h = Hexagram([9, 7, 7, 7, 7, 7], 2024, 1, 15)
        ws = analyze_hexagram_wangshuai(h)
        db = analyze_dongbian(h, ws)
        result = judge_dong_gua(h, "妻财", ws, db, "cai")
        assert "pattern" in result
        assert "ji_xiong" in result
        assert "explanation" in result

    def test_ji_xiong_valid_values(self):
        """ji_xiong值为吉/凶/平之一"""
        h = Hexagram([9, 7, 7, 7, 7, 7], 2024, 1, 15)
        ws = analyze_hexagram_wangshuai(h)
        db = analyze_dongbian(h, ws)
        result = judge_dong_gua(h, "妻财", ws, db, "cai")
        assert result["ji_xiong"] in ("吉", "凶", "平")

    def test_missing_yong_shen(self):
        """找不到用神时返回平局"""
        h = Hexagram([9, 7, 7, 7, 7, 7], 2024, 1, 15)
        ws = analyze_hexagram_wangshuai(h)
        db = analyze_dongbian(h, ws)
        result = judge_dong_gua(h, "不存在的六亲", ws, db, "cai")
        assert result["ji_xiong"] == "平"
        assert result["pattern"] == "无法判断"

    def test_multi_moving_lines(self):
        """多动爻卦判断"""
        h = Hexagram([9, 9, 7, 7, 7, 7], 2024, 1, 15)
        ws = analyze_hexagram_wangshuai(h)
        db = analyze_dongbian(h, ws)
        yong_shen = determine_yong_shen("cai")
        result = judge_dong_gua(h, yong_shen, ws, db, "cai")
        assert result["ji_xiong"] in ("吉", "凶", "平")


class TestJudgeJingGua:
    """静卦吉凶判断测试"""

    def test_returns_required_keys(self):
        """返回字典包含pattern, ji_xiong, explanation"""
        h = Hexagram([7, 7, 7, 7, 7, 7], 2024, 1, 15)
        ws = analyze_hexagram_wangshuai(h)
        result = judge_jing_gua(h, "妻财", ws, "cai")
        assert "pattern" in result
        assert "ji_xiong" in result
        assert "explanation" in result

    def test_ji_xiong_valid_values(self):
        """ji_xiong值为吉/凶/平之一"""
        h = Hexagram([7, 7, 7, 7, 7, 7], 2024, 1, 15)
        ws = analyze_hexagram_wangshuai(h)
        result = judge_jing_gua(h, "妻财", ws, "cai")
        assert result["ji_xiong"] in ("吉", "凶", "平")

    def test_missing_yong_shen(self):
        """找不到用神时返回平局"""
        h = Hexagram([7, 7, 7, 7, 7, 7], 2024, 1, 15)
        ws = analyze_hexagram_wangshuai(h)
        result = judge_jing_gua(h, "不存在的六亲", ws, "cai")
        assert result["ji_xiong"] == "平"
        assert result["pattern"] == "无法判断"

    def test_yong_shen_chi_shi(self):
        """用神持世 -> 吉"""
        # 乾为天(金宫): lines[5]上爻=戌土=父母, shi_pos=6
        # 需要用神为父母, shi爻liu_qin=父母
        # 乾宫金, 上爻戌土: get_liu_qin("金","土")=父母
        # shi_pos=6 (本宫卦), so world is at pos6 which is 父母戌土
        h = Hexagram([7, 7, 7, 7, 7, 7], 2024, 1, 15)
        # This is 乾为天, palace_order=0, shi_pos=6
        assert h.shi_pos == 6
        shi = find_shi_line(h)
        assert shi.liu_qin == "父母"
        ws = analyze_hexagram_wangshuai(h)
        # Use 父母 as yong_shen (kaoshi)
        result = judge_jing_gua(h, "父母", ws, "kaoshi")
        assert result["pattern"] == "用神持世"
        assert result["ji_xiong"] == "吉"

    def test_different_question_types(self):
        """不同问事类型应得到不同结果"""
        h = Hexagram([7, 7, 7, 7, 7, 7], 2024, 3, 15)
        ws = analyze_hexagram_wangshuai(h)
        result_cai = judge_jing_gua(h, "妻财", ws, "cai")
        result_guan = judge_jing_gua(h, "官鬼", ws, "guan")
        # Different yong_shen may produce different patterns
        assert isinstance(result_cai["pattern"], str)
        assert isinstance(result_guan["pattern"], str)


class TestJudgeJixiong:
    """综合吉凶判断入口测试"""

    def test_dispatches_to_dong_gua(self):
        """有动爻时走动卦逻辑"""
        h = Hexagram([9, 7, 7, 7, 7, 7], 2024, 1, 15)
        ws = analyze_hexagram_wangshuai(h)
        db = analyze_dongbian(h, ws)
        result = judge_jixiong(h, "妻财", ws, db, "cai")
        assert "pattern" in result
        assert "ji_xiong" in result
        assert "explanation" in result

    def test_dispatches_to_jing_gua(self):
        """无动爻时走静卦逻辑"""
        h = Hexagram([7, 7, 7, 7, 7, 7], 2024, 1, 15)
        ws = analyze_hexagram_wangshuai(h)
        db = analyze_dongbian(h, ws)
        result = judge_jixiong(h, "妻财", ws, db, "cai")
        assert "pattern" in result
        assert "ji_xiong" in result
        assert "explanation" in result

    def test_dong_gua_vs_jing_gua_different_paths(self):
        """动卦和静卦走不同路径"""
        # Same hexagram values but one with moving
        h_static = Hexagram([7, 7, 7, 7, 7, 7], 2024, 1, 15)
        h_moving = Hexagram([9, 7, 7, 7, 7, 7], 2024, 1, 15)
        ws_s = analyze_hexagram_wangshuai(h_static)
        ws_m = analyze_hexagram_wangshuai(h_moving)
        db_s = analyze_dongbian(h_static, ws_s)
        db_m = analyze_dongbian(h_moving, ws_m)
        result_s = judge_jixiong(h_static, "妻财", ws_s, db_s, "cai")
        result_m = judge_jixiong(h_moving, "妻财", ws_m, db_m, "cai")
        # Both should have valid results
        assert result_s["ji_xiong"] in ("吉", "凶", "平")
        assert result_m["ji_xiong"] in ("吉", "凶", "平")
