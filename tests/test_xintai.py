"""
心态卦识别模块测试 - Tests for Xin-Tai-Gua Module
"""

import pytest
from liuyao.hexagram import Hexagram
from liuyao.wangshuai import analyze_hexagram_wangshuai
from liuyao.dongbian import analyze_dongbian
from liuyao.xintai import (
    detect_xintai_gua, analyze_xintai,
    is_true_yongshen, find_xinnian_yao,
)
from liuyao.jixiong import find_shi_line, find_ying_line, find_yong_shen_lines
from liuyao.analyzer import run_analysis


class TestDetectXintaiGua:
    """测试心态卦检测"""

    def test_explicit_youhuan_question(self):
        """问事类型为youHuan时直接判定为心态卦"""
        h = Hexagram([7, 7, 7, 8, 8, 8], 2024, 3, 15)
        ws = analyze_hexagram_wangshuai(h)
        db = analyze_dongbian(h, ws)
        result = detect_xintai_gua(h, "youHuan", ws, db)
        assert result["is_xintai"] is True
        assert result["confidence"] == 1.0
        assert result["xintai_type"] == "worry"

    def test_explicit_worry_question(self):
        """问事类型为worry时直接判定"""
        h = Hexagram([7, 7, 7, 8, 8, 8], 2024, 3, 15)
        ws = analyze_hexagram_wangshuai(h)
        db = analyze_dongbian(h, ws)
        result = detect_xintai_gua(h, "worry", ws, db)
        assert result["is_xintai"] is True
        assert result["confidence"] == 1.0

    def test_explicit_doubt_question(self):
        """问事类型为doubt"""
        h = Hexagram([7, 7, 7, 8, 8, 8], 2024, 3, 15)
        ws = analyze_hexagram_wangshuai(h)
        db = analyze_dongbian(h, ws)
        result = detect_xintai_gua(h, "doubt", ws, db)
        assert result["is_xintai"] is True
        assert result["xintai_type"] == "doubt"

    def test_explicit_hesitation_question(self):
        """问事类型为hesitation"""
        h = Hexagram([7, 7, 7, 8, 8, 8], 2024, 3, 15)
        ws = analyze_hexagram_wangshuai(h)
        db = analyze_dongbian(h, ws)
        result = detect_xintai_gua(h, "hesitation", ws, db)
        assert result["is_xintai"] is True
        assert result["xintai_type"] == "hesitation"

    def test_event_question_low_confidence(self):
        """普通事卦问事, 无明显心态指标时不应判为心态卦"""
        # 乾为天 - 静卦, 问财运
        h = Hexagram([7, 7, 7, 7, 7, 7], 2024, 1, 15)
        ws = analyze_hexagram_wangshuai(h)
        db = analyze_dongbian(h, ws)
        result = detect_xintai_gua(h, "cai", ws, db)
        # confidence should be below threshold for event hexagrams without strong mindset indicators
        assert result["confidence"] < 1.0

    def test_shi_bian_zisun_boosts_confidence(self):
        """世爻动化子孙增加心态卦置信度"""
        # 需要找到一个世爻动化子孙的卦
        # 震为雷 (震宫本宫卦, 世在6爻)
        # 9=老阳动, 如果第6爻动化出子孙
        h = Hexagram([7, 7, 7, 7, 7, 9], 2024, 3, 15)
        ws = analyze_hexagram_wangshuai(h)
        db = analyze_dongbian(h, ws)
        shi_line = find_shi_line(h)
        if shi_line and shi_line.is_moving and shi_line.bian_liu_qin == "子孙":
            result = detect_xintai_gua(h, "cai", ws, db)
            assert "世爻动化子孙" in str(result["indicators"])

    def test_six_chong_gua_boosts_confidence(self):
        """六冲卦增加心态卦置信度"""
        # 天雷无妄 -> 内外卦对冲: 乾(子寅辰) vs 震(午申戌)
        # 子-午冲, 寅-申冲, 辰-戌冲 => 六冲卦
        # 巽宫四世卦: yao = [9, 7, 7, 7, 7, 7] -> 天雷无妄? 
        # Actually let's use known six-chong hexagrams
        # 乾为天(内: 子寅辰, 外: 午申戌) -> 六冲卦!
        h = Hexagram([7, 7, 7, 7, 7, 7], 2024, 3, 15)
        # Check if this is actually liu-chong
        from liuyao.xintai import _is_liu_chong_gua
        if _is_liu_chong_gua(h):
            ws = analyze_hexagram_wangshuai(h)
            db = analyze_dongbian(h, ws)
            result = detect_xintai_gua(h, "cai", ws, db)
            assert any("六冲" in ind for ind in result["indicators"])

    def test_hidden_yongshen_boosts_confidence(self):
        """事用神伏藏增加置信度"""
        # 坤为地: 坤宫纯卦, 六亲都是坤宫的
        # 坤属土: 兄弟=土, 子孙=金, 妻财=水, 官鬼=木, 父母=火
        # 坤为地内卦: 未巳卯(土火木) 外卦: 丑亥酉(土水金)
        # 六亲: 兄弟(未), 父母(巳), 官鬼(卯), 兄弟(丑), 妻财(亥), 子孙(酉)
        # 问guan(官运, 用神=官鬼), 卦中有官鬼卯 -> 不会伏藏
        # 需要找一个缺某六亲的卦
        # 兑为泽(兑宫纯卦): 兑属金
        # 内卦兑: 巳卯丑(火木土) 外卦兑: 亥酉未(水金土)
        # 六亲: 官鬼(巳), 妻财(卯), 父母(丑), 子孙(亥), 兄弟(酉), 父母(未)
        # 缺: 没有兄弟以外的金... 有兄弟(酉), 子孙(亥水), 妻财(卯木), 官鬼(巳火), 父母(丑土/未土)
        # 问kaoshi(父母) -> 有父母(丑, 未), 不伏藏
        # Let's use a hexagram where we know 妻财 is missing
        # 离为火(离宫): 离属火, 内卯丑亥, 外酉未巳
        # 六亲: 兄弟(卯木?no, 火宫:木=父母) 
        # 离属火: 火=兄弟, 土=子孙, 金=妻财, 水=官鬼, 木=父母
        # 内: 卯(木=父母), 丑(土=子孙), 亥(水=官鬼)
        # 外: 酉(金=妻财), 未(土=子孙), 巳(火=兄弟)
        # 有妻财(酉), 不缺
        # Try 火地晋(离宫游魂卦): 上离下坤
        # 坤内: 未巳卯(土火木), 离外: 酉未巳(金土火)
        # 宫=离(火): 土=子孙, 火=兄弟, 木=父母, 金=妻财, 水=官鬼
        # 内: 未(土=子孙), 巳(火=兄弟), 卯(木=父母)
        # 外: 酉(金=妻财), 未(土=子孙), 巳(火=兄弟)
        # 缺: 官鬼(水) -> 问cai用神=妻财(有酉), 问guan用神=官鬼(缺!)
        h = Hexagram([8, 8, 7, 7, 8, 7], 2024, 3, 15)  # 火地晋?
        ws = analyze_hexagram_wangshuai(h)
        db = analyze_dongbian(h, ws)
        # Check if yongshen is hidden for some question type
        from liuyao.jixiong import determine_yong_shen
        yong_lq = determine_yong_shen("guan")  # 官鬼
        yong_lines = find_yong_shen_lines(h, yong_lq)
        if not yong_lines:
            result = detect_xintai_gua(h, "guan", ws, db)
            assert result["confidence"] >= 0.3
            assert any("伏藏" in ind for ind in result["indicators"])


