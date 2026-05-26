"""
月破真假分析模块测试 - Tests for yuepo module

测试月破真假判断、矛盾趋势分析。
"""

import pytest
from liuyao.hexagram import Hexagram
from liuyao.wangshuai import analyze_hexagram_wangshuai
from liuyao.dongbian import analyze_dongbian
from liuyao.yuepo import (
    is_zhen_po,
    analyze_maodun_qushi,
    analyze_yuepo,
)
from liuyao.data import LIU_CHONG


class TestIsZhenPo:
    """月破真假判断测试"""

    def test_moving_line_yue_po_is_false_break(self):
        """动而逢破不为真破: 动爻遇月破为假破"""
        # 2024-1-15: 丑月(丑冲未), 需要找动爻地支为未的情况
        # 坤外卦第4爻=丑, 第5爻=亥, 第6爻=酉
        # 坤内卦第1爻=未, 第2爻=巳, 第3爻=卯
        # 所以坤为地[6,6,6,6,6,6], 第1爻未在丑月被冲(月破)
        h = Hexagram([6, 6, 6, 6, 6, 6], 2024, 1, 15)
        ws_results = analyze_hexagram_wangshuai(h)
        db = analyze_dongbian(h, ws_results)

        # 找月破的动爻
        month_zhi = h.gan_zhi["month_zhi"]  # 丑
        for line in h.lines:
            if line.is_moving and LIU_CHONG.get(month_zhi) == line.di_zhi:
                result = is_zhen_po(line, h, db, ws_results)
                assert result["is_zhen_po"] is False
                assert "动而逢破" in result["reason"]
                break

    def test_hua_po_with_hui_tou_is_false_break(self):
        """化破但变爻可回头作用者不为真破"""
        # 需要构造: 动爻的变爻被月冲(化破), 且变爻对动爻有回头生/克
        # 这需要特定的卦象配置
        # 寅化申: 寅申冲(化破), 申金克寅木(回头克) -> 假破
        # 但这也是回头克, 按理论回头克本身就是无用动爻
        # 让我们测试有回头生的情况
        h = Hexagram([9, 7, 7, 8, 7, 8], 2024, 1, 15)
        ws_results = analyze_hexagram_wangshuai(h)
        db = analyze_dongbian(h, ws_results)
        # 检查是否有化破+回头作用
        month_zhi = h.gan_zhi["month_zhi"]
        for line in h.lines:
            if line.is_moving and line.bian_di_zhi:
                is_hua_po = (LIU_CHONG.get(month_zhi) == line.bian_di_zhi)
                if is_hua_po:
                    result = is_zhen_po(line, h, db, ws_results)
                    # 如果有回头作用, 应该是假破
                    if result["condition"] == "化破有回头作用":
                        assert result["is_zhen_po"] is False
                    break

    def test_hua_jin_shen_hua_po_is_false_break(self):
        """化进退又化破不为真破"""
        # 需要构造化进神+化破的情况
        # 进神: 寅->卯, 申->酉, 巳->午, 亥->子
        # 同时化破: 变爻被月冲
        # 如果月建冲变爻: 如寅月, 变爻为申就被冲
        # 寅化卯(进神), 卯在酉月被冲(月破)
        # 所以需要酉月, 有动爻寅化卯
        h = Hexagram([9, 7, 7, 8, 7, 8], 2024, 9, 15)  # 9月~酉月
        ws_results = analyze_hexagram_wangshuai(h)
        db = analyze_dongbian(h, ws_results)
        month_zhi = h.gan_zhi["month_zhi"]
        for line in h.lines:
            if line.is_moving and line.bian_di_zhi:
                from liuyao.dongbian import is_hua_jin_shen, is_hua_tui_shen
                has_jin_tui = (is_hua_jin_shen(line.di_zhi, line.bian_di_zhi) or
                               is_hua_tui_shen(line.di_zhi, line.bian_di_zhi))
                is_hua_po_flag = (LIU_CHONG.get(month_zhi) == line.bian_di_zhi)
                if has_jin_tui and is_hua_po_flag:
                    result = is_zhen_po(line, h, db, ws_results)
                    assert result["is_zhen_po"] is False
                    assert "进退" in result["reason"]
                    break

    def test_shi_yao_hua_po_in_self_divination_is_false(self):
        """自占自事世爻动而化破不为真破"""
        # 需要世爻动且变爻被月冲
        # 先找世爻位置, 然后让世爻动
        # 丑月: 丑冲未. 需要世爻动, 变爻为未
        # 尝试不同的卦
        h = Hexagram([9, 6, 9, 6, 9, 6], 2024, 1, 15)
        ws_results = analyze_hexagram_wangshuai(h)
        db = analyze_dongbian(h, ws_results)
        month_zhi = h.gan_zhi["month_zhi"]

        shi_line = None
        for line in h.lines:
            if line.is_shi:
                shi_line = line
                break

        if shi_line and shi_line.is_moving and shi_line.bian_di_zhi:
            is_hua_po_flag = (LIU_CHONG.get(month_zhi) == shi_line.bian_di_zhi)
            if is_hua_po_flag:
                result = is_zhen_po(shi_line, h, db, ws_results)
                assert result["is_zhen_po"] is False
                assert "世爻" in result["reason"]

    def test_static_line_yue_po_is_true_break(self):
        """静爻月破 = 真破"""
        # 丑月: 丑冲未. 需要静爻地支为未
        # 坤为地内卦: 未巳卯
        # [8,8,8,8,8,8] 全静
        h = Hexagram([8, 8, 8, 8, 8, 8], 2024, 1, 15)
        ws_results = analyze_hexagram_wangshuai(h)
        db = analyze_dongbian(h, ws_results)
        month_zhi = h.gan_zhi["month_zhi"]

        for line in h.lines:
            if not line.is_moving and LIU_CHONG.get(month_zhi) == line.di_zhi:
                result = is_zhen_po(line, h, db, ws_results)
                assert result["is_zhen_po"] is True
                assert "静爻" in result["reason"] or "真破" in result["reason"]
                break

    def test_non_yue_po_line(self):
        """非月破爻返回非真破"""
        h = Hexagram([7, 7, 7, 7, 7, 7], 2024, 1, 15)
        ws_results = analyze_hexagram_wangshuai(h)
        db = analyze_dongbian(h, ws_results)
        month_zhi = h.gan_zhi["month_zhi"]

        for line in h.lines:
            if LIU_CHONG.get(month_zhi) != line.di_zhi:
                result = is_zhen_po(line, h, db, ws_results)
                assert result["is_zhen_po"] is False
                assert "非月破" in result["reason"]
                break


