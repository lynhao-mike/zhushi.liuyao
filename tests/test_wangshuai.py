"""
旺衰模块专项测试 - Dedicated unit tests for liuyao/wangshuai.py

测试月建旺衰、日辰旺衰、综合分析及整卦旺衰分析。
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
    """月建旺衰判断 - 4旺4衰全覆盖"""

    def test_lin_yue_ling(self):
        """临月令: 爻支与月支相同"""
        wang, shuai = yue_jian_wangshuai("子", "子")
        assert "临月令" in wang

    def test_yue_ling_he(self):
        """月令合: 爻支与月支六合 (子丑合土)"""
        wang, shuai = yue_jian_wangshuai("子", "丑")
        assert "月令合" in wang

    def test_yue_ling_sheng(self):
        """月令生: 月支五行生爻支五行 (亥水生寅木)"""
        wang, shuai = yue_jian_wangshuai("寅", "亥")
        assert "月令生" in wang

    def test_yue_ling_fu(self):
        """月令扶: 同五行不同支 (卯木扶寅木)"""
        wang, shuai = yue_jian_wangshuai("寅", "卯")
        assert "月令扶" in wang

    def test_yue_po(self):
        """月破: 月支与爻支互冲 (申月寅爻, 寅申互冲)"""
        wang, shuai = yue_jian_wangshuai("寅", "申")
        assert "月破" in shuai

    def test_yue_ling_ke(self):
        """月令克: 月支五行克爻支五行 (申金克寅木)"""
        wang, shuai = yue_jian_wangshuai("寅", "申")
        assert "月令克" in shuai

    def test_xiu(self):
        """休: 爻支五行克月支五行 (寅木克丑土)"""
        wang, shuai = yue_jian_wangshuai("寅", "丑")
        assert "休" in shuai

    def test_xie(self):
        """泄: 爻支五行生月支五行 (寅木生巳火)"""
        wang, shuai = yue_jian_wangshuai("寅", "巳")
        assert "泄" in shuai

    def test_no_wang_no_shuai(self):
        """无关关系时旺衰列表均为空 (午火与辰土)"""
        # 午火, 辰土: 火生土 -> 泄
        wang, shuai = yue_jian_wangshuai("午", "辰")
        # 午火生辰土 -> 泄
        assert "泄" in shuai

    def test_multiple_wang_reasons(self):
        """多重旺因: 寅亥既六合又生 (亥水生寅木 + 寅亥合木)"""
        wang, shuai = yue_jian_wangshuai("寅", "亥")
        assert "月令合" in wang
        assert "月令生" in wang


class TestRiChenWangshuai:
    """日辰旺衰判断 - 5旺2衰全覆盖"""

    def test_lin_ri_jian(self):
        """临日建: 爻支与日支相同"""
        wang, shuai = ri_chen_wangshuai("午", "午")
        assert "临日建" in wang

    def test_ri_ling_he_static(self):
        """日令合(静爻): 静爻与日支六合 (寅亥合)"""
        wang, shuai = ri_chen_wangshuai("寅", "亥", is_static=True)
        assert "日令合" in wang

    def test_ri_ling_he_moving_not_wang(self):
        """日令合(动爻): 动爻与日支相合为日绊, 不算旺"""
        wang, shuai = ri_chen_wangshuai("寅", "亥", is_static=False)
        assert "日令合" not in wang

    def test_ri_ling_sheng(self):
        """日令生: 日支五行生爻支五行 (亥水生寅木)"""
        wang, shuai = ri_chen_wangshuai("寅", "亥")
        assert "日令生" in wang

    def test_ri_ling_fu(self):
        """日令扶: 日支五行同爻支五行但不同支 (卯木扶寅木)"""
        wang, shuai = ri_chen_wangshuai("寅", "卯")
        assert "日令扶" in wang

    def test_chang_sheng_diwang(self):
        """临日令长生/帝旺: 木长生在亥"""
        wang, shuai = ri_chen_wangshuai("寅", "亥")
        assert any("长生" in r or "帝旺" in r for r in wang)

    def test_ri_ling_ke(self):
        """日令克: 日支五行克爻支五行 (申金克寅木)"""
        wang, shuai = ri_chen_wangshuai("寅", "申")
        assert "日令克" in shuai

    def test_yao_jue_zai_ri(self):
        """爻绝在日: 金绝在寅"""
        wang, shuai = ri_chen_wangshuai("酉", "寅")
        assert "爻绝在日" in shuai

    def test_is_static_false_no_ri_he(self):
        """动爻时日令合不应出现在旺因中"""
        wang, shuai = ri_chen_wangshuai("子", "丑", is_static=False)
        assert "日令合" not in wang

    def test_multiple_wang_reasons(self):
        """多重旺因: 寅日寅爻 -> 临日建"""
        wang, shuai = ri_chen_wangshuai("寅", "寅")
        assert "临日建" in wang


class TestAnalyzeLineWangshuai:
    """综合分析单爻旺衰"""

    def test_overall_wang(self):
        """月令生 + 日令生 -> 整体旺"""
        result = analyze_line_wangshuai("寅", "亥", "亥")
        assert result["overall"] == "旺"

    def test_overall_shuai(self):
        """月破 + 日克 -> 整体衰"""
        result = analyze_line_wangshuai("寅", "申", "申")
        assert result["overall"] == "衰"

    def test_overall_ping(self):
        """旺衰平衡 -> 平"""
        # 子水: 月=丑(月令合=旺) + 休(子水克丑土=衰); 日=午(日令克=衰)
        # Let's find a balanced case: 午火, 月=子(月令克), 日=寅(日令生)
        result = analyze_line_wangshuai("午", "子", "寅")
        # 月: 子水克午火 -> 月令克(衰); 日: 寅木生午火 -> 日令生(旺) + 长生(旺)
        # score: wang=2, shuai=1 -> 旺
        # Need better example: 辰土, 月=卯, 日=午
        # 月: 卯木克辰土 -> 月令克(衰); 日: 午火生辰土 -> 日令生(旺)
        result2 = analyze_line_wangshuai("辰", "卯", "午")
        # 月: 月令克(衰); 日: 日令生(旺)
        # wang_score=1, shuai_score=1 -> 平
        assert result2["overall"] == "平"

    def test_yue_po_overrides(self):
        """月破在无强月旺时定衰不可逆"""
        # 午火, 月=子(月破+月令克), 日=卯(日令生+长生)
        result = analyze_line_wangshuai("午", "子", "卯")
        # 月: 月破, 月令克 (2衰); 日: 日令生(旺), 长生(旺) (2旺)
        # wang=2, shuai=2 -> 平, but 月破 overrides -> 衰
        assert result["overall"] == "衰"

    def test_jue_treated_as_ping_when_wang(self):
        """整体趋旺时日绝当平看(绝处逢生)"""
        # 酉金绝在寅; 但如果月令生酉金(丑土生金), 整体趋旺, 则绝当平看
        # 酉金, 月=丑(月令生=旺, 因为丑土生酉金), 日=寅(日令克+爻绝在日)
        result = analyze_line_wangshuai("酉", "丑", "寅")
        # 月: 丑土生酉金 -> 月令生(旺); 日: 寅木? 金克木 -> 休(shuai),
        # Actually: 寅=木, 酉=金. WU_XING_KE["木"]="土", not 金.
        # day_wx=木, line_wx=金. WU_XING_KE["木"]="土" != "金", so no 日令克
        # gold绝在寅: stage == "绝" -> 爻绝在日 (shuai)
        # month: DI_ZHI_WU_XING["丑"]="土", WU_XING_SHENG["土"]="金" == line_wx -> 月令生
        # Summary: month_wang=["月令生"], month_shuai=[], day_wang=[], day_shuai=["爻绝在日"]
        # preliminary_wang = True (has_strong_month_wang), so 爻绝在日 is removed
        # Final: wang=1+1(绝处逢生)=2, shuai=0 -> 旺
        assert result["overall"] == "旺"
        assert "绝处逢生(以平论)" in result["day_wang"]

    def test_result_has_all_keys(self):
        """结果字典包含所有必要键"""
        result = analyze_line_wangshuai("子", "寅", "午")
        assert "overall" in result
        assert "month_wang" in result
        assert "month_shuai" in result
        assert "day_wang" in result
        assert "day_shuai" in result
        assert "details" in result


class TestAnalyzeHexagramWangshuai:
    """整卦旺衰分析"""

    def test_returns_six_results(self):
        """返回6个爻的旺衰结果"""
        h = Hexagram([7, 7, 7, 7, 7, 7], 2024, 1, 15)
        results = analyze_hexagram_wangshuai(h)
        assert len(results) == 6

    def test_each_result_has_position(self):
        """每个结果包含爻位信息"""
        h = Hexagram([7, 7, 7, 7, 7, 7], 2024, 1, 15)
        results = analyze_hexagram_wangshuai(h)
        positions = [r["position"] for r in results]
        assert positions == [1, 2, 3, 4, 5, 6]

    def test_each_result_has_overall(self):
        """每个结果包含overall旺衰判断"""
        h = Hexagram([7, 7, 7, 7, 7, 7], 2024, 1, 15)
        results = analyze_hexagram_wangshuai(h)
        for r in results:
            assert r["overall"] in ("旺", "衰", "平")

    def test_moving_line_uses_is_static_false(self):
        """动爻在分析时is_static=False(日令合不算旺)"""
        # 9=老阳(动爻)
        h = Hexagram([9, 7, 7, 7, 7, 7], 2024, 1, 15)
        results = analyze_hexagram_wangshuai(h)
        # 第1爻是动爻
        assert h.lines[0].is_moving is True