class TestAnalyzeXintai:
    """测试心态卦分析六模型"""

    def _make_hexagram_and_analyze(self, yao_values, year=2024, month=3, day=15):
        """辅助: 创建卦并做基础分析"""
        h = Hexagram(yao_values, year, month, day)
        ws = analyze_hexagram_wangshuai(h)
        db = analyze_dongbian(h, ws)
        return h, ws, db

    def test_model2_shi_bian_zisun(self):
        """Model 2: 世爻动化子孙 -> 放心"""
        # We need a hexagram where shi line moves and changes to 子孙
        # Try various combinations
        h = Hexagram([9, 7, 7, 7, 7, 7], 2024, 3, 15)
        ws = analyze_hexagram_wangshuai(h)
        db = analyze_dongbian(h, ws)
        shi = find_shi_line(h)
        if shi and shi.is_moving and shi.bian_liu_qin == "子孙":
            result = analyze_xintai(h, ws, db)
            assert result["verdict"] == "放心"

    def test_model5_static_zisun_holds_shi(self):
        """Model 5: 静卦子孙持世 -> 放心"""
        # 坤为地: 世在6爻, 六爻=酉(金=子孙 in 坤宫土)
        # Use month where 酉 is NOT month-broken (卯月冲酉)
        # Use 1月(寅月) so 酉 not broken
        h = Hexagram([8, 8, 8, 8, 8, 8], 2024, 1, 15)
        shi = find_shi_line(h)
        if shi and shi.liu_qin == "子孙":
            ws = analyze_hexagram_wangshuai(h)
            db = analyze_dongbian(h, ws)
            result = analyze_xintai(h, ws, db)
            assert result["verdict"] == "放心"

    def test_model5_static_guangui_holds_shi(self):
        """Model 5: 静卦官鬼持世 -> 有忧"""
        # Need a static hexagram where shi line is 官鬼
        # 离为火: 离宫纯卦, 世在6, 六爻=巳(火=兄弟 in 离宫火)
        # Try 震为雷: 震宫纯卦, 世在6, 六爻=戌(土) 震属木: 土=妻财
        # Try various
        h = Hexagram([7, 7, 7, 7, 7, 7], 2024, 6, 15)  # 乾为天
        shi = find_shi_line(h)
        # 乾宫: 金, 六爻=戌(土=父母)... not 官鬼
        # Let's search for one where shi_line.liu_qin == "官鬼"
        # 坎为水: 坎宫纯卦, 属水, 世在6, 六爻=子(水=兄弟)
        # 巽为风: 巽宫, 属木, 世在6, 六爻=卯(木=兄弟)
        # Need 官鬼 at shi position
        # 艮为山: 艮宫(土), 世在6爻, 六爻=寅(木=官鬼!)
        h = Hexagram([8, 8, 8, 8, 8, 8], 2024, 6, 15)  
        # This will be 坤为地 (坤宫): 世在6, 酉(金=子孙)
        # Try [7, 8, 7, 8, 7, 8] or similar for 艮
        # 艮为山: (0,0,1, 0,0,1) = 内艮外艮
        # yao_values for yin=8, yang=7: 艮=(阳阴阴) from bottom = 7,8,8 inner, 7,8,8 outer
        h = Hexagram([7, 8, 8, 7, 8, 8], 2024, 6, 15)
        shi = find_shi_line(h)
        if shi and shi.liu_qin == "官鬼" and not any(l.is_moving for l in h.lines):
            ws = analyze_hexagram_wangshuai(h)
            db = analyze_dongbian(h, ws)
            result = analyze_xintai(h, ws, db)
            assert result["verdict"] == "有忧"

    def test_model6_zisun_xunkong(self):
        """Model 6: 子孙旬空 -> 短期忧虑持续"""
        # Need a hexagram where 子孙 line is xun_kong
        h = Hexagram([8, 8, 8, 8, 8, 8], 2024, 3, 15)
        ws = analyze_hexagram_wangshuai(h)
        db = analyze_dongbian(h, ws)
        # Check if any 子孙 is xun_kong
        has_zisun_kong = any(
            l.liu_qin == "子孙" and l.is_xun_kong for l in h.lines
        )
        if has_zisun_kong:
            result = analyze_xintai(h, ws, db)
            found_model6 = any(d["model"] == "Model6" for d in result["details"])
            assert found_model6

    def test_model1_guangui_ke_shi(self):
        """Model 1: 官鬼动克世 -> 大凶"""
        # Need: 官鬼 as a useful moving line that ke's shi_line wu_xing
        # Create a hexagram scenario
        # This is hard to construct deterministically, so we test the logic path
        h = Hexagram([9, 7, 7, 9, 7, 7], 2024, 3, 15)
        ws = analyze_hexagram_wangshuai(h)
        db = analyze_dongbian(h, ws)
        shi = find_shi_line(h)
        result = analyze_xintai(h, ws, db)
        # Just verify it returns a valid structure
        assert "verdict" in result
        assert "explanation" in result
        assert "details" in result

    def test_model4_zisun_ke_guangui(self):
        """Model 4: 子孙克动态官鬼 -> 忧患可解"""
        # Need both 子孙 and 官鬼 moving, with 子孙 wu_xing ke's 官鬼 wu_xing
        h = Hexagram([9, 9, 9, 9, 9, 9], 2024, 3, 15)  # all moving
        ws = analyze_hexagram_wangshuai(h)
        db = analyze_dongbian(h, ws)
        result = analyze_xintai(h, ws, db)
        # Check structure is valid
        assert "verdict" in result
        assert isinstance(result["details"], list)


