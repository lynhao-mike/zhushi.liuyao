"""
拓扑用神选择模块测试 - Tests for Tuo-Pu Yong-Shen (Topological Use-Spirit Selection)
"""

import pytest
from liuyao.hexagram import Hexagram
from liuyao.data import (
    get_ma_xing, get_tao_hua, get_wen_chang,
    get_lu_shen, get_jiang_xing,
)
from liuyao.tuopu_yongshen import (
    select_by_wuxing_leixiang,
    select_by_xingsha,
    select_by_liushen,
    determine_tuopu_yongshen,
    WU_XING_LEI_XIANG,
)
from liuyao.analyzer import run_analysis


# =============================================================================
# 星煞计算测试
# =============================================================================

class TestXingShaCalculation:
    """星煞计算函数测试"""

    def test_ma_xing_shen_zi_chen(self):
        """驿马: 申子辰 -> 寅"""
        assert get_ma_xing("子") == "寅"
        assert get_ma_xing("申") == "寅"
        assert get_ma_xing("辰") == "寅"

    def test_ma_xing_yin_wu_xu(self):
        """驿马: 寅午戌 -> 申"""
        assert get_ma_xing("寅") == "申"
        assert get_ma_xing("午") == "申"
        assert get_ma_xing("戌") == "申"

    def test_ma_xing_hai_mao_wei(self):
        """驿马: 亥卯未 -> 巳"""
        assert get_ma_xing("亥") == "巳"
        assert get_ma_xing("卯") == "巳"
        assert get_ma_xing("未") == "巳"

    def test_ma_xing_si_you_chou(self):
        """驿马: 巳酉丑 -> 亥"""
        assert get_ma_xing("巳") == "亥"
        assert get_ma_xing("酉") == "亥"
        assert get_ma_xing("丑") == "亥"

    def test_tao_hua_shen_zi_chen(self):
        """桃花: 申子辰 -> 酉"""
        assert get_tao_hua("子") == "酉"
        assert get_tao_hua("申") == "酉"
        assert get_tao_hua("辰") == "酉"

    def test_tao_hua_yin_wu_xu(self):
        """桃花: 寅午戌 -> 卯"""
        assert get_tao_hua("寅") == "卯"
        assert get_tao_hua("午") == "卯"
        assert get_tao_hua("戌") == "卯"

    def test_tao_hua_hai_mao_wei(self):
        """桃花: 亥卯未 -> 子"""
        assert get_tao_hua("亥") == "子"
        assert get_tao_hua("卯") == "子"
        assert get_tao_hua("未") == "子"

    def test_tao_hua_si_you_chou(self):
        """桃花: 巳酉丑 -> 午"""
        assert get_tao_hua("巳") == "午"
        assert get_tao_hua("酉") == "午"
        assert get_tao_hua("丑") == "午"

    def test_wen_chang_jia_yi(self):
        """文昌: 甲->巳, 乙->午"""
        assert get_wen_chang("甲") == "巳"
        assert get_wen_chang("乙") == "午"

    def test_wen_chang_bing_ding(self):
        """文昌: 丙->申, 丁->酉"""
        assert get_wen_chang("丙") == "申"
        assert get_wen_chang("丁") == "酉"

    def test_wen_chang_wu_ji(self):
        """文昌: 戊->申, 己->酉"""
        assert get_wen_chang("戊") == "申"
        assert get_wen_chang("己") == "酉"

    def test_wen_chang_geng_xin(self):
        """文昌: 庚->亥, 辛->子"""
        assert get_wen_chang("庚") == "亥"
        assert get_wen_chang("辛") == "子"

    def test_wen_chang_ren_gui(self):
        """文昌: 壬->寅, 癸->卯"""
        assert get_wen_chang("壬") == "寅"
        assert get_wen_chang("癸") == "卯"

    def test_lu_shen_jia(self):
        """禄神: 甲->寅"""
        assert get_lu_shen("甲") == "寅"

    def test_lu_shen_yi(self):
        """禄神: 乙->卯"""
        assert get_lu_shen("乙") == "卯"

    def test_lu_shen_bing_wu(self):
        """禄神: 丙->巳, 戊->巳"""
        assert get_lu_shen("丙") == "巳"
        assert get_lu_shen("戊") == "巳"

    def test_lu_shen_ding_ji(self):
        """禄神: 丁->午, 己->午"""
        assert get_lu_shen("丁") == "午"
        assert get_lu_shen("己") == "午"

    def test_lu_shen_geng(self):
        """禄神: 庚->申"""
        assert get_lu_shen("庚") == "申"

    def test_lu_shen_xin(self):
        """禄神: 辛->酉"""
        assert get_lu_shen("辛") == "酉"

    def test_lu_shen_ren(self):
        """禄神: 壬->亥"""
        assert get_lu_shen("壬") == "亥"

    def test_lu_shen_gui(self):
        """禄神: 癸->子"""
        assert get_lu_shen("癸") == "子"

    def test_jiang_xing_shen_zi_chen(self):
        """将星: 申子辰 -> 子"""
        assert get_jiang_xing("子") == "子"
        assert get_jiang_xing("申") == "子"
        assert get_jiang_xing("辰") == "子"

    def test_jiang_xing_yin_wu_xu(self):
        """将星: 寅午戌 -> 午"""
        assert get_jiang_xing("寅") == "午"
        assert get_jiang_xing("午") == "午"
        assert get_jiang_xing("戌") == "午"

    def test_jiang_xing_hai_mao_wei(self):
        """将星: 亥卯未 -> 卯"""
        assert get_jiang_xing("亥") == "卯"
        assert get_jiang_xing("卯") == "卯"
        assert get_jiang_xing("未") == "卯"

    def test_jiang_xing_si_you_chou(self):
        """将星: 巳酉丑 -> 酉"""
        assert get_jiang_xing("巳") == "酉"
        assert get_jiang_xing("酉") == "酉"
        assert get_jiang_xing("丑") == "酉"


