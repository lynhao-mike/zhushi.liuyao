"""
分析模块测试 - Tests for the analysis engine

测试旺衰分析、动变分析、吉凶判断、应期推断等模块。
"""

import pytest
from liuyao.hexagram import Hexagram
from liuyao.wangshuai import (
    yue_jian_wangshuai,
    ri_chen_wangshuai,
    analyze_line_wangshuai,
    analyze_hexagram_wangshuai,
)
from liuyao.dongbian import (
    is_hui_tou_sheng,
    is_hui_tou_ke,
    is_hua_jin_shen,
    is_hua_tui_shen,
    is_hua_jue,
    is_hua_po,
    analyze_dongbian,
    detect_an_dong,
)
from liuyao.jixiong import (
    determine_yong_shen,
    find_yong_shen_lines,
    find_shi_line,
    judge_jixiong,
)
from liuyao.yingqi import estimate_yingqi, analyze_yingqi
from liuyao.analyzer import run_analysis, AnalysisReport
from liuyao.report import format_report


# =============================================================================
# 旺衰分析测试
# =============================================================================

class TestWangShuai:
    """旺衰分析测试"""

    def test_lin_yue_ling(self):
        """临月令: 爻支与月支相同 -> 旺"""
        wang, shuai = yue_jian_wangshuai("寅", "寅")
        assert "临月令" in wang

    def test_yue_ling_he(self):
        """月令合: 爻支与月支六合 -> 旺"""
        # 寅亥合木
        wang, shuai = yue_jian_wangshuai("寅", "亥")
        assert "月令合" in wang

    def test_yue_ling_sheng(self):
        """月令生: 月支五行生爻支五行 -> 旺"""
        # 亥水生寅木
        wang, shuai = yue_jian_wangshuai("寅", "亥")
        assert "月令生" in wang

    def test_yue_ling_fu(self):
        """月令扶: 同五行不同支 -> 旺"""
        # 卯木扶寅木
        wang, shuai = yue_jian_wangshuai("寅", "卯")
        assert "月令扶" in wang

    def test_yue_po(self):
        """月破: 月支冲爻支 -> 衰"""
        # 申冲寅
        wang, shuai = yue_jian_wangshuai("寅", "申")
        assert "月破" in shuai

    def test_yue_ling_ke(self):
        """月令克: 月支五行克爻支五行 -> 衰"""
        # 申金克寅木
        wang, shuai = yue_jian_wangshuai("寅", "申")
        assert "月令克" in shuai

    def test_yao_ke_yue(self):
        """休: 爻克月 -> 衰"""
        # 寅木克丑土
        wang, shuai = yue_jian_wangshuai("寅", "丑")
        assert "休" in shuai

    def test_yao_sheng_yue(self):
        """泄: 爻生月 -> 衰"""
        # 寅木生巳火
        wang, shuai = yue_jian_wangshuai("寅", "巳")
        assert "泄" in shuai

    def test_ri_chen_lin_ri_jian(self):
        """临日建: 爻支与日支相同 -> 旺"""
        wang, shuai = ri_chen_wangshuai("午", "午")
        assert "临日建" in wang

    def test_ri_chen_ri_ling_sheng(self):
        """日令生: 日支五行生爻支五行 -> 旺"""
        # 亥水生寅木
        wang, shuai = ri_chen_wangshuai("寅", "亥")
        assert "日令生" in wang

    def test_ri_chen_ri_ling_fu(self):
        """日令扶: 同五行不同支 -> 旺"""
        wang, shuai = ri_chen_wangshuai("寅", "卯")
        assert "日令扶" in wang

    def test_ri_chen_changsheng_diwang(self):
        """临日令长生帝旺"""
        # 金长生在巳
        wang, shuai = ri_chen_wangshuai("申", "巳")
        assert any("长生" in r or "帝旺" in r for r in wang)

    def test_ri_chen_ri_ling_ke(self):
        """日令克: 日支五行克爻支五行 -> 衰"""
        # 申金克寅木
        wang, shuai = ri_chen_wangshuai("寅", "申")
        assert "日令克" in wang or "日令克" in shuai
        # Actually check shuai
        assert "日令克" in shuai

    def test_ri_chen_yao_jue(self):
        """爻绝在日: 爻五行在日支处于绝地 -> 衰"""
        # 金绝在寅 (金: 长生巳, 绝在寅)
        wang, shuai = ri_chen_wangshuai("申", "寅")
        assert "爻绝在日" in shuai

    def test_overall_wang(self):
        """综合旺: 月生日扶"""
        # 寅木, 月亥(水生木), 日卯(木扶木)
        result = analyze_line_wangshuai("寅", "亥", "卯")
        assert result["overall"] == "旺"

    def test_overall_shuai(self):
        """综合衰: 月克日克"""
        # 寅木, 月申(金克木+月破), 日酉(金克木)
        result = analyze_line_wangshuai("寅", "申", "酉")
        assert result["overall"] == "衰"

    def test_hexagram_wangshuai(self):
        """测试整卦旺衰分析"""
        # 2024-01-15: 丑月 寅日
        h = Hexagram([8, 7, 7, 9, 7, 8], 2024, 1, 15)
        results = analyze_hexagram_wangshuai(h)
        assert len(results) == 6
        for r in results:
            assert r["overall"] in ("旺", "衰", "平")
            assert "position" in r

    def test_jue_treated_as_ping_when_wang(self):
        """特殊规则: 整体趋旺时日绝当平看"""
        # 寅木, 月亥(水生木=旺), 日巳(木在巳... check)
        # 木: 长生亥, 沐浴子, 冠带丑, 临官寅, 帝旺卯, 衰辰, 病巳, 死午, 墓未, 绝申, 胎酉, 养戌
        # 木绝在申
        # 寅木, 月亥(水生木), 日申(金克木 + 木绝在申)
        # This is complicated - month wang (生) but day has both 克 and 绝
        # Let's test with a clear case: 卯木, 月寅(木扶), 日申(绝)
        result = analyze_line_wangshuai("卯", "寅", "申")
        # 月: 月令扶(旺)
        # 日: 日令克(衰), 爻绝在日(but should be treated as ping if overall wang)
        # Overall should still be determined by count
        assert "month_wang" in result