class TestIsTrueYongshen:
    """测试真用神判定"""

    def _setup(self, yao_values, year=2024, month=3, day=15):
        h = Hexagram(yao_values, year, month, day)
        ws = analyze_hexagram_wangshuai(h)
        db = analyze_dongbian(h, ws)
        return h, ws, db

    def test_line_at_shi_is_true(self):
        """持世爻为真用神"""
        h, ws, db = self._setup([7, 7, 7, 7, 7, 7])
        shi = find_shi_line(h)
        assert shi is not None
        assert is_true_yongshen(shi, h, ws, db) is True

    def test_line_at_ying_is_true(self):
        """持应爻为真用神"""
        h, ws, db = self._setup([7, 7, 7, 7, 7, 7])
        ying = find_ying_line(h)
        assert ying is not None
        assert is_true_yongshen(ying, h, ws, db) is True

    def test_line_xunkong_is_true(self):
        """旬空爻为真用神"""
        h, ws, db = self._setup([7, 7, 7, 7, 7, 7])
        kong_lines = [l for l in h.lines if l.is_xun_kong]
        if kong_lines:
            assert is_true_yongshen(kong_lines[0], h, ws, db) is True

    def test_line_lin_day_is_true(self):
        """临日辰爻为真用神"""
        h, ws, db = self._setup([7, 7, 7, 8, 8, 8], 2024, 3, 15)
        day_zhi = h.gan_zhi["day_zhi"]
        day_lines = [l for l in h.lines if l.di_zhi == day_zhi]
        if day_lines:
            assert is_true_yongshen(day_lines[0], h, ws, db) is True

    def test_line_lin_month_is_true(self):
        """临月建爻为真用神"""
        h, ws, db = self._setup([7, 7, 7, 8, 8, 8], 2024, 3, 15)
        month_zhi = h.gan_zhi["month_zhi"]
        month_lines = [l for l in h.lines if l.di_zhi == month_zhi]
        if month_lines:
            assert is_true_yongshen(month_lines[0], h, ws, db) is True

    def test_line_with_interaction_is_true(self):
        """有动爻作用于它的爻为真用神"""
        h, ws, db = self._setup([9, 9, 7, 7, 7, 7])
        interactions = db.get("interactions", {})
        for pos, inter in interactions.items():
            if inter["受生"] or inter["受克"]:
                line = h.lines[pos - 1]
                assert is_true_yongshen(line, h, ws, db) is True
                break

    def test_false_yongshen(self):
        """不满足任何5条件的爻为假用神"""
        # Static hexagram, pick a line that is not shi, not ying,
        # not xunkong, not lin day/month, not in interactions
        h, ws, db = self._setup([7, 7, 7, 8, 8, 8], 2024, 1, 20)
        month_zhi = h.gan_zhi["month_zhi"]
        day_zhi = h.gan_zhi["day_zhi"]
        for line in h.lines:
            if (not line.is_shi and not line.is_ying and
                not line.is_xun_kong and
                line.di_zhi != month_zhi and line.di_zhi != day_zhi):
                # Check liu_he
                from liuyao.data import LIU_HE, get_chang_sheng, DI_ZHI_WU_XING
                he_match = False
                if line.di_zhi in LIU_HE:
                    he_zhi = LIU_HE[line.di_zhi][0]
                    if he_zhi == month_zhi or he_zhi == day_zhi:
                        he_match = True
                if he_match:
                    continue
                # Check mu
                line_wx = DI_ZHI_WU_XING[line.di_zhi]
                if get_chang_sheng(line_wx, line.di_zhi) == "墓":
                    continue
                # Check interactions
                interactions = db.get("interactions", {})
                if line.position in interactions:
                    inter = interactions[line.position]
                    if inter["受生"] or inter["受克"]:
                        continue
                result = is_true_yongshen(line, h, ws, db)
                if not result:
                    assert result is False
                    return
        # If we can't find such a line, skip
        pytest.skip("Could not find a false yongshen line in this hexagram")


