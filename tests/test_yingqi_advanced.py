"""
应期推断高级测试 - Advanced Ying-Qi Tests

测试增强版应期推断系统的各项功能。
"""

import pytest
from liuyao.hexagram import Hexagram
from liuyao.yingqi import (
    classify_event_duration, identify_yuan_shen,
    estimate_andong_yingqi, estimate_yueling_yingqi,
    estimate_riling_yingqi, apply_standard_formulas,
    detect_timing_modifiers, rank_timing_candidates,
    estimate_yingqi, analyze_yingqi,
    estimate_yuan_shen_yingqi,
)
from liuyao.wangshuai import analyze_hexagram_wangshuai
from liuyao.dongbian import analyze_dongbian


# ============================================================================
# Test classify_event_duration
# ============================================================================

class TestClassifyEventDuration:
    """测试事件持续期分类"""

    def test_short_bing(self):
        assert classify_event_duration("bing") == "short"

    def test_medium_cai(self):
        assert classify_event_duration("cai") == "medium"

    def test_medium_guan(self):
        assert classify_event_duration("guan") == "medium"

    def test_medium_hun_male(self):
        assert classify_event_duration("hun_male") == "medium"

    def test_medium_hun_female(self):
        assert classify_event_duration("hun_female") == "medium"

    def test_medium_kaoshi(self):
        assert classify_event_duration("kaoshi") == "medium"

    def test_medium_xingRen(self):
        assert classify_event_duration("xingRen") == "medium"

    def test_medium_youHuan(self):
        assert classify_event_duration("youHuan") == "medium"

    def test_medium_other(self):
        assert classify_event_duration("other") == "medium"

    def test_medium_zinv(self):
        assert classify_event_duration("zinv") == "medium"

    def test_unknown_defaults_medium(self):
        assert classify_event_duration("unknown") == "medium"


# ============================================================================
# Test identify_yuan_shen
# ============================================================================

class TestIdentifyYuanShen:
    """测试元神识别"""

    def test_qicai_yuan_shen(self):
        """妻财的元神是子孙"""
        assert identify_yuan_shen("妻财") == "子孙"

    def test_guangui_yuan_shen(self):
        """官鬼的元神是妻财"""
        assert identify_yuan_shen("官鬼") == "妻财"

    def test_fumu_yuan_shen(self):
        """父母的元神是官鬼"""
        assert identify_yuan_shen("父母") == "官鬼"

    def test_zisun_yuan_shen(self):
        """子孙的元神是兄弟"""
        assert identify_yuan_shen("子孙") == "兄弟"

    def test_xiongdi_yuan_shen(self):
        """兄弟的元神是父母"""
        assert identify_yuan_shen("兄弟") == "父母"

    def test_unknown_returns_empty(self):
        assert identify_yuan_shen("unknown") == ""


# ============================================================================
# Test estimate_andong_yingqi
# ============================================================================

class TestEstimateAndongYingqi:
    """测试暗动应期"""

    def test_chong_kong_immediate(self):
        """旬空逢日冲(冲空) -> 即时生效"""
        # Hexagram with xunkong line being day-clashed
        h = Hexagram([8, 8, 7, 7, 8, 8], 2024, 1, 15)
        # Find a line that is xunkong
        an_dong_info = {
            "position": 1,
            "di_zhi": "子",
            "reason": "旬空逢日冲(冲空为暗动)",
            "type": "暗动",
        }
        line = h.lines[0]
        candidates = estimate_andong_yingqi(line, an_dong_info, h)
        # Should have immediate timing
        assert len(candidates) > 0
        assert any("即时" in c["timing"] for c in candidates)
        assert candidates[0]["formula"] == "冲空即时生效"
        assert candidates[0]["confidence"] == 90

    def test_normal_andong_fengzhi(self):
        """正常暗动 -> 逢值逢合"""
        h = Hexagram([8, 8, 7, 7, 8, 8], 2024, 1, 15)
        an_dong_info = {
            "position": 1,
            "di_zhi": h.lines[0].di_zhi,
            "reason": "月旺逢日冲(冲旺为暗动)",
            "type": "暗动",
        }
        line = h.lines[0]
        candidates = estimate_andong_yingqi(line, an_dong_info, h)
        assert len(candidates) >= 2
        assert any("逢值" in c["formula"] for c in candidates)

    def test_andong_shunshi(self):
        """暗动顺时而应"""
        h = Hexagram([8, 8, 7, 7, 8, 8], 2024, 1, 15)
        an_dong_info = {
            "position": 1,
            "di_zhi": h.lines[0].di_zhi,
            "reason": "月旺逢日冲(冲旺为暗动)",
            "type": "暗动",
        }
        line = h.lines[0]
        candidates = estimate_andong_yingqi(line, an_dong_info, h)
        assert any("顺时而应" in c["formula"] for c in candidates)