# =============================================================================
# 动变分析测试
# =============================================================================

class TestDongBian:
    """动变分析测试"""

    def test_hui_tou_sheng(self):
        """回头生: 变爻五行生本爻五行"""
        # 申金变亥水? No, 水生木. Let's do: 寅木, 变亥水 -> 水生木 = 回头生
        assert is_hui_tou_sheng("寅", "亥") is True
        # 寅木, 变午火 -> 木生火, 不是回头生
        assert is_hui_tou_sheng("寅", "午") is False

    def test_hui_tou_ke(self):
        """回头克: 变爻五行克本爻五行"""
        # 寅木, 变申金 -> 金克木 = 回头克
        assert is_hui_tou_ke("寅", "申") is True
        # 寅木, 变亥水 -> 水生木, 不是回头克
        assert is_hui_tou_ke("寅", "亥") is False

    def test_hua_jin_shen(self):
        """化进神: 同五行向前"""
        assert is_hua_jin_shen("寅", "卯") is True
        assert is_hua_jin_shen("申", "酉") is True
        assert is_hua_jin_shen("巳", "午") is True
        assert is_hua_jin_shen("亥", "子") is True
        # 反方向不是进神
        assert is_hua_jin_shen("卯", "寅") is False

    def test_hua_tui_shen(self):
        """化退神: 同五行后退"""
        assert is_hua_tui_shen("卯", "寅") is True
        assert is_hua_tui_shen("酉", "申") is True
        assert is_hua_tui_shen("午", "巳") is True
        assert is_hua_tui_shen("子", "亥") is True
        # 正方向不是退神
        assert is_hua_tui_shen("寅", "卯") is False

    def test_hua_jue(self):
        """化绝: 本爻五行在变爻处于绝地"""
        # 金绝在寅: 申金化寅
        assert is_hua_jue("申", "寅") is True
        # 木绝在申
        assert is_hua_jue("寅", "申") is True

    def test_hua_po(self):
        """化破: 本爻与变爻相冲"""
        assert is_hua_po("子", "午") is True
        assert is_hua_po("寅", "申") is True
        assert is_hua_po("子", "丑") is False

    def test_analyze_dongbian_with_moving(self):
        """带动爻的卦动变分析"""
        # [8, 7, 7, 9, 7, 8]: 第4爻动(老阳)
        h = Hexagram([8, 7, 7, 9, 7, 8], 2024, 1, 15)
        ws_results = analyze_hexagram_wangshuai(h)
        result = analyze_dongbian(h, ws_results)

        assert "moving_analyses" in result
        assert 4 in result["moving_analyses"]
        assert "useful_moving" in result
        assert "useless_moving" in result

    def test_analyze_dongbian_static(self):
        """纯静卦动变分析"""
        h = Hexagram([7, 7, 8, 8, 7, 8], 2024, 1, 15)
        ws_results = analyze_hexagram_wangshuai(h)
        result = analyze_dongbian(h, ws_results)

        assert result["moving_analyses"] == {}
        assert result["useful_moving"] == []

    def test_useless_moving_hui_tou_ke(self):
        """无用动爻: 回头克"""
        # 需要构造一个动爻变回头克的卦
        # 用老阳(9)和老阴(6)产生动爻
        # 我们需要找一个实际的例子
        h = Hexagram([8, 7, 7, 9, 7, 8], 2024, 1, 15)
        ws_results = analyze_hexagram_wangshuai(h)
        result = analyze_dongbian(h, ws_results)
        # 验证结构正确
        for pos, ma in result["moving_analyses"].items():
            assert "is_useless" in ma
            assert "趋旺" in ma
            assert "趋衰" in ma

    def test_an_dong_detection(self):
        """暗动检测: 静爻月旺日冲"""
        # 构造一个静爻得月旺且被日冲的情况
        # 2024-01-15: 丑月寅日, 找一个被寅冲的爻(申)且在丑月旺的
        # 申金, 丑月: 丑土生金=月令生(旺), 寅日冲申(日冲)
        # 需要卦中有申的静爻
        # 乾卦内卦纳甲: 子寅辰, 外卦: 午申戌
        # 用乾为天(纯卦, 全阳静): [7,7,7,7,7,7]
        h = Hexagram([7, 7, 7, 7, 7, 7], 2024, 1, 15)
        ws_results = analyze_hexagram_wangshuai(h)
        an_dong = detect_an_dong(h, ws_results)

        # 第5爻是申, 丑月(土生金=旺), 寅日冲申 -> 应该暗动
        found_shen = False
        for ad in an_dong:
            if ad["di_zhi"] == "申":
                found_shen = True
                assert "暗动" in ad["type"] or "冲起" in ad["type"]
        assert found_shen, f"未检测到申爻暗动, an_dong={an_dong}"