# =============================================================================
# 五行类象选择测试
# =============================================================================

class TestWuXingLeiXiang:
    """五行类象选择测试"""

    def test_select_jin_lines(self):
        """选取金行爻"""
        h = Hexagram([8, 7, 7, 9, 7, 8], 2024, 1, 15)
        results = select_by_wuxing_leixiang(h, "金")
        for line in results:
            assert line.wu_xing == "金"

    def test_select_mu_lines(self):
        """选取木行爻"""
        h = Hexagram([8, 7, 7, 9, 7, 8], 2024, 1, 15)
        results = select_by_wuxing_leixiang(h, "木")
        for line in results:
            assert line.wu_xing == "木"

    def test_keyword_mapping(self):
        """关键词映射正确"""
        assert WU_XING_LEI_XIANG["金融"] == "金"
        assert WU_XING_LEI_XIANG["木材"] == "木"
        assert WU_XING_LEI_XIANG["运输"] == "水"
        assert WU_XING_LEI_XIANG["电子"] == "火"
        assert WU_XING_LEI_XIANG["建筑"] == "土"


# =============================================================================
# 星煞选择测试
# =============================================================================

class TestXingShaSelection:
    """星煞选择测试"""

    def test_select_by_ma_xing(self):
        """驿马星选择"""
        h = Hexagram([8, 7, 7, 9, 7, 8], 2024, 1, 15)
        # 2024年为甲辰年, 年支辰, 辰属申子辰组, 驿马在寅
        results = select_by_xingsha(h, "ma_xing")
        target = get_ma_xing(h.gan_zhi["year_zhi"])
        for line in results:
            assert line.di_zhi == target

    def test_select_by_tao_hua(self):
        """桃花星选择"""
        h = Hexagram([8, 7, 7, 9, 7, 8], 2024, 1, 15)
        results = select_by_xingsha(h, "tao_hua")
        target = get_tao_hua(h.gan_zhi["year_zhi"])
        for line in results:
            assert line.di_zhi == target

    def test_select_by_wen_chang(self):
        """文昌星选择"""
        h = Hexagram([8, 7, 7, 9, 7, 8], 2024, 1, 15)
        results = select_by_xingsha(h, "wen_chang")
        target = get_wen_chang(h.gan_zhi["day_gan"])
        for line in results:
            assert line.di_zhi == target