# ============================================================================
# Test estimate_yueling_yingqi
# ============================================================================

class TestEstimateYuelingYingqi:
    """测试月令应期"""

    def test_lin_yuejian(self):
        """临月建 -> 本月"""
        # Need a hexagram where a line matches month_zhi
        h = Hexagram([8, 8, 7, 7, 8, 8], 2024, 1, 15)
        month_zhi = h.gan_zhi["month_zhi"]
        # Find a line that matches month_zhi
        ws_results = analyze_hexagram_wangshuai(h)
        for i, line in enumerate(h.lines):
            if line.di_zhi == month_zhi:
                candidates = estimate_yueling_yingqi(line, h, ws_results[i])
                assert any("本月" in c["timing"] for c in candidates)
                assert any(c["formula"] == "临月建" for c in candidates)
                break

    def test_yue_he_within_3_months(self):
        """月合 -> 三月内"""
        h = Hexagram([8, 8, 7, 7, 8, 8], 2024, 1, 15)
        month_zhi = h.gan_zhi["month_zhi"]
        ws_results = analyze_hexagram_wangshuai(h)
        from liuyao.data import LIU_HE
        # Find a line whose LIU_HE partner is the month_zhi
        for i, line in enumerate(h.lines):
            if line.di_zhi in LIU_HE:
                he_partner, _ = LIU_HE[line.di_zhi]
                if he_partner == month_zhi:
                    candidates = estimate_yueling_yingqi(line, h, ws_results[i])
                    assert any("三月内" in c["timing"] for c in candidates)
                    break


# ============================================================================
# Test estimate_riling_yingqi
# ============================================================================

class TestEstimateRilingYingqi:
    """测试日令应期"""

    def test_short_event_lin_riling(self):
        """短事临日令 -> 今日"""
        h = Hexagram([8, 8, 7, 7, 8, 8], 2024, 1, 15)
        day_zhi = h.gan_zhi["day_zhi"]
        ws_results = analyze_hexagram_wangshuai(h)
        # Find line matching day_zhi
        for i, line in enumerate(h.lines):
            if line.di_zhi == day_zhi:
                candidates = estimate_riling_yingqi(
                    line, h, ws_results[i], "short")
                assert any("今日" in c["timing"] for c in candidates)
                assert any(c["formula"] == "短事临日令" for c in candidates)
                break

    def test_medium_event_lin_yueling(self):
        """常事临月令 -> 本月"""
        h = Hexagram([8, 8, 7, 7, 8, 8], 2024, 1, 15)
        month_zhi = h.gan_zhi["month_zhi"]
        ws_results = analyze_hexagram_wangshuai(h)
        for i, line in enumerate(h.lines):
            if line.di_zhi == month_zhi:
                candidates = estimate_riling_yingqi(
                    line, h, ws_results[i], "medium")
                assert any("本月" in c["timing"] for c in candidates)
                break

    def test_short_event_no_match(self):
        """短事非临日令 -> 逢值日"""
        h = Hexagram([8, 8, 7, 7, 8, 8], 2024, 1, 15)
        day_zhi = h.gan_zhi["day_zhi"]
        ws_results = analyze_hexagram_wangshuai(h)
        from liuyao.data import LIU_CHONG
        for i, line in enumerate(h.lines):
            if line.di_zhi != day_zhi and line.di_zhi != LIU_CHONG.get(day_zhi):
                candidates = estimate_riling_yingqi(
                    line, h, ws_results[i], "short")
                assert len(candidates) > 0
                assert any("逢值" in c["formula"] for c in candidates)
                break



# ============================================================================
# Test apply_standard_formulas
# ============================================================================