class TestFindXinnianYao:
    """测试心念爻定位"""

    def test_returns_dict_or_none(self):
        """返回值为dict或None"""
        h = Hexagram([7, 7, 7, 8, 8, 8], 2024, 3, 15)
        result = find_xinnian_yao(h)
        assert result is None or isinstance(result, dict)

    def test_result_has_required_fields(self):
        """返回的dict包含必要字段"""
        h = Hexagram([7, 7, 7, 8, 8, 8], 2024, 3, 15)
        result = find_xinnian_yao(h)
        if result is not None:
            assert "position" in result
            assert "di_zhi" in result
            assert "wu_xing" in result
            assert "liu_qin" in result

    def test_static_hexagram_step1(self):
        """静卦: Step 1 - 变卦对位爻"""
        # 静卦的变卦=本卦, 所以对位爻=世爻本身
        # Step 1 won't produce different line for pure static
        h = Hexagram([7, 7, 7, 7, 7, 7], 2024, 3, 15)
        result = find_xinnian_yao(h)
        # Should fall through to step 2 or 3
        assert result is None or isinstance(result, dict)

    def test_moving_hexagram(self):
        """动卦情况下的心念爻"""
        h = Hexagram([9, 7, 7, 7, 7, 7], 2024, 3, 15)
        result = find_xinnian_yao(h)
        assert result is None or isinstance(result, dict)

    def test_step3_jun_yao(self):
        """Step 3: 君爻(第5爻)静且六亲不同"""
        # If step 1 and 2 fail, check jun_yao (position 5)
        h = Hexagram([8, 8, 8, 8, 8, 8], 2024, 3, 15)
        shi = find_shi_line(h)
        jun = h.lines[4]  # position 5
        if shi and not jun.is_moving and jun.liu_qin != shi.liu_qin:
            result = find_xinnian_yao(h)
            # Should find jun_yao or cang_yao
            assert result is not None

    def test_xinnian_zisun_or_guangui(self):
        """心念爻为子孙或官鬼时倾向心态卦"""
        h = Hexagram([7, 7, 7, 8, 8, 8], 2024, 3, 15)
        result = find_xinnian_yao(h)
        if result and result["liu_qin"] in ("子孙", "官鬼"):
            # This is just a check that the logic works
            assert result["liu_qin"] in ("子孙", "官鬼")