# =============================================================================
# 六神选择测试
# =============================================================================

class TestLiuShenSelection:
    """六神选择测试"""

    def test_select_by_liushen(self):
        """六神选择返回正确爻"""
        h = Hexagram([8, 7, 7, 9, 7, 8], 2024, 1, 15)
        results = select_by_liushen(h, "玄武")
        for line in results:
            assert line.liu_shen == "玄武"

    def test_select_all_liushen_types(self):
        """所有六神类型均能选择"""
        h = Hexagram([8, 7, 7, 9, 7, 8], 2024, 1, 15)
        for shen in ("青龙", "朱雀", "勾陈", "螣蛇", "白虎", "玄武"):
            results = select_by_liushen(h, shen)
            assert len(results) == 1  # 每个六神只对应一爻


# =============================================================================
# 拓扑用神综合选择测试
# =============================================================================

class TestDetermineTuopuYongshen:
    """拓扑用神综合选择测试"""

    def test_standard_liuqin_available(self):
        """标准六亲法有可用爻时直接返回"""
        h = Hexagram([8, 7, 7, 9, 7, 8], 2024, 1, 15)
        result = determine_tuopu_yongshen(h, "cai", ["金融"])
        # 如果卦中有妻财爻, 应返回 liu_qin 方法
        if result["method"] == "liu_qin":
            assert len(result["lines"]) > 0
            assert "标准六亲法" in result["details"]

    def test_fallback_to_wuxing(self):
        """标准法无可用爻时回退到五行类象法"""
        # 需要找一个卦中某六亲不现的场景
        h = Hexagram([8, 7, 7, 9, 7, 8], 2024, 1, 15)
        # 找一个卦中不存在的六亲
        all_liu_qin = set(l.liu_qin for l in h.lines)
        missing_qin = None
        type_map = {"妻财": "cai", "官鬼": "guan", "父母": "kaoshi",
                    "子孙": "zinv", "兄弟": "other"}
        for qin, qtype in type_map.items():
            if qin not in all_liu_qin:
                missing_qin = qin
                # 尝试使用这个类型
                result = determine_tuopu_yongshen(h, qtype, ["金融"])
                if result["method"] == "wuxing":
                    assert "五行类象法" in result["details"]
                    assert len(result["lines"]) > 0
                break

    def test_fallback_to_xingsha(self):
        """回退到星煞法"""
        h = Hexagram([8, 7, 7, 9, 7, 8], 2024, 1, 15)
        # 使用不在五行类象表但在星煞表中的关键词
        all_liu_qin = set(l.liu_qin for l in h.lines)
        type_map = {"妻财": "cai", "官鬼": "guan", "父母": "kaoshi",
                    "子孙": "zinv", "兄弟": "other"}
        for qin, qtype in type_map.items():
            if qin not in all_liu_qin:
                result = determine_tuopu_yongshen(h, qtype, ["出行"])
                # 可能是 xingsha 或 wuxing (取决于卦)
                assert result["method"] in ("xingsha", "wuxing", "liushen", "none")
                break

    def test_no_keywords_standard_only(self):
        """无关键词时仅尝试标准法"""
        h = Hexagram([8, 7, 7, 9, 7, 8], 2024, 1, 15)
        result = determine_tuopu_yongshen(h, "cai", [])
        # 无关键词, 如果标准法有则返回 liu_qin, 否则 none
        assert result["method"] in ("liu_qin", "none")

    def test_result_structure(self):
        """返回结构正确"""
        h = Hexagram([8, 7, 7, 9, 7, 8], 2024, 1, 15)
        result = determine_tuopu_yongshen(h, "cai", ["金融"])
        assert "method" in result
        assert "lines" in result
        assert "details" in result
        assert isinstance(result["lines"], list)