class TestApplyStandardFormulas:
    """测试标准应期公式"""

    def test_formula1_wang_jing_feng_chong(self):
        """公式1: 旺静逢冲"""
        # Static hexagram with a prosperous line
        h = Hexagram([8, 8, 7, 7, 8, 8], 2024, 1, 15)
        ws_results = analyze_hexagram_wangshuai(h)
        dongbian = analyze_dongbian(h, ws_results)
        # Find a prosperous static line
        for i, line in enumerate(h.lines):
            if not line.is_moving and ws_results[i]["overall"] == "旺":
                candidates = apply_standard_formulas(
                    line, h, ws_results[i], None, dongbian,
                    "medium", {"ji_xiong": "吉"}
                )
                # Should have formula_id 1
                f1 = [c for c in candidates if c["formula_id"] == 1]
                if f1:
                    assert "旺静逢冲" in f1[0]["formula_name"]
                break

    def test_formula2_moving_fenghe(self):
        """公式2: 动爻逢合"""
        # Hexagram with one moving line
        h = Hexagram([9, 7, 8, 7, 8, 7], 2024, 6, 15)
        ws_results = analyze_hexagram_wangshuai(h)
        dongbian = analyze_dongbian(h, ws_results)
        moving_analyses = dongbian.get("moving_analyses", {})
        # Find the moving line
        for i, line in enumerate(h.lines):
            if line.is_moving:
                ma = moving_analyses.get(line.position)
                candidates = apply_standard_formulas(
                    line, h, ws_results[i], ma, dongbian,
                    "medium", {"ji_xiong": "吉"}
                )
                # Should have formula_id 2 (moving line)
                f2 = [c for c in candidates if c["formula_id"] == 2]
                assert len(f2) > 0
                break

    def test_formula5_xunkong(self):
        """公式5: 旬空 -> 填空/冲空/出空"""
        h = Hexagram([8, 8, 7, 7, 8, 8], 2024, 1, 15)
        ws_results = analyze_hexagram_wangshuai(h)
        dongbian = analyze_dongbian(h, ws_results)
        # Find a xunkong line
        for i, line in enumerate(h.lines):
            if line.is_xun_kong:
                candidates = apply_standard_formulas(
                    line, h, ws_results[i], None, dongbian,
                    "medium", {"ji_xiong": "平"}
                )
                # Should have formula_id 5
                f5 = [c for c in candidates if c["formula_id"] == 5]
                assert len(f5) >= 2  # at least fill and clash
                names = [c["formula_name"] for c in f5]
                assert any("填空" in n for n in names)
                assert any("冲空" in n for n in names)
                break

    def test_formula1_shuai_jing_feng_zhi(self):
        """公式1: 衰静逢值"""
        h = Hexagram([8, 8, 7, 7, 8, 8], 2024, 1, 15)
        ws_results = analyze_hexagram_wangshuai(h)
        dongbian = analyze_dongbian(h, ws_results)
        # Find a weak static non-xunkong non-yuepo line
        for i, line in enumerate(h.lines):
            if (not line.is_moving and
                ws_results[i]["overall"] != "旺" and
                not line.is_xun_kong and
                "月破" not in ws_results[i].get("month_shuai", [])):
                candidates = apply_standard_formulas(
                    line, h, ws_results[i], None, dongbian,
                    "medium", {"ji_xiong": "吉"}
                )
                f1 = [c for c in candidates if c["formula_id"] == 1]
                if f1:
                    assert "衰静逢值" in f1[0]["formula_name"]
                break

    def test_formula9_hua_jin_shen(self):
        """公式9: 化进神 -> 逢值/逢合/逢进"""
        # Need a hexagram with jin_shen transformation
        # 寅化卯: need a line at 寅 that changes to 卯
        # Let us try different configurations
        h = Hexagram([9, 7, 8, 7, 8, 7], 2024, 6, 15)
        ws_results = analyze_hexagram_wangshuai(h)
        dongbian = analyze_dongbian(h, ws_results)
        moving_analyses = dongbian.get("moving_analyses", {})
        for pos, ma in moving_analyses.items():
            if "化进神" in ma.get("趋旺", []):
                line = h.lines[pos - 1]
                candidates = apply_standard_formulas(
                    line, h, ws_results[pos-1], ma, dongbian,
                    "medium", {"ji_xiong": "吉"}
                )
                f9 = [c for c in candidates if c["formula_id"] == 9]
                assert len(f9) > 0
                break


# ============================================================================
# Test detect_timing_modifiers
# ============================================================================