class TestMaodunQushi:
    """矛盾趋势分析测试"""

    def test_maodun_detection(self):
        """检测矛盾趋势"""
        # 多动爻卦中可能有矛盾趋势
        h = Hexagram([9, 6, 9, 6, 9, 6], 2024, 1, 15)
        ws_results = analyze_hexagram_wangshuai(h)
        db = analyze_dongbian(h, ws_results)
        result = analyze_maodun_qushi(h, db, ws_results)
        # 验证结构
        assert isinstance(result, list)
        for md in result:
            assert "position" in md
            assert "wang_reasons" in md
            assert "shuai_reasons" in md
            assert "principle" in md
            assert "conclusion" in md

    def test_no_contradiction_in_static(self):
        """静卦无矛盾趋势"""
        h = Hexagram([7, 8, 7, 8, 7, 8], 2024, 1, 15)
        ws_results = analyze_hexagram_wangshuai(h)
        db = analyze_dongbian(h, ws_results)
        result = analyze_maodun_qushi(h, db, ws_results)
        assert result == []

    def test_shi_yao_principle(self):
        """世爻之变原则优先"""
        # 全动卦, 世爻应有矛盾时使用世爻之变原则
        h = Hexagram([9, 9, 9, 9, 9, 9], 2024, 1, 15)
        ws_results = analyze_hexagram_wangshuai(h)
        db = analyze_dongbian(h, ws_results)
        result = analyze_maodun_qushi(h, db, ws_results)
        # 如果有世爻矛盾, 应使用世爻之变原则
        for md in result:
            if md.get("is_shi"):
                assert md["principle"] == "世爻之变原则"
                break

    def test_internal_over_external(self):
        """重动轻静/重内轻外原则"""
        h = Hexagram([9, 6, 9, 6, 9, 6], 2024, 3, 15)
        ws_results = analyze_hexagram_wangshuai(h)
        db = analyze_dongbian(h, ws_results)
        result = analyze_maodun_qushi(h, db, ws_results)
        for md in result:
            if md["principle"] == "重动轻静/重内轻外":
                assert "内因" in md["conclusion"] or "外因" in md["conclusion"]
                break