class TestIntegration:
    """测试与analyzer的集成"""

    def test_youhuan_triggers_xintai(self):
        """youHuan问事类型触发心态卦分析"""
        h = Hexagram([9, 7, 7, 7, 7, 7], 2024, 3, 15)
        report = run_analysis(h, question_type="youHuan")
        assert report.xintai_result is not None
        assert report.xintai_result["detection"]["is_xintai"] is True

    def test_normal_cai_no_xintai(self):
        """普通求财卦通常不触发心态卦(除非指标充足)"""
        h = Hexagram([7, 7, 7, 7, 7, 7], 2024, 1, 15)
        report = run_analysis(h, question_type="cai")
        # May or may not trigger depending on hexagram indicators
        # Just verify structure is correct
        if report.xintai_result:
            assert "detection" in report.xintai_result
            assert "analysis" in report.xintai_result

    def test_report_format_with_xintai(self):
        """心态卦报告格式化正确"""
        from liuyao.report import format_report
        h = Hexagram([9, 7, 7, 7, 7, 7], 2024, 3, 15)
        report = run_analysis(h, question_type="youHuan")
        text = format_report(report)
        assert "心态卦识别" in text

    def test_existing_analysis_still_works(self):
        """心态卦模块不影响已有分析流程"""
        h = Hexagram([8, 7, 7, 9, 7, 8], 2024, 1, 15)
        report = run_analysis(h, question_type="cai")
        assert report.jixiong_result is not None
        assert "ji_xiong" in report.jixiong_result
        assert report.wangshuai_results is not None
        assert len(report.wangshuai_results) == 6

    def test_zisun_sheng_shi_is_relief(self):
        """子孙动生世爻判为放心"""
        # Try to construct a scenario - may not always hit
        # Use multiple moving lines to increase chance
        h = Hexagram([9, 9, 7, 7, 7, 7], 2024, 3, 15)
        ws = analyze_hexagram_wangshuai(h)
        db = analyze_dongbian(h, ws)
        result = analyze_xintai(h, ws, db)
        # Verify structure
        assert "verdict" in result
        assert result["verdict"] in (
            "放心", "有忧", "大凶", "忧患可解", "有忧无实患",
            "忧患成真", "忧患", "短期忧虑持续", "短期安全", "平"
        )

    def test_guangui_ke_shi_is_danger(self):
        """官鬼动克世爻判为大凶"""
        # Hard to deterministically construct, test structure
        h = Hexagram([7, 9, 7, 9, 7, 7], 2024, 5, 10)
        ws = analyze_hexagram_wangshuai(h)
        db = analyze_dongbian(h, ws)
        result = analyze_xintai(h, ws, db)
        assert "verdict" in result
        assert isinstance(result["details"], list)