# =============================================================================
# 吉凶判断测试
# =============================================================================

class TestJiXiong:
    """吉凶判断测试"""

    def test_determine_yong_shen(self):
        """用神确定"""
        assert determine_yong_shen("cai") == "妻财"
        assert determine_yong_shen("guan") == "官鬼"
        assert determine_yong_shen("bing") == "官鬼"
        assert determine_yong_shen("kaoshi") == "父母"
        assert determine_yong_shen("zinv") == "子孙"
        assert determine_yong_shen("youHuan") == "子孙"

    def test_find_yong_shen_lines(self):
        """查找用神爻"""
        h = Hexagram([8, 7, 7, 9, 7, 8], 2024, 1, 15)
        # 找妻财爻
        cai_lines = find_yong_shen_lines(h, "妻财")
        for line in cai_lines:
            assert line.liu_qin == "妻财"

    def test_find_shi_line(self):
        """查找世爻"""
        h = Hexagram([8, 7, 7, 9, 7, 8], 2024, 1, 15)
        shi = find_shi_line(h)
        assert shi is not None
        assert shi.is_shi is True

    def test_jixiong_basic(self):
        """基本吉凶判断"""
        h = Hexagram([8, 7, 7, 9, 7, 8], 2024, 1, 15)
        ws = analyze_hexagram_wangshuai(h)
        db = analyze_dongbian(h, ws)
        result = judge_jixiong(h, "妻财", ws, db, "cai")

        assert "pattern" in result
        assert "ji_xiong" in result
        assert result["ji_xiong"] in ("吉", "凶", "平")
        assert "explanation" in result

    def test_jing_gua_judgment(self):
        """静卦判断"""
        # 全静卦
        h = Hexagram([7, 7, 8, 8, 7, 8], 2024, 1, 15)
        ws = analyze_hexagram_wangshuai(h)
        db = analyze_dongbian(h, ws)
        result = judge_jixiong(h, "妻财", ws, db, "cai")

        assert "pattern" in result
        assert result["ji_xiong"] in ("吉", "凶", "平")

    def test_dong_gua_yong_wang_shi_xing(self):
        """动卦: 用旺世兴局"""
        # 需要构造用神旺+世有日月扶的情况
        # 这取决于具体日期和卦, 只验证逻辑结构正确
        h = Hexagram([9, 7, 7, 8, 7, 8], 2024, 3, 15)
        ws = analyze_hexagram_wangshuai(h)
        db = analyze_dongbian(h, ws)
        result = judge_jixiong(h, "妻财", ws, db, "cai")
        # 只验证能产生结果
        assert result["ji_xiong"] in ("吉", "凶", "平")


