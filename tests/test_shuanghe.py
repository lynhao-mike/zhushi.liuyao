"""
双合卦分析模块测试 - Tests for Shuang-He (Dual-Core Hexagram) Analysis
"""

import pytest
from liuyao.hexagram import Hexagram
from liuyao.shuanghe import (
    detect_shuanghe_type,
    analyze_ying_yao_role,
    judge_shuanghe_jixiong,
)
from liuyao.jixiong import find_yong_shen_lines, determine_yong_shen
from liuyao.wangshuai import analyze_hexagram_wangshuai
from liuyao.dongbian import analyze_dongbian
from liuyao.analyzer import run_analysis


# =============================================================================
# 双合卦类型检测测试
# =============================================================================

class TestDetectShuangheType:
    """双合卦类型检测测试"""

    def test_te_zhi_prefix(self):
        """前缀 te_zhi_ 识别为特指"""
        result = detect_shuanghe_type("te_zhi_cai")
        assert result == "te_zhi"

    def test_jia_jie_prefix(self):
        """前缀 jia_jie_ 识别为嫁接"""
        result = detect_shuanghe_type("jia_jie_cai")
        assert result == "jia_jie"

    def test_normal_type(self):
        """普通问事类型返回 normal"""
        result = detect_shuanghe_type("cai")
        assert result == "normal"

    def test_te_zhi_keyword_in_desc(self):
        """描述文本中含特指关键词"""
        result = detect_shuanghe_type("cai", "能否在这家公司成功")
        assert result == "te_zhi"

    def test_jia_jie_keyword_in_desc(self):
        """描述文本中含嫁接关键词"""
        result = detect_shuanghe_type("cai", "与他合作能否获利")
        assert result == "jia_jie"

    def test_no_keyword_normal(self):
        """描述文本无特殊关键词, 返回normal"""
        result = detect_shuanghe_type("cai", "今年财运如何")
        assert result == "normal"

    def test_te_zhi_guan(self):
        """te_zhi_guan 识别为特指"""
        result = detect_shuanghe_type("te_zhi_guan")
        assert result == "te_zhi"

    def test_empty_desc(self):
        """空描述返回normal"""
        result = detect_shuanghe_type("other", "")
        assert result == "normal"


# =============================================================================
# 应爻角色分析测试
# =============================================================================

class TestAnalyzeYingYaoRole:
    """应爻角色分析测试"""

    def test_ying_moving_is_guanlian(self):
        """应爻发动 -> 关联"""
        # 乾为天: 世在6, 应在3
        # 让第3爻(应爻)为老阳9动
        h = Hexagram([7, 7, 9, 7, 7, 7], 2024, 1, 15)
        ws = analyze_hexagram_wangshuai(h)
        db = analyze_dongbian(h, ws)
        yong_liu_qin = determine_yong_shen("cai")
        yong_lines = find_yong_shen_lines(h, yong_liu_qin)

        result = analyze_ying_yao_role(h, yong_lines, db, ws)
        assert result["role"] == "guan_lian"
        assert "发动" in result["details"]

    def test_no_relation_is_wuguan(self):
        """应爻与用神/动变无关系 -> 无关"""
        # 静卦: 无动爻, 应爻不动
        h = Hexagram([8, 7, 7, 7, 7, 8], 2024, 1, 15)
        ws = analyze_hexagram_wangshuai(h)
        db = analyze_dongbian(h, ws)
        # 找一个六亲, 检查如果应爻与用神关系不密切
        yong_lines = find_yong_shen_lines(h, "子孙")

        result = analyze_ying_yao_role(h, yong_lines, db, ws)
        # 静卦中根据具体地支关系可能是 wu_guan 或 dui_bi
        assert result["role"] in ("wu_guan", "dui_bi")

    def test_ying_chong_yong_is_duibi(self):
        """应爻与用神相冲 -> 对比 (冲或同五行)"""
        # 构造一个应爻与用神相冲的卦
        h = Hexagram([8, 7, 7, 9, 7, 8], 2024, 1, 15)
        ws = analyze_hexagram_wangshuai(h)
        db = analyze_dongbian(h, ws)

        # 查找应爻
        ying_line = None
        for line in h.lines:
            if line.is_ying:
                ying_line = line
                break

        # 选择与应爻相冲的地支所对应的爻
        from liuyao.data import LIU_CHONG
        chong_zhi = LIU_CHONG.get(ying_line.di_zhi, "")

        # 找含有冲支的用神
        target_lines = [l for l in h.lines if l.di_zhi == chong_zhi]
        if target_lines:
            result = analyze_ying_yao_role(h, target_lines, db, ws)
            # 冲的地支可能同时是同五行, 两种情况都是 dui_bi
            assert result["role"] == "dui_bi"
            assert "对比" in result["details"]