class TestAnalyzeYuepo:
    """月破综合分析测试"""

    def test_comprehensive_analysis(self):
        """综合月破分析返回完整结构"""
        h = Hexagram([8, 7, 7, 9, 7, 8], 2024, 1, 15)
        ws_results = analyze_hexagram_wangshuai(h)
        db = analyze_dongbian(h, ws_results)
        result = analyze_yuepo(h, db, ws_results)

        assert "po_analyses" in result
        assert "maodun_qushi" in result
        assert "has_po" in result
        assert isinstance(result["po_analyses"], list)
        assert isinstance(result["maodun_qushi"], list)

    def test_no_po_lines(self):
        """无月破爻时结果正确"""
        # 在某些月份, 可能没有爻被月冲
        h = Hexagram([7, 7, 7, 7, 7, 7], 2024, 1, 15)
        ws_results = analyze_hexagram_wangshuai(h)
        db = analyze_dongbian(h, ws_results)
        month_zhi = h.gan_zhi["month_zhi"]
        result = analyze_yuepo(h, db, ws_results)
        # 验证逻辑: 检查是否有被月冲的爻
        has_po_line = any(
            LIU_CHONG.get(month_zhi) == l.di_zhi for l in h.lines)
        assert result["has_po"] == has_po_line

    def test_integration_with_analyzer(self):
        """与分析器集成测试"""
        from liuyao.analyzer import run_analysis
        h = Hexagram([8, 7, 7, 9, 7, 8], 2024, 1, 15)
        report = run_analysis(h, "cai")
        assert report.yuepo_results is not None
        assert "po_analyses" in report.yuepo_results
        assert "maodun_qushi" in report.yuepo_results

    def test_report_format_includes_yuepo(self):
        """报告格式包含月破分析"""
        from liuyao.analyzer import run_analysis
        from liuyao.report import format_report
        # 用坤为地[8,8,8,8,8,8] 丑月, 第1爻未被月冲
        h = Hexagram([8, 8, 8, 8, 8, 8], 2024, 1, 15)
        report = run_analysis(h, "cai")
        text = format_report(report)
        # 如果有月破爻, 报告应包含月破分析节
        if report.yuepo_results.get("has_po"):
            assert "月破真假分析" in text

    def test_po_analysis_all_fields(self):
        """月破分析项包含所有字段"""
        h = Hexagram([8, 8, 8, 8, 8, 8], 2024, 1, 15)
        ws_results = analyze_hexagram_wangshuai(h)
        db = analyze_dongbian(h, ws_results)
        result = analyze_yuepo(h, db, ws_results)
        for pa in result["po_analyses"]:
            assert "position" in pa
            assert "di_zhi" in pa
            assert "is_yue_po" in pa
            assert "analysis" in pa
            assert "is_zhen_po" in pa["analysis"]
            assert "reason" in pa["analysis"]