# =============================================================================
# 应期推断测试
# =============================================================================

class TestYingQi:
    """应期推断测试"""

    def test_static_wang_line(self):
        """旺静爻应期: 逢冲"""
        h = Hexagram([7, 7, 7, 7, 7, 7], 2024, 1, 15)
        ws_results = analyze_hexagram_wangshuai(h)
        # 找一个旺的静爻
        for i, line in enumerate(h.lines):
            if ws_results[i]["overall"] == "旺":
                candidates = estimate_yingqi(line, ws_results[i])
                # 旺静爻应该有逢冲
                assert any("逢冲" in c for c in candidates), \
                    f"旺静爻应有逢冲候选, got: {candidates}"
                break

    def test_moving_line_yingqi(self):
        """动爻应期: 逢合或逢值"""
        h = Hexagram([9, 7, 7, 8, 7, 8], 2024, 1, 15)
        ws_results = analyze_hexagram_wangshuai(h)
        db = analyze_dongbian(h, ws_results)
        moving_analyses = db.get("moving_analyses", {})

        for line in h.lines:
            if line.is_moving:
                ma = moving_analyses.get(line.position)
                candidates = estimate_yingqi(line, ws_results[line.position - 1], ma)
                # 动爻应该有逢合或逢值
                assert len(candidates) > 0
                break

    def test_xunkong_yingqi(self):
        """旬空爻应期: 填空/冲空/出空"""
        h = Hexagram([7, 7, 7, 7, 7, 7], 2024, 1, 15)
        ws_results = analyze_hexagram_wangshuai(h)

        for i, line in enumerate(h.lines):
            if line.is_xun_kong:
                candidates = estimate_yingqi(line, ws_results[i])
                assert any("填空" in c for c in candidates)
                assert any("冲空" in c for c in candidates)
                assert any("出空" in c for c in candidates)
                break

    def test_analyze_yingqi(self):
        """完整应期分析"""
        h = Hexagram([8, 7, 7, 9, 7, 8], 2024, 1, 15)
        ws = analyze_hexagram_wangshuai(h)
        db = analyze_dongbian(h, ws)
        yong_lines = find_yong_shen_lines(h, "妻财")

        if yong_lines:
            results = analyze_yingqi(h, yong_lines, ws, db)
            assert len(results) > 0
            for r in results:
                assert "position" in r
                assert "candidates" in r
                assert len(r["candidates"]) > 0


# =============================================================================
# 分析编排器测试
# =============================================================================