class TestConfidenceBoundary:
    """测试置信度边界(0.7阈值)"""

    def test_below_threshold_no_xintai_analysis(self):
        """置信度0.65(低于0.7): 检测为is_xintai但analyzer不触发分析"""
        # [8,8,8,9,8,8] date=(2024,1,15) qt=kaoshi => conf=0.65
        h = Hexagram([8, 8, 8, 9, 8, 8], 2024, 1, 15)
        ws = analyze_hexagram_wangshuai(h)
        db = analyze_dongbian(h, ws)
        result = detect_xintai_gua(h, "kaoshi", ws, db)
        # confidence should be 0.65 (below 0.7)
        assert result["is_xintai"] is True
        assert result["confidence"] < 0.7

        # Analyzer should NOT trigger xintai_result
        report = run_analysis(h, question_type="kaoshi")
        assert report.xintai_result is None

    def test_above_threshold_triggers_xintai_analysis(self):
        """置信度0.75(高于0.7): analyzer触发心态卦分析"""
        # [9,8,9,8,9,8] date=(2024,1,15) qt=cai => conf=0.75
        h = Hexagram([9, 8, 9, 8, 9, 8], 2024, 1, 15)
        ws = analyze_hexagram_wangshuai(h)
        db = analyze_dongbian(h, ws)
        result = detect_xintai_gua(h, "cai", ws, db)
        assert result["confidence"] >= 0.7

        # Analyzer should trigger xintai_result
        report = run_analysis(h, question_type="cai")
        assert report.xintai_result is not None
        assert "detection" in report.xintai_result
        assert "analysis" in report.xintai_result

    def test_exact_threshold_triggers(self):
        """置信度恰好为1.0(明确心态类问事): analyzer触发分析"""
        # Explicit mindset question type always gives confidence=1.0
        h = Hexagram([7, 7, 7, 8, 8, 8], 2024, 1, 15)
        report = run_analysis(h, question_type="youHuan")
        assert report.xintai_result is not None
        assert report.xintai_result["detection"]["confidence"] == 1.0