class TestDetectTimingModifiers:
    """测试应期修正信号"""

    def test_andong_acceleration(self):
        """暗动产生加速信号"""
        h = Hexagram([8, 8, 7, 7, 8, 8], 2024, 1, 15)
        ws_results = analyze_hexagram_wangshuai(h)
        dongbian = analyze_dongbian(h, ws_results)
        an_dong = dongbian.get("an_dong", [])
        # If there are andong entries, check modifiers
        modifiers = detect_timing_modifiers(h, dongbian, None)
        if an_dong:
            andong_typed = [a for a in an_dong if a.get("type") == "暗动"]
            if andong_typed:
                assert len(modifiers["acceleration"]) > 0
                assert any("暗动" in a for a in modifiers["acceleration"])

    def test_san_he_deceleration(self):
        """三合局产生减速信号"""
        # Create hexagram with all lines moving (likely to form san-he)
        h = Hexagram([9, 9, 9, 9, 9, 9], 2024, 1, 15)
        ws_results = analyze_hexagram_wangshuai(h)
        dongbian = analyze_dongbian(h, ws_results)
        san_he = dongbian.get("san_he_ju", [])
        modifiers = detect_timing_modifiers(h, dongbian, None)
        if san_he:
            assert len(modifiers["deceleration"]) > 0
            assert any("三合局" in d for d in modifiers["deceleration"])

    def test_liuchong_bian_acceleration(self):
        """卦变六冲加速"""
        from liuyao.liuchong_liuhe import analyze_liuchong_liuhe
        h = Hexagram([9, 9, 9, 9, 9, 9], 2024, 1, 15)
        ws_results = analyze_hexagram_wangshuai(h)
        dongbian = analyze_dongbian(h, ws_results)
        lcr = analyze_liuchong_liuhe(h, dongbian, ws_results)
        modifiers = detect_timing_modifiers(h, dongbian, lcr)
        liu_chong = lcr.get("liu_chong", {})
        if liu_chong.get("is_liu_chong"):
            chong_type = liu_chong.get("type", "")
            if chong_type in ("bian", "both"):
                assert any("卦变六冲" in a for a in modifiers["acceleration"])

    def test_empty_modifiers(self):
        """无修正信号时返回空列表"""
        h = Hexagram([8, 8, 7, 7, 8, 8], 2024, 6, 15)
        dongbian_mock = {
            "moving_analyses": {},
            "an_dong": [],
            "san_he_ju": [],
        }
        modifiers = detect_timing_modifiers(h, dongbian_mock, None)
        assert "acceleration" in modifiers
        assert "deceleration" in modifiers


# ============================================================================
# Test rank_timing_candidates
# ============================================================================

class TestRankTimingCandidates:
    """测试应期候选排序"""

    def test_duplicate_higher_score(self):
        """重复候选得分更高(应众不应寡)"""
        candidates = [
            {"timing": "午日/月(逢冲)", "confidence": 70, "formula_name": "旺静逢冲"},
            {"timing": "午日/月(逢冲)", "confidence": 65, "formula_name": "暗动逢值"},
            {"timing": "子日/月(逢值)", "confidence": 60, "formula_name": "衰静逢值"},
        ]
        ranked = rank_timing_candidates(candidates)
        assert len(ranked) == 2
        # 午 appears twice, should have higher score
        wu_entry = [r for r in ranked if "午" in r["timing"]]
        zi_entry = [r for r in ranked if "子" in r["timing"]]
        assert wu_entry[0]["score"] > zi_entry[0]["score"]

    def test_adjacent_bonus(self):
        """相邻地支得分奖励(应邻不应单)"""
        candidates = [
            {"timing": "巳日/月(逢值)", "confidence": 60, "formula_name": "f1"},
            {"timing": "午日/月(逢冲)", "confidence": 60, "formula_name": "f2"},
            {"timing": "子日/月(逢值)", "confidence": 60, "formula_name": "f3"},
        ]
        ranked = rank_timing_candidates(candidates)
        # 巳 and 午 are adjacent, should get bonus
        si_entry = [r for r in ranked if "巳" in r["timing"]]
        wu_entry = [r for r in ranked if "午" in r["timing"]]
        zi_entry = [r for r in ranked if "子" in r["timing"]]
        # Both 巳 and 午 should score higher than 子
        assert si_entry[0]["score"] > zi_entry[0]["score"]
        assert wu_entry[0]["score"] > zi_entry[0]["score"]

    def test_empty_candidates(self):
        """空候选列表"""
        assert rank_timing_candidates([]) == []

    def test_formulas_collected(self):
        """公式名称被收集"""
        candidates = [
            {"timing": "午日/月", "confidence": 70, "formula_name": "旺静逢冲"},
            {"timing": "午日/月", "confidence": 60, "formula_name": "动爻逢合"},
        ]
        ranked = rank_timing_candidates(candidates)
        assert "旺静逢冲" in ranked[0]["formulas"]
        assert "动爻逢合" in ranked[0]["formulas"]

    def test_score_ordering(self):
        """结果按得分降序排列"""
        candidates = [
            {"timing": "子日/月", "confidence": 30, "formula_name": "f1"},
            {"timing": "午日/月", "confidence": 90, "formula_name": "f2"},
            {"timing": "寅日/月", "confidence": 60, "formula_name": "f3"},
        ]
        ranked = rank_timing_candidates(candidates)
        for i in range(len(ranked) - 1):
            assert ranked[i]["score"] >= ranked[i+1]["score"]