class TestAnalyzer:
    """分析编排器测试"""

    def test_run_analysis_basic(self):
        """基本分析流程"""
        h = Hexagram([8, 7, 7, 9, 7, 8], 2024, 1, 15)
        report = run_analysis(h, "cai")

        assert isinstance(report, AnalysisReport)
        assert report.hexagram is h
        assert report.question_type == "cai"
        assert report.yong_shen_liu_qin == "妻财"
        assert len(report.wangshuai_results) == 6
        assert "moving_analyses" in report.dongbian_results
        assert "ji_xiong" in report.jixiong_result
    def test_run_analysis_all_types(self):
        """测试所有问事类型"""
        h = Hexagram([8, 7, 7, 9, 7, 8], 2024, 1, 15)
        for qtype in ["cai", "guan", "bing", "kaoshi", "zinv", "youHuan", "other"]:
            report = run_analysis(h, qtype)
            assert report.yong_shen_liu_qin != ""
            assert report.jixiong_result["ji_xiong"] in ("吉", "凶", "平")

    def test_run_analysis_includes_yimao_imagery(self):
        """单视角分析应生成《易冒》象法摘要, 供报告层取象。"""
        h = Hexagram([8, 7, 7, 9, 7, 8], 2024, 1, 15)
        report = run_analysis(h, "cai")
        imagery = report.yimao_imagery

        assert imagery["source"] == "docs/reference/yimao"
        assert "用神定吉凶" in imagery["principle"]
        assert imagery["trigram_images"]
        assert any("用神" in item["roles"] for item in imagery["line_images"])
        assert any(item["liu_qin_image"] for item in imagery["line_images"])

    def test_yimao_imagery_has_source_and_relevance_fields(self):
        """象法摘要每条爻象应有来源字段和问事相关性标记。"""
        h = Hexagram([8, 7, 7, 9, 7, 8], 2024, 1, 15)
        report = run_analysis(h, "cai")
        imagery = report.yimao_imagery

        assert imagery["question_type"] == "cai"
        for item in imagery["line_images"]:
            assert "liu_qin_source" in item
            assert "liu_shen_source" in item
            assert "yao_wei_source" in item
            assert "liu_qin_relevant" in item
        for tg in imagery["trigram_images"]:
            assert "source" in tg

    def test_yimao_imagery_filters_by_question_type(self):
        """问财时妻财爻应标记为相关，官鬼不在关注列表时应标记不相关。"""
        h = Hexagram([8, 7, 7, 9, 7, 8], 2024, 1, 15)
        report = run_analysis(h, "cai")
        imagery = report.yimao_imagery

        # 求财关注妻财/子孙/兄弟, 官鬼不在关注列表
        guan_items = [item for item in imagery["line_images"] if item["liu_qin"] == "官鬼"]
        for item in guan_items:
            assert item["liu_qin_relevant"] is False

        cai_items = [item for item in imagery["line_images"] if item["liu_qin"] == "妻财"]
        for item in cai_items:
            assert item["liu_qin_relevant"] is True

    def test_yimao_imagery_generates_combo_sentences(self):
        """象法摘要应生成高频组合线索句（如白虎临官鬼动）。"""
        h = Hexagram([8, 7, 7, 9, 7, 8], 2024, 1, 15)
        report = run_analysis(h, "cai")
        imagery = report.yimao_imagery

        assert "sentences" in imagery
        # 至少有一条组合句（如果卦中匹配到）或为空列表
        assert isinstance(imagery["sentences"], list)
        for s in imagery["sentences"]:
            assert "sentence" in s
            assert "source" in s
            assert "position" in s
            assert "signal_type" in s
            assert s["signal_type"] in ("象法印证", "象法警示")

    def test_yimao_signals_injected_into_jixiong_result(self):
        """匹配到组合句时应注入 jixiong_result['yimao_signals']。"""
        # 构造一个白虎临官鬼发动的卦（乙日起白虎，需在特定爻位匹配官鬼动爻）
        # 用宽泛测试：只要有组合句就应注入；否则不注入（不报错）
        h = Hexagram([8, 7, 7, 9, 7, 8], 2024, 1, 15)
        report = run_analysis(h, "bing")  # 问病，白虎临官鬼更易匹配
        jx = report.jixiong_result

        if report.yimao_imagery.get("sentences"):
            assert "yimao_signals" in jx
            for sig in jx["yimao_signals"]:
                assert "signal_type" in sig
                assert sig["signal_type"] in ("象法印证", "象法警示")
        else:
            assert "yimao_signals" not in jx or jx.get("yimao_signals") == []


    def test_run_analysis_static_hexagram(self):
        """静卦分析"""
        h = Hexagram([7, 8, 7, 8, 7, 8], 2024, 1, 15)
        report = run_analysis(h, "cai")
        assert report.dongbian_results["moving_analyses"] == {}


# =============================================================================
# 报告格式化测试
# =============================================================================

