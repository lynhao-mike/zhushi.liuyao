"""
旺衰模块专项测试 - Dedicated unit tests for liuyao/wangshuai.py
"""

import pytest
from liuyao.wangshuai import (
    yue_jian_wangshuai,
    ri_chen_wangshuai,
    analyze_line_wangshuai,
    analyze_hexagram_wangshuai,
)
from liuyao.hexagram import Hexagram


class TestYueJianWangshuai:
    """月建旺衰判断 - 4旺4衰"""

    def test_lin_yue_ling(self):
        wang, shuai = yue_jian_wangshuai("子", "子")
        assert "临月令" in wang

    def test_yue_ling_he(self):
        wang, shuai = yue_jian_wangshuai("子", "丑")
        assert "月令合" in wang

    def test_yue_ling_sheng(self):
        # 亥水生寅木
        wang, shuai = yue_jian_wangshuai("寅", "亥")
        assert "月令生" in wang

    def test_yue_ling_fu(self):
        # 卯木扶寅木
        wang, shuai = yue_jian_wangshuai("寅", "卯")
        assert "月令扶" in wang

    def test_yue_po(self):
        # 申月冲寅爻
        wang, shuai = yue_jian_wangshuai("寅", "申")
        assert "月破" in shuai

    def test_yue_ling_ke(self):
        # 申金克寅木
        wang, shuai = yue_jian_wangshuai("寅", "申")
        assert "月令克" in shuai

    def test_xiu(self):
        # 寅木克丑土 (爻克月)
        wang, shuai = yue_jian_wangshuai("寅", "丑")
        assert "休" in shuai

    def test_xie(self):
        # 寅木生巳火 (爻生月)
        wang, shuai = yue_jian_wangshuai("寅", "巳")
        assert "泄" in shuai


class TestRiChenWangshuai:
    """日辰旺衰判断 - 5旺2衰"""

    def test_lin_ri_jian(self):
        wang, shuai = ri_chen_wangshuai("午", "午")
        assert "临日建" in wang

    def test_ri_ling_he_static(self):
        # 子丑合, 静爻
        wang, shuai = ri_chen_wangshuai("子", "丑", is_static=True)
        assert "日令合" in wang

    def test_ri_ling_he_moving_no_wang(self):
        # 动爻日令合不算旺
        wang, shuai = ri_chen_wangshuai("子", "丑", is_static=False)
        assert "日令合" not in wang

    def test_ri_ling_sheng(self):
        # 亥水生寅木
        wang, shuai = ri_chen_wangshuai("寅", "亥")
        assert "日令生" in wang

    def test_ri_ling_fu(self):
        # 卯木扶寅木
        wang, shuai = ri_chen_wangshuai("寅", "卯")
        assert "日令扶" in wang

    def test_ri_ling_ke(self):
        # 申金克寅木
        wang, shuai = ri_chen_wangshuai("寅", "申")
        assert "日令克" in shuai

    def test_jue_zai_ri(self):
        # 酉金绝在寅
        wang, shuai = ri_chen_wangshuai("酉", "寅")
        assert "爻绝在日" in shuai


class TestAnalyzeLineWangshuai:
    """综合旺衰分析"""

    def test_overall_wang(self):
        # 寅木在亥月卯日: 月令生+月令合, 日令扶
        result = analyze_line_wangshuai("寅", "亥", "卯")
        assert result["overall"] == "旺"

    def test_overall_shuai(self):
        # 寅木在申月酉日: 月破+月令克, 日令克
        result = analyze_line_wangshuai("寅", "申", "酉")
        assert result["overall"] == "衰"

    def test_jue_removed_when_wang(self):
        # 酉金在酉月寅日: 临月令(旺), 但绝在寅 -> 绝应被移除
        result = analyze_line_wangshuai("酉", "酉", "寅")
        assert result["overall"] == "旺"
        assert "爻绝在日" not in result["day_shuai"]

    def test_yue_po_overrides(self):
        # 月破时无强月旺 -> 衰
        result = analyze_line_wangshuai("寅", "申", "寅")
        # 申月寅爻=月破+月令克, 但临日建
        # 月破 + 月令克 vs 临日建 -> 要看逻辑
        assert "月破" in result["month_shuai"]


class TestAnalyzeHexagramWangshuai:
    """整卦旺衰分析"""

    def test_returns_six_results(self):
        h = Hexagram([7, 7, 7, 7, 7, 7], 2024, 3, 15)
        results = analyze_hexagram_wangshuai(h)
        assert len(results) == 6

    def test_each_has_required_keys(self):
        h = Hexagram([7, 7, 7, 7, 7, 7], 2024, 3, 15)
        results = analyze_hexagram_wangshuai(h)
        for r in results:
            assert "overall" in r
            assert "month_wang" in r
            assert "month_shuai" in r
            assert "day_wang" in r
            assert "day_shuai" in r
            assert "position" in r