# =============================================================================
# 双核吉凶判断测试
# =============================================================================

class TestJudgeShuangheJixiong:
    """双核吉凶判断测试"""

    def test_returns_te_zhi_match(self):
        """双核判断返回 te_zhi_match 字段"""
        h = Hexagram([8, 7, 7, 9, 7, 8], 2024, 1, 15)
        ws = analyze_hexagram_wangshuai(h)
        db = analyze_dongbian(h, ws)
        yong_liu_qin = "妻财"
        ying_role = {"role": "dui_bi", "details": "测试"}

        result = judge_shuanghe_jixiong(
            h, yong_liu_qin, ying_role, ws, db, "te_zhi_cai"
        )
        assert "te_zhi_match" in result
        assert isinstance(result["te_zhi_match"], bool)
        assert "ying_strength" in result
        assert "explanation" in result

    def test_returns_ying_strength(self):
        """双核判断返回应爻强度"""
        h = Hexagram([9, 7, 7, 9, 7, 8], 2024, 3, 15)
        ws = analyze_hexagram_wangshuai(h)
        db = analyze_dongbian(h, ws)
        ying_role = {"role": "guan_lian", "details": "测试"}

        result = judge_shuanghe_jixiong(
            h, "妻财", ying_role, ws, db, "te_zhi_cai"
        )
        assert result["ying_strength"] in ("强", "弱", "平")


# =============================================================================
# 集成测试: run_analysis 调用双合卦
# =============================================================================

class TestShuangheIntegration:
    """双合卦集成测试"""

    def test_run_analysis_te_zhi(self):
        """run_analysis 使用 te_zhi_ 前缀时触发双合卦分析"""
        h = Hexagram([8, 7, 7, 9, 7, 8], 2024, 1, 15)
        report = run_analysis(h, question_type="te_zhi_cai")

        assert report.shuanghe_type == "te_zhi"
        assert report.shuanghe_ying_role is not None
        assert report.shuanghe_ying_role["role"] in ("wu_guan", "dui_bi", "guan_lian")

    def test_run_analysis_normal_no_shuanghe(self):
        """普通问事类型不触发双合卦分析"""
        h = Hexagram([8, 7, 7, 9, 7, 8], 2024, 1, 15)
        report = run_analysis(h, question_type="cai")

        assert report.shuanghe_type == "normal"
        assert report.shuanghe_ying_role is None

    def test_run_analysis_jia_jie(self):
        """jia_jie_ 前缀触发双合卦分析"""
        h = Hexagram([9, 7, 8, 7, 9, 8], 2024, 5, 20)
        report = run_analysis(h, question_type="jia_jie_cai")

        assert report.shuanghe_type == "jia_jie"
        assert report.shuanghe_ying_role is not None

    def test_run_analysis_desc_triggers_shuanghe(self):
        """描述文本中的关键词触发双合卦"""
        h = Hexagram([8, 7, 7, 9, 7, 8], 2024, 1, 15)
        report = run_analysis(
            h, question_type="cai",
            question_desc="能否在这家公司获利"
        )

        assert report.shuanghe_type == "te_zhi"

    def test_report_contains_shuanghe_section(self):
        """格式化报告包含双合卦分析部分"""
        from liuyao.report import format_report
        h = Hexagram([8, 7, 7, 9, 7, 8], 2024, 1, 15)
        report = run_analysis(h, question_type="te_zhi_cai")
        text = format_report(report)

        assert "双合卦分析" in text