class TestReport:
    """报告格式化测试"""

    def test_format_report_complete(self):
        """完整报告输出"""
        h = Hexagram([8, 7, 7, 9, 7, 8], 2024, 1, 15)
        report = run_analysis(h, "cai")
        text = format_report(report)

        # 验证六个部分都存在
        assert "排卦信息" in text
        assert "日月信息" in text
        assert "各爻旺衰" in text
        assert "动变分析" in text
        assert "吉凶判断" in text
        assert "应期推断" in text

    def test_format_report_has_content(self):
        """报告各部分有内容"""
        h = Hexagram([8, 7, 7, 9, 7, 8], 2024, 1, 15)
        report = run_analysis(h, "cai")
        text = format_report(report)

        # 基本信息
        assert "本卦" in text
        assert "变卦" in text
        assert "用神" in text
        assert "妻财" in text  # 财运的用神

        # 日月信息
        assert "月建" in text
        assert "日辰" in text
        assert "旬空" in text

        # 旺衰有状态标记
        assert "旺" in text or "衰" in text or "平" in text

        # 吉凶有判断
        assert "吉" in text or "凶" in text

    def test_format_report_static_hexagram(self):
        """静卦报告"""
        h = Hexagram([7, 8, 7, 8, 7, 8], 2024, 1, 15)
        report = run_analysis(h, "guan")
        text = format_report(report)

        assert "静卦" in text
        assert "排卦信息" in text

    def test_format_report_multiple_moving(self):
        """多动爻卦报告"""
        # 3个动爻
        h = Hexagram([9, 6, 7, 9, 7, 8], 2024, 1, 15)
        report = run_analysis(h, "cai")
        text = format_report(report)

        assert "动变分析" in text
        # 应该列出多个动爻分析
        assert "->" in text


# =============================================================================
# 综合示例测试
# =============================================================================

class TestIntegration:
    """综合集成测试"""

    def test_full_pipeline_2024_01_15(self):
        """
        完整流程测试: 2024-01-15, 摇卦 [8,7,7,9,7,8], 问财运。
        验证整个分析管道能正确运行并生成有意义的结果。
        """
        h = Hexagram([8, 7, 7, 9, 7, 8], 2024, 1, 15)
        report = run_analysis(h, "cai")
        text = format_report(report)

        # 验证报告完整性
        assert len(text) > 200  # 报告应有相当长度
        assert report.jixiong_result["ji_xiong"] in ("吉", "凶", "平")
        assert len(report.wangshuai_results) == 6

    def test_full_pipeline_static(self):
        """纯静卦完整流程"""
        h = Hexagram([7, 7, 8, 8, 8, 7], 2024, 6, 15)
        report = run_analysis(h, "guan")
        text = format_report(report)

        assert "排卦信息" in text
        assert "吉凶判断" in text
        assert report.yong_shen_liu_qin == "官鬼"

    def test_full_pipeline_all_moving(self):
        """六爻全动卦"""
        h = Hexagram([9, 6, 9, 6, 9, 6], 2024, 3, 20)
        report = run_analysis(h, "other")
        text = format_report(report)

        assert "动变分析" in text
        # 6个动爻
        assert len(report.dongbian_results["moving_analyses"]) == 6

    def test_yong_shen_selection_by_type(self):
        """验证不同问事类型选择不同用神"""
        h = Hexagram([8, 7, 7, 9, 7, 8], 2024, 1, 15)

        r1 = run_analysis(h, "cai")
        assert r1.yong_shen_liu_qin == "妻财"

        r2 = run_analysis(h, "guan")
        assert r2.yong_shen_liu_qin == "官鬼"

        r3 = run_analysis(h, "kaoshi")
        assert r3.yong_shen_liu_qin == "父母"

        r4 = run_analysis(h, "zinv")
        assert r4.yong_shen_liu_qin == "子孙"

    def test_moving_line_generates_world(self):
        """
        测试动爻生世的情况能被正确识别。
        需要构造一个有用动爻生世爻的卦。
        """
        # 构造: 找一个卦使得有动爻的五行生世爻五行
        h = Hexagram([8, 7, 7, 9, 7, 8], 2024, 1, 15)
        report = run_analysis(h, "cai")

        # 验证动爻交互被正确计算
        interactions = report.dongbian_results.get("interactions", {})
        # 不管具体结果, 结构应该正确
        for pos, inter in interactions.items():
            assert "受生" in inter
            assert "受克" in inter