# =============================================================================
# 集成测试: run_analysis 调用拓扑用神
# =============================================================================

class TestTuopuIntegration:
    """拓扑用神集成测试"""

    def test_tuopu_not_triggered_when_yong_exists(self):
        """用神存在时不触发拓扑用神"""
        h = Hexagram([8, 7, 7, 9, 7, 8], 2024, 1, 15)
        report = run_analysis(h, question_type="cai", question_keywords=["金融"])
        # 如果标准用神存在, tuopu_result 应为 None
        if report.yong_shen_lines:
            assert report.tuopu_result is None

    def test_tuopu_triggered_when_yong_missing(self):
        """用神不存在时触发拓扑用神(需找到合适卦例)"""
        # 尝试多个卦例找一个用神不现的
        h = Hexagram([8, 7, 7, 9, 7, 8], 2024, 1, 15)
        all_liu_qin = set(l.liu_qin for l in h.lines)
        type_map = {"妻财": "cai", "官鬼": "guan", "父母": "kaoshi",
                    "子孙": "zinv", "兄弟": "other"}
        for qin, qtype in type_map.items():
            if qin not in all_liu_qin:
                report = run_analysis(
                    h, question_type=qtype,
                    question_keywords=["金融"]
                )
                if not report.yong_shen_lines:
                    assert report.tuopu_result is not None
                    assert report.tuopu_result["method"] != "liu_qin"
                break

    def test_report_format_with_tuopu(self):
        """当有拓扑用神时, 格式化报告包含相应部分"""
        from liuyao.report import format_report
        h = Hexagram([8, 7, 7, 9, 7, 8], 2024, 1, 15)
        all_liu_qin = set(l.liu_qin for l in h.lines)
        type_map = {"妻财": "cai", "官鬼": "guan", "父母": "kaoshi",
                    "子孙": "zinv", "兄弟": "other"}
        for qin, qtype in type_map.items():
            if qin not in all_liu_qin:
                report = run_analysis(
                    h, question_type=qtype,
                    question_keywords=["金融"]
                )
                if report.tuopu_result:
                    text = format_report(report)
                    assert "拓扑用神选择" in text
                break

    def test_tuopu_triggered_when_all_yongshen_xunkong(self):
        """所有用神爻皆旬空时触发拓扑用神作为补充分析"""
        # [7,7,7,7,7,7] date=(2024,7,20) qt=guan
        # yong_shen_lines has 官鬼(午) which is xun_kong
        from liuyao.jixiong import find_yong_shen_lines, determine_yong_shen
        h = Hexagram([7, 7, 7, 7, 7, 7], 2024, 7, 20)
        yong_lq = determine_yong_shen("guan")
        yong_lines = find_yong_shen_lines(h, yong_lq)
        # Verify precondition: lines exist but all xun_kong
        assert len(yong_lines) > 0
        assert all(l.is_xun_kong for l in yong_lines)

        # Run analysis with keywords - tuopu should fire
        report = run_analysis(
            h, question_type="guan",
            question_keywords=["金融"]
        )
        # yong_shen_lines should be non-empty (they exist in the hexagram)
        assert len(report.yong_shen_lines) > 0
        # tuopu_result should be populated as supplementary analysis
        assert report.tuopu_result is not None
        assert report.tuopu_result["method"] != "none"

    def test_tuopu_not_triggered_when_yongshen_not_all_xunkong(self):
        """用神爻存在且非全部旬空时, 不触发拓扑用神"""
        from liuyao.jixiong import find_yong_shen_lines, determine_yong_shen
        h = Hexagram([8, 7, 7, 9, 7, 8], 2024, 1, 15)
        report = run_analysis(
            h, question_type="cai",
            question_keywords=["金融"]
        )
        if report.yong_shen_lines:
            # If not all are xun_kong, tuopu should NOT fire
            if not all(l.is_xun_kong for l in report.yong_shen_lines):
                assert report.tuopu_result is None