# ============================================================================
# Test Full Integration: analyze_yingqi backward compatibility
# ============================================================================

class TestAnalyzeYingqiIntegration:
    """测试analyze_yingqi集成和后向兼容"""

    def test_backward_compatible_keys(self):
        """确保后向兼容的key仍然存在"""
        h = Hexagram([9, 7, 8, 7, 8, 7], 2024, 6, 15)
        ws_results = analyze_hexagram_wangshuai(h)
        dongbian = analyze_dongbian(h, ws_results)
        # Find yong_shen lines (use first line for testing)
        yong_lines = [h.lines[0]]

        results = analyze_yingqi(h, yong_lines, ws_results, dongbian)
        assert len(results) > 0
        r = results[0]
        # Backward compatible keys
        assert "position" in r
        assert "di_zhi" in r
        assert "liu_qin" in r
        assert "candidates" in r
        # candidates should be list of strings
        assert isinstance(r["candidates"], list)
        if r["candidates"]:
            assert isinstance(r["candidates"][0], str)

    def test_enhanced_keys_present(self):
        """增强版key存在"""
        h = Hexagram([9, 7, 8, 7, 8, 7], 2024, 6, 15)
        ws_results = analyze_hexagram_wangshuai(h)
        dongbian = analyze_dongbian(h, ws_results)
        yong_lines = [h.lines[0]]

        results = analyze_yingqi(
            h, yong_lines, ws_results, dongbian,
            event_duration="medium",
            jixiong_result={"ji_xiong": "吉", "pattern": "test", "explanation": "test"},
            liuchong_liuhe_results=None
        )
        r = results[0]
        assert "event_duration" in r
        assert "ranked_candidates" in r
        assert "modifiers" in r
        assert "yuan_shen_timing" in r

    def test_ranked_candidates_structure(self):
        """ranked_candidates结构正确"""
        h = Hexagram([8, 8, 7, 7, 8, 8], 2024, 1, 15)
        ws_results = analyze_hexagram_wangshuai(h)
        dongbian = analyze_dongbian(h, ws_results)
        yong_lines = [l for l in h.lines if not l.is_moving][:1]
        if not yong_lines:
            yong_lines = [h.lines[0]]

        results = analyze_yingqi(
            h, yong_lines, ws_results, dongbian,
            event_duration="short",
            jixiong_result={"ji_xiong": "吉", "pattern": "test", "explanation": "test"}
        )
        r = results[0]
        ranked = r["ranked_candidates"]
        if ranked:
            item = ranked[0]
            assert "timing" in item
            assert "score" in item
            assert "formulas" in item
            assert isinstance(item["score"], int)
            assert isinstance(item["formulas"], list)

    def test_no_kwargs_still_works(self):
        """不传kwargs时仍然正常工作"""
        h = Hexagram([8, 8, 7, 7, 8, 8], 2024, 1, 15)
        ws_results = analyze_hexagram_wangshuai(h)
        dongbian = analyze_dongbian(h, ws_results)
        yong_lines = [h.lines[0]]

        # Call without kwargs (backward compatible)
        results = analyze_yingqi(h, yong_lines, ws_results, dongbian)
        assert len(results) > 0
        assert "candidates" in results[0]

    def test_modifiers_structure(self):
        """modifiers结构正确"""
        h = Hexagram([9, 9, 9, 9, 9, 9], 2024, 1, 15)
        ws_results = analyze_hexagram_wangshuai(h)
        dongbian = analyze_dongbian(h, ws_results)
        yong_lines = [h.lines[0]]

        results = analyze_yingqi(
            h, yong_lines, ws_results, dongbian,
            event_duration="medium",
            jixiong_result={"ji_xiong": "吉", "pattern": "test", "explanation": "test"}
        )
        r = results[0]
        assert "acceleration" in r["modifiers"]
        assert "deceleration" in r["modifiers"]