# =============================================================================
# 双视角分析测试
# =============================================================================

from liuyao.analyzer import run_dual_analysis, DualPerspectiveReport
from liuyao.jixiong import (
    DUAL_PERSPECTIVE_TABLE, get_dual_perspectives,
    YONG_SHEN_TABLE,
)
from liuyao.report import format_dual_report


class TestDualPerspective:
    """双(多)视角分析测试"""

    def test_yong_shen_table_includes_shiwu(self):
        """YONG_SHEN_TABLE 应包含 shiwu 类型"""
        assert "shiwu" in YONG_SHEN_TABLE
        assert YONG_SHEN_TABLE["shiwu"] == "妻财"

    def test_dual_perspective_table_shiwu(self):
        """失物应配置双视角: 父母 + 妻财"""
        assert "shiwu" in DUAL_PERSPECTIVE_TABLE
        ys_list = [ys for ys, _ in DUAL_PERSPECTIVE_TABLE["shiwu"]]
        assert "妻财" in ys_list
        assert "父母" in ys_list

    def test_dual_perspective_table_bing(self):
        """问病应配置双视角: 官鬼(病) + 子孙(药)"""
        assert "bing" in DUAL_PERSPECTIVE_TABLE
        ys_list = [ys for ys, _ in DUAL_PERSPECTIVE_TABLE["bing"]]
        assert "官鬼" in ys_list
        assert "子孙" in ys_list

    def test_get_dual_perspectives_shiwu(self):
        """失物类型: 应返回两个视角，妻财为主视角"""
        ps = get_dual_perspectives("shiwu")
        assert len(ps) == 2
        ys_set = {ys for ys, _ in ps}
        assert ys_set == {"妻财", "父母"}
        # 主视角（第一个）应为妻财
        assert ps[0][0] == "妻财"

    def test_get_dual_perspectives_single_type(self):
        """无双视角配置的类型(如 cai): 应退化为单元素列表"""
        ps = get_dual_perspectives("cai")
        assert len(ps) == 1
        assert ps[0][0] == "妻财"
        assert ps[0][1] == "默认视角"

    def test_run_analysis_with_yong_shen_override(self):
        """run_analysis 支持 yong_shen_override 参数"""
        h = Hexagram([8, 7, 7, 9, 7, 8], 2024, 1, 15)
        # shiwu 默认是妻财, 这里强制覆盖为父母
        report = run_analysis(h, "shiwu", yong_shen_override="父母")
        assert report.yong_shen_liu_qin == "父母"
        for line in report.yong_shen_lines:
            assert line.liu_qin == "父母"

    def test_run_analysis_perspective_label(self):
        """run_analysis 支持 perspective_label 参数"""
        h = Hexagram([8, 7, 7, 9, 7, 8], 2024, 1, 15)
        report = run_analysis(h, "shiwu", perspective_label="测试视角")
        assert report.perspective_label == "测试视角"

    def test_run_dual_analysis_shiwu(self):
        """失物类型: 双视角分析应产生两个视角"""
        h = Hexagram([8, 7, 7, 9, 7, 8], 2024, 1, 15)
        dual = run_dual_analysis(h, "shiwu")

        assert isinstance(dual, DualPerspectiveReport)
        assert dual.hexagram is h
        assert dual.question_type == "shiwu"
        assert len(dual.perspectives) == 2

        # 验证两个视角的用神不同
        ys_set = {p.yong_shen_liu_qin for p in dual.perspectives}
        assert ys_set == {"妻财", "父母"}

        # 共享部分应填充
        assert len(dual.wangshuai_results) == 6
        assert "moving_analyses" in dual.dongbian_results
        assert dual.shi_line is not None

        # 每个视角应有完整分析
        for p in dual.perspectives:
            assert p.perspective_label != ""
            assert "ji_xiong" in p.jixiong_result
            assert p.jixiong_result["ji_xiong"] in ("吉", "凶", "平")

    def test_run_dual_analysis_bing(self):
        """问病类型: 双视角分析应产生官鬼+子孙两个视角"""
        h = Hexagram([8, 7, 7, 9, 7, 8], 2024, 1, 15)
        dual = run_dual_analysis(h, "bing")

        assert len(dual.perspectives) == 2
        ys_set = {p.yong_shen_liu_qin for p in dual.perspectives}
        assert ys_set == {"官鬼", "子孙"}

    def test_run_dual_analysis_fallback(self):
        """无双视角配置的类型: 应退化为单视角"""
        h = Hexagram([8, 7, 7, 9, 7, 8], 2024, 1, 15)
        dual = run_dual_analysis(h, "cai")

        assert len(dual.perspectives) == 1
        assert dual.perspectives[0].yong_shen_liu_qin == "妻财"

    def test_dual_consensus_calculation(self):
        """consensus 应正确反映吉凶一致或分歧"""
        h = Hexagram([8, 7, 7, 9, 7, 8], 2024, 1, 15)
        dual = run_dual_analysis(h, "shiwu")

        ji_xiong_set = {p.jixiong_result["ji_xiong"] for p in dual.perspectives}
        if len(ji_xiong_set) == 1:
            assert "一致" in dual.consensus
        else:
            assert "分歧" in dual.consensus

    def test_dual_shared_computation_consistency(self):
        """共享部分(旺衰/动变)在所有视角应一致"""
        h = Hexagram([8, 7, 7, 9, 7, 8], 2024, 1, 15)
        dual = run_dual_analysis(h, "shiwu")

        # 各视角引用的旺衰结果应是同一个对象
        for p in dual.perspectives:
            assert p.wangshuai_results is dual.wangshuai_results
            assert p.dongbian_results is dual.dongbian_results
            assert p.shi_line is dual.shi_line

    def test_run_dual_analysis_includes_yimao_imagery_per_perspective(self):
        """双视角每个视角都应保留各自用神对应的《易冒》象法摘要。"""
        h = Hexagram([8, 7, 7, 9, 7, 8], 2024, 1, 15)
        dual = run_dual_analysis(h, "shiwu")

        for p in dual.perspectives:
            assert p.yimao_imagery["line_images"]
            assert any("用神" in item["roles"] for item in p.yimao_imagery["line_images"])

    def test_format_dual_report_complete(self):
        """双视角报告应包含所有必要部分"""
        h = Hexagram([8, 7, 7, 9, 7, 8], 2024, 1, 15)
        dual = run_dual_analysis(h, "shiwu")
        text = format_dual_report(dual)

        # 共享部分
        assert "排卦信息" in text
        assert "日月信息" in text
        assert "各爻旺衰" in text
        assert "动变分析" in text

        # 双视角对照
        assert "双视角吉凶判断" in text
        assert "视角1" in text
        assert "视角2" in text
        assert "贵重财物" in text  # 妻财视角标签（主视角）
        assert "物件本相" in text  # 父母视角标签（辅助）

        # 《易冒》象法摘要
        assert "《易冒》象法摘要" in text
        assert "用神定吉凶" in text

        # 综合结论
        assert "综合" in text

    def test_format_dual_report_bing(self):
        """问病双视角报告"""
        h = Hexagram([8, 7, 7, 9, 7, 8], 2024, 1, 15)
        dual = run_dual_analysis(h, "bing")
        text = format_dual_report(dual)

        assert "病情视角" in text
        assert "药效视角" in text

    def test_format_dual_report_no_redundancy(self):
        """共享段落只出现一次, 不应在视角块中重复"""
        h = Hexagram([8, 7, 7, 9, 7, 8], 2024, 1, 15)
        dual = run_dual_analysis(h, "shiwu")
        text = format_dual_report(dual)

        # 各爻旺衰段落标题只出现一次
        assert text.count("【各爻旺衰】") == 1
        assert text.count("【动变分析】") == 1
        assert text.count("【日月信息】") == 1


class TestShiwuSpecialCase:
    """失物用克世特例测试"""

    def test_shiwu_in_question_type_choices(self):
        """shiwu 应可作为有效的问事类型运行 run_analysis"""
        h = Hexagram([8, 7, 7, 9, 7, 8], 2024, 1, 15)
        report = run_analysis(h, "shiwu")
        assert report.yong_shen_liu_qin == "妻财"
        assert report.jixiong_result["ji_xiong"] in ("吉", "凶", "平")