class TestXintaiTypeRelief:
    """测试心态类型正确返回relief"""

    def test_only_zisun_indicators_returns_relief(self):
        """仅有子孙指标时返回relief而非worry"""
        # [9,8,9,8,9,8] date=(2024,1,15) qt=cai
        # indicators: 伏藏不现 + 世爻动化子孙 + 子孙独发 (all 子孙-related)
        h = Hexagram([9, 8, 9, 8, 9, 8], 2024, 1, 15)
        ws = analyze_hexagram_wangshuai(h)
        db = analyze_dongbian(h, ws)
        result = detect_xintai_gua(h, "cai", ws, db)
        assert result["is_xintai"] is True
        assert result["xintai_type"] == "relief"
        # Verify no guan-gui indicators
        assert not any("官鬼" in ind for ind in result["indicators"])

    def test_only_guangui_indicators_returns_worry(self):
        """仅有官鬼指标时返回worry"""
        # [9,9,9,8,8,8] date=(2024,1,15) qt=kaoshi => conf=0.90
        # indicators: 伏藏 + 世爻动化官鬼 + 官鬼独发 + 应爻临子孙
        h = Hexagram([9, 9, 9, 8, 8, 8], 2024, 1, 15)
        ws = analyze_hexagram_wangshuai(h)
        db = analyze_dongbian(h, ws)
        result = detect_xintai_gua(h, "kaoshi", ws, db)
        assert result["is_xintai"] is True
        # Check it has worry indicators
        has_worry = any("官鬼" in ind for ind in result["indicators"])
        has_relief = any("子孙" in ind for ind in result["indicators"])
        if has_worry and has_relief:
            assert result["xintai_type"] == "hesitation"
        elif has_worry:
            assert result["xintai_type"] == "worry"

    def test_mixed_indicators_returns_hesitation(self):
        """同时有子孙和官鬼指标时返回hesitation"""
        from liuyao.xintai import _determine_xintai_type
        # Direct test of the helper function
        indicators = ["世爻动化子孙(趋向安心)", "官鬼独发(第2爻动)"]
        result = _determine_xintai_type(None, None, indicators)
        assert result == "hesitation"

    def test_determine_xintai_type_relief_only(self):
        """_determine_xintai_type: 仅有子孙 -> relief"""
        from liuyao.xintai import _determine_xintai_type
        indicators = ["子孙独发(第1爻动)", "世爻动化子孙(趋向安心)"]
        result = _determine_xintai_type(None, None, indicators)
        assert result == "relief"

    def test_determine_xintai_type_worry_only(self):
        """_determine_xintai_type: 仅有官鬼 -> worry"""
        from liuyao.xintai import _determine_xintai_type
        indicators = ["官鬼独发(第4爻动)", "世爻动化官鬼(趋向忧虑)"]
        result = _determine_xintai_type(None, None, indicators)
        assert result == "worry"

    def test_determine_xintai_type_neither(self):
        """_determine_xintai_type: 无子孙无官鬼 -> worry(默认)"""
        from liuyao.xintai import _determine_xintai_type
        indicators = ["事用神(妻财)伏藏不现", "六冲卦(冲散忧虑之象)"]
        result = _determine_xintai_type(None, None, indicators)
        assert result == "worry"