# ============================================================================
# Test estimate_yuan_shen_yingqi
# ============================================================================

class TestEstimateYuanShenYingqi:
    """测试元神应期"""

    def test_ji_yuan_shen_xunkong(self):
        """吉时元神旬空 -> 出空应期"""
        h = Hexagram([8, 8, 7, 7, 8, 8], 2024, 1, 15)
        ws_results = analyze_hexagram_wangshuai(h)
        jixiong = {"ji_xiong": "吉", "pattern": "test", "explanation": "test"}
        # Try to find yuan_shen timing with qicai as yong_shen
        results = estimate_yuan_shen_yingqi(
            h, "妻财", ws_results, jixiong
        )
        # Results depend on whether 子孙 lines exist and are xunkong
        # Just verify structure
        assert isinstance(results, list)
        for r in results:
            assert "timing" in r
            assert "formula" in r
            assert "confidence" in r

    def test_xiong_yuan_shen_bei_chong(self):
        """凶时元神被冲"""
        h = Hexagram([8, 8, 7, 7, 8, 8], 2024, 1, 15)
        ws_results = analyze_hexagram_wangshuai(h)
        jixiong = {"ji_xiong": "凶", "pattern": "test", "explanation": "test"}
        results = estimate_yuan_shen_yingqi(
            h, "妻财", ws_results, jixiong
        )
        assert isinstance(results, list)
        # If there are 子孙 lines, should get 被冲 candidates
        for r in results:
            assert "被冲" in r["formula"] or "逢值" in r["formula"]

    def test_unknown_yong_shen_no_results(self):
        """未知用神六亲 -> 无结果"""
        h = Hexagram([8, 8, 7, 7, 8, 8], 2024, 1, 15)
        ws_results = analyze_hexagram_wangshuai(h)
        jixiong = {"ji_xiong": "吉", "pattern": "test", "explanation": "test"}
        results = estimate_yuan_shen_yingqi(
            h, "unknown", ws_results, jixiong
        )
        assert results == []


# ============================================================================
# Test estimate_yingqi (original function backward compat)
# ============================================================================

class TestEstimateYingqiOriginal:
    """测试原始estimate_yingqi函数后向兼容"""

    def test_static_wang_line(self):
        """旺静爻返回逢冲"""
        h = Hexagram([8, 8, 7, 7, 8, 8], 2024, 1, 15)
        ws_results = analyze_hexagram_wangshuai(h)
        for i, line in enumerate(h.lines):
            if not line.is_moving and ws_results[i]["overall"] == "旺":
                candidates = estimate_yingqi(line, ws_results[i])
                assert any("逢冲" in c for c in candidates)
                break

    def test_xunkong_line(self):
        """旬空爻返回填空冲空出空"""
        h = Hexagram([8, 8, 7, 7, 8, 8], 2024, 1, 15)
        ws_results = analyze_hexagram_wangshuai(h)
        for i, line in enumerate(h.lines):
            if line.is_xun_kong:
                candidates = estimate_yingqi(line, ws_results[i])
                assert any("填空" in c for c in candidates)
                break

    def test_moving_line(self):
        """动爻返回逢合逢值"""
        h = Hexagram([9, 7, 8, 7, 8, 7], 2024, 6, 15)
        ws_results = analyze_hexagram_wangshuai(h)
        dongbian = analyze_dongbian(h, ws_results)
        moving_analyses = dongbian.get("moving_analyses", {})
        for i, line in enumerate(h.lines):
            if line.is_moving:
                ma = moving_analyses.get(line.position)
                candidates = estimate_yingqi(line, ws_results[i], ma)
                assert len(candidates) > 0
                break