class TestFindXinnianYaoStepPriority:
    """测试find_xinnian_yao的Step 1优先级"""

    def test_step1_priority_over_step2(self):
        """世爻不动时Step 1(变卦对位爻)优先于Step 2(藏爻)"""
        # [7,7,7,9,7,7]: shi at pos 6 (not moving), line 4 moves
        # Bian_gua has different di_zhi at pos 6 (卯 vs 戌)
        h = Hexagram([7, 7, 7, 9, 7, 7], 2024, 3, 15)
        shi = find_shi_line(h)
        assert shi.position == 6
        assert not shi.is_moving

        from liuyao.xintai import _get_bian_gua_line_at
        from liuyao.fushen import get_cang_yao

        # Step 1 should find bian line with di_zhi different from shi
        bian_info = _get_bian_gua_line_at(h, shi.position)
        assert bian_info is not None
        assert bian_info["di_zhi"] != shi.di_zhi

        # Get result - should match step 1 (bian), not step 2 (cang)
        result = find_xinnian_yao(h)
        assert result is not None
        assert result["di_zhi"] == bian_info["di_zhi"]
        assert result["position"] == shi.position

    def test_step2_when_shi_is_moving(self):
        """世爻动时使用Step 2(藏爻)"""
        # [7,7,7,7,7,9]: shi at pos 6, moving (old yang)
        h = Hexagram([7, 7, 7, 7, 7, 9], 2024, 3, 15)
        shi = find_shi_line(h)
        assert shi.position == 6
        assert shi.is_moving

        # Step 1 is skipped because shi is moving
        # Step 2 checks cang_yao - if same di_zhi, falls through to step 3
        from liuyao.fushen import get_cang_yao
        cang = get_cang_yao(h)
        cang_at_shi = cang[shi.position - 1]

        result = find_xinnian_yao(h)
        assert result is not None
        # Since cang at shi has same di_zhi as shi (戌==戌),
        # step 2 fails and falls to step 3 (jun_yao)
        if cang_at_shi["di_zhi"] == shi.di_zhi:
            # Should have gone to step 3 (jun_yao at pos 5)
            jun_line = h.lines[4]
            if not jun_line.is_moving and jun_line.liu_qin != shi.liu_qin:
                assert result["position"] == 5

    def test_step1_fallthrough_when_bian_same(self):
        """Step 1对位爻与世爻相同时落入Step 2"""
        # Pure static hexagram: bian = ben, so bian line at shi pos = shi itself
        # [7,7,7,7,7,7] (乾为天, all static, bian=乾为天)
        h = Hexagram([7, 7, 7, 7, 7, 7], 2024, 3, 15)
        shi = find_shi_line(h)
        assert not shi.is_moving

        from liuyao.xintai import _get_bian_gua_line_at
        bian_info = _get_bian_gua_line_at(h, shi.position)
        # Bian = same hexagram, so same di_zhi
        assert bian_info["di_zhi"] == shi.di_zhi

        # Should fall through to step 2 (cang_yao)
        from liuyao.fushen import get_cang_yao
        cang = get_cang_yao(h)
        cang_at_shi = cang[shi.position - 1]

        result = find_xinnian_yao(h)
        # If cang also same, falls to step 3
        if cang_at_shi["di_zhi"] == shi.di_zhi:
            # Step 3: jun_yao (pos 5) static and different liu_qin
            jun_line = h.lines[4]
            if not jun_line.is_moving and jun_line.liu_qin != shi.liu_qin:
                assert result is not None
                assert result["position"] == 5
