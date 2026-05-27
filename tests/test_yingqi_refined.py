"""
应期精细化测试 - Tests for Refined Ying-Qi System

测试21个应期公式、候选排序、速度修正、远近筛选。
"""

import pytest
from dataclasses import dataclass
from liuyao.hexagram import Hexagram
from liuyao.wangshuai import analyze_hexagram_wangshuai
from liuyao.dongbian import analyze_dongbian
from liuyao.jixiong import find_yong_shen_lines
from liuyao.yingqi import (
    YingqiCandidate,
    estimate_yingqi,
    estimate_yingqi_candidates,
    analyze_yingqi,
    rank_yingqi_candidates,
    detect_speed_modifiers,
    formula_01_static,
    formula_02_moving,
    formula_03_yue_po,
    formula_04_ri_chong,
    formula_05_xun_kong,
    formula_06_yu_he_chong,
    formula_07_dong_yue_he,
    formula_08_single_attr,
    formula_09_bian_yao,
    formula_10_hua_jin,
    formula_11_hua_tui,
    formula_12_san_he,
    formula_13_san_mu,
    formula_14_san_xing,
    formula_15_fan_yin,
    formula_16_fu_yin,
    formula_17_fu_shen,
    formula_18_shou_ke,
    formula_19_shou_sheng,
    formula_20_guo_wang,
    formula_21_duo_xian,
)
from liuyao.analyzer import run_analysis
from liuyao.report import format_report


# =============================================================================
# YingqiCandidate Dataclass Tests
# =============================================================================

class TestYingqiCandidate:
    """应期候选数据类测试"""

    def test_create_candidate(self):
        """创建候选对象"""
        c = YingqiCandidate(
            di_zhi="辰", timing_type="day", formula_id=2,
            formula_name="动逢合", reasoning="动爻逢合即应"
        )
        assert c.di_zhi == "辰"
        assert c.timing_type == "day"
        assert c.formula_id == 2
        assert c.formula_name == "动逢合"
        assert c.priority == 0
        assert c.speed_modifier == ""

    def test_candidate_with_speed(self):
        """带速度修正的候选"""
        c = YingqiCandidate(
            di_zhi="午", timing_type="month", formula_id=3,
            formula_name="填实", reasoning="月破逢值",
            speed_modifier="accelerated"
        )
        assert c.speed_modifier == "accelerated"


# =============================================================================
# Individual Formula Tests
# =============================================================================

class TestFormula01Static:
    """公式1: 静爻"""

    def test_wang_static_feng_chong(self):
        """旺静逢冲"""
        candidates = formula_01_static("子", "旺")
        assert len(candidates) == 1
        assert candidates[0].di_zhi == "午"  # 子午冲
        assert candidates[0].formula_id == 1

    def test_shuai_static_feng_zhi(self):
        """衰静逢值"""
        candidates = formula_01_static("寅", "衰")
        assert len(candidates) == 1
        assert candidates[0].di_zhi == "寅"
        assert candidates[0].formula_id == 1


class TestFormula02Moving:
    """公式2: 动爻"""

    def test_moving_feng_he(self):
        """动爻逢合: 酉合辰"""
        candidates = formula_02_moving("酉")
        di_zhis = [c.di_zhi for c in candidates]
        assert "辰" in di_zhis  # 酉辰合
        assert "酉" in di_zhis  # 逢值

    def test_moving_feng_zhi(self):
        """动爻逢值"""
        candidates = formula_02_moving("午")
        di_zhis = [c.di_zhi for c in candidates]
        assert "午" in di_zhis


class TestFormula03YuePo:
    """公式3: 月破"""

    def test_yue_po_candidates(self):
        """月破三候选: 填实/补破/出月破"""
        candidates = formula_03_yue_po("申")
        assert len(candidates) == 3
        names = [c.formula_name for c in candidates]
        assert "填实" in names
        assert "补破" in names
        assert "出月破" in names
        # 填实 = 申
        tian_shi = [c for c in candidates if c.formula_name == "填实"][0]
        assert tian_shi.di_zhi == "申"
        # 补破 = 巳 (申巳合)
        bu_po = [c for c in candidates if c.formula_name == "补破"][0]
        assert bu_po.di_zhi == "巳"


class TestFormula04RiChong:
    """公式4: 日冲"""

    def test_ri_chong(self):
        """日冲逢值"""
        candidates = formula_04_ri_chong("卯")
        assert len(candidates) == 2
        di_zhis = [c.di_zhi for c in candidates]
        assert "卯" in di_zhis


class TestFormula05XunKong:
    """公式5: 旬空"""

    def test_xun_kong_candidates(self):
        """旬空三候选"""
        candidates = formula_05_xun_kong("午")
        names = [c.formula_name for c in candidates]
        assert "填空" in names
        assert "冲空" in names
        assert "出空" in names
        # 填空 = 午
        tian = [c for c in candidates if c.formula_name == "填空"][0]
        assert tian.di_zhi == "午"
        # 冲空 = 子 (午子冲)
        chong = [c for c in candidates if c.formula_name == "冲空"][0]
        assert chong.di_zhi == "子"


class TestFormula06YuHeChong:
    """公式6: 遇合/遇冲"""

    def test_yu_he_feng_chong(self):
        """遇合逢冲"""
        candidates = formula_06_yu_he_chong("寅", is_yu_he=True)
        assert len(candidates) == 1
        assert candidates[0].di_zhi == "申"  # 寅申冲

    def test_yu_chong_feng_he(self):
        """遇冲逢合"""
        candidates = formula_06_yu_he_chong("寅", is_yu_he=False)
        assert len(candidates) == 1
        assert candidates[0].di_zhi == "亥"  # 寅亥合


class TestFormula07DongYueHe:
    """公式7: 动逢月合"""

    def test_dong_yue_he(self):
        """三个月内"""
        candidates = formula_07_dong_yue_he("子")
        assert len(candidates) == 3
        # 子后三个月: 丑、寅、卯
        di_zhis = [c.di_zhi for c in candidates]
        assert "丑" in di_zhis
        assert "寅" in di_zhis
        assert "卯" in di_zhis


class TestFormula08SingleAttr:
    """公式8: 单属性"""

    def test_same_wuxing(self):
        """同五行地支"""
        # 寅木 -> 卯也是木
        candidates = formula_08_single_attr("寅")
        di_zhis = [c.di_zhi for c in candidates]
        assert "卯" in di_zhis
        assert "寅" not in di_zhis  # 排除自身


class TestFormula09BianYao:
    """公式9: 变爻"""

    def test_no_hui_tou(self):
        """无回头: 逢值/逢冲"""
        candidates = formula_09_bian_yao("寅", "巳", False)
        di_zhis = [c.di_zhi for c in candidates]
        assert "寅" in di_zhis  # 逢值
        assert "申" in di_zhis  # 寅申冲

    def test_with_hui_tou(self):
        """有回头: 逢值/逢合"""
        candidates = formula_09_bian_yao("寅", "亥", True)
        di_zhis = [c.di_zhi for c in candidates]
        assert "寅" in di_zhis  # 逢值
        assert "亥" in di_zhis  # 寅亥合


class TestFormula10HuaJin:
    """公式10: 化进神"""

    def test_hua_jin_shen(self):
        """申->酉 进神: 逢值申, 逢合巳, 逢进酉"""
        candidates = formula_10_hua_jin("申", "酉")
        di_zhis = [c.di_zhi for c in candidates]
        assert "申" in di_zhis  # 逢值(本)
        assert "巳" in di_zhis  # 逢合(申巳合)
        assert "酉" in di_zhis  # 逢进(变)


class TestFormula11HuaTui:
    """公式11: 化退神"""

    def test_hua_tui_shen(self):
        """酉->申 退神: 冲本卯, 冲变寅, 逢退值申"""
        candidates = formula_11_hua_tui("酉", "申")
        di_zhis = [c.di_zhi for c in candidates]
        assert "卯" in di_zhis  # 冲酉
        assert "寅" in di_zhis  # 冲申
        assert "申" in di_zhis  # 逢退值


class TestFormula12SanHe:
    """公式12: 三合局"""

    def test_internal_break(self):
        """内合破局"""
        san_he_info = {"wu_xing": "水", "members": ["申", "子", "辰"]}
        candidates = formula_12_san_he(san_he_info, is_internal=True)
        di_zhis = [c.di_zhi for c in candidates]
        # 冲成员: 寅冲申, 午冲子, 戌冲辰
        assert "寅" in di_zhis
        assert "午" in di_zhis
        assert "戌" in di_zhis

    def test_external_complete(self):
        """外合补全"""
        san_he_info = {"wu_xing": "水", "missing": "辰"}
        candidates = formula_12_san_he(san_he_info, is_internal=False)
        assert len(candidates) == 1
        assert candidates[0].di_zhi == "辰"


class TestFormula13SanMu:
    """公式13: 入墓"""

    def test_mu_wood(self):
        """木入墓未: 冲墓=丑, 冲爻=申(寅申冲)"""
        candidates = formula_13_san_mu("寅")
        di_zhis = [c.di_zhi for c in candidates]
        assert "丑" in di_zhis  # 冲墓(未丑冲)
        assert "申" in di_zhis  # 冲爻(寅申冲)
        assert "未" in di_zhis  # 出墓

    def test_mu_fire(self):
        """火入墓戌"""
        candidates = formula_13_san_mu("巳")
        names = [c.formula_name for c in candidates]
        assert "冲墓" in names
        # 火墓戌, 冲墓=辰(戌辰冲)
        chong_mu = [c for c in candidates if c.formula_name == "冲墓"][0]
        assert chong_mu.di_zhi == "辰"


class TestFormula14SanXing:
    """公式14: 三刑"""

    def test_san_xing_fill(self):
        """三刑补缺: 巳申寅组, 有巳申缺寅"""
        hex_zhis = ["巳", "申", "子", "午", "卯", "酉"]
        candidates = formula_14_san_xing("巳", hex_zhis)
        di_zhis = [c.di_zhi for c in candidates]
        assert "寅" in di_zhis  # 缺寅


class TestFormula15FanYin:
    """公式15: 反吟"""

    def test_fan_yin(self):
        """反吟逢值"""
        candidates = formula_15_fan_yin("卯")
        assert len(candidates) == 1
        assert candidates[0].di_zhi == "卯"
        assert candidates[0].formula_id == 15


class TestFormula16FuYin:
    """公式16: 伏吟"""

    def test_fu_yin_target(self):
        """伏吟目标: 逢值/逢冲"""
        candidates = formula_16_fu_yin("午", is_target=True)
        di_zhis = [c.di_zhi for c in candidates]
        assert "午" in di_zhis
        assert "子" in di_zhis  # 午子冲

    def test_fu_yin_non_target(self):
        """伏吟非目标: 逢值/逢合"""
        candidates = formula_16_fu_yin("午", is_target=False)
        di_zhis = [c.di_zhi for c in candidates]
        assert "午" in di_zhis
        assert "未" in di_zhis  # 午未合


class TestFormula17FuShen:
    """公式17: 伏神"""

    def test_fu_shen(self):
        """伏神: 逢值/逢合/冲飞"""
        candidates = formula_17_fu_shen("卯", "申")
        di_zhis = [c.di_zhi for c in candidates]
        assert "卯" in di_zhis  # 逢值
        assert "戌" in di_zhis  # 卯戌合
        assert "寅" in di_zhis  # 冲飞(申寅冲)


class TestFormula18ShouKe:
    """公式18: 吉用受克"""

    def test_shou_ke(self):
        """等克源被冲"""
        candidates = formula_18_shou_ke("寅", "申")
        assert len(candidates) == 1
        assert candidates[0].di_zhi == "寅"  # 寅冲申


class TestFormula19ShouSheng:
    """公式19: 凶用受生"""

    def test_shou_sheng(self):
        """等生源被冲"""
        candidates = formula_19_shou_sheng("寅", "亥")
        assert len(candidates) == 1
        assert candidates[0].di_zhi == "巳"  # 巳冲亥


class TestFormula20GuoWang:
    """公式20: 过旺"""

    def test_guo_wang(self):
        """过旺逢墓/逢克"""
        candidates = formula_20_guo_wang("寅")
        names = [c.formula_name for c in candidates]
        assert "过旺逢墓" in names
        assert "过旺逢克" in names
        # 木墓未
        mu_c = [c for c in candidates if c.formula_name == "过旺逢墓"][0]
        assert mu_c.di_zhi == "未"


class TestFormula21DuoXian:
    """公式21: 用神多现"""

    def test_duo_xian(self):
        """多现逢墓"""
        candidates = formula_21_duo_xian("酉")
        assert len(candidates) == 1
        # 金墓丑
        assert candidates[0].di_zhi == "丑"



# =============================================================================
# Ranking Tests
# =============================================================================

class TestRanking:
    """候选排序测试"""

    def test_frequency_higher_priority(self):
        """出现频率越高优先级越高"""
        candidates = [
            YingqiCandidate(di_zhi="子", timing_type="day", formula_id=1,
                           formula_name="A", reasoning="r1"),
            YingqiCandidate(di_zhi="午", timing_type="day", formula_id=2,
                           formula_name="B", reasoning="r2"),
            YingqiCandidate(di_zhi="子", timing_type="month", formula_id=3,
                           formula_name="C", reasoning="r3"),
            YingqiCandidate(di_zhi="子", timing_type="day", formula_id=4,
                           formula_name="D", reasoning="r4"),
        ]
        ranked = rank_yingqi_candidates(candidates, "寅", "卯")
        # 子 appears 3 times, 午 appears 1 time
        # Top results should be 子
        top_zhis = [c.di_zhi for c in ranked[:3]]
        assert top_zhis.count("子") == 3

    def test_proximity_bonus(self):
        """距离近者优先"""
        candidates = [
            YingqiCandidate(di_zhi="卯", timing_type="day", formula_id=1,
                           formula_name="A", reasoning="r1"),
            YingqiCandidate(di_zhi="酉", timing_type="day", formula_id=2,
                           formula_name="B", reasoning="r2"),
        ]
        # Current month is 寅 (index 2)
        ranked = rank_yingqi_candidates(candidates, "寅", "寅")
        # 卯 is 1 step from 寅, 酉 is 7 steps from 寅
        assert ranked[0].di_zhi == "卯"

    def test_adjacent_bonus(self):
        """相邻地支加成"""
        candidates = [
            YingqiCandidate(di_zhi="巳", timing_type="day", formula_id=1,
                           formula_name="A", reasoning="r1"),
            YingqiCandidate(di_zhi="午", timing_type="day", formula_id=2,
                           formula_name="B", reasoning="r2"),
            YingqiCandidate(di_zhi="子", timing_type="day", formula_id=3,
                           formula_name="C", reasoning="r3"),
        ]
        # 巳 and 午 are adjacent, both get bonus
        ranked = rank_yingqi_candidates(candidates, "辰", "辰")
        top_zhis = [c.di_zhi for c in ranked[:2]]
        assert "巳" in top_zhis
        assert "午" in top_zhis

    def test_empty_candidates(self):
        """空候选列表"""
        result = rank_yingqi_candidates([])
        assert result == []


# =============================================================================
# Speed Modifier Tests
# =============================================================================

class TestSpeedModifiers:
    """速度修正测试"""

    def test_acceleration_an_dong(self):
        """暗动加速"""
        dongbian = {
            "moving_analyses": {},
            "an_dong": [{"position": 3, "di_zhi": "申", "reason": "test", "type": "暗动"}],
            "san_he_ju": [],
        }
        speed = detect_speed_modifiers(dongbian)
        assert speed == "accelerated"

    def test_deceleration_san_he(self):
        """三合减速"""
        dongbian = {
            "moving_analyses": {},
            "an_dong": [],
            "san_he_ju": [{"wu_xing": "水", "members": ["申", "子", "辰"]}],
        }
        speed = detect_speed_modifiers(dongbian)
        assert speed == "decelerated"

    def test_no_modifier(self):
        """无修正"""
        dongbian = {
            "moving_analyses": {},
            "an_dong": [],
            "san_he_ju": [],
        }
        speed = detect_speed_modifiers(dongbian)
        assert speed == ""

    def test_acceleration_pure_gua(self):
        """变纯卦加速"""
        dongbian = {
            "moving_analyses": {},
            "an_dong": [],
            "san_he_ju": [],
        }
        # Create mock hexagram with bian_gua_name = pure hexagram
        class MockHex:
            bian_gua_name = "乾为天"
        speed = detect_speed_modifiers(dongbian, MockHex())
        assert speed == "accelerated"


# =============================================================================
# Time Scope Filtering Tests
# =============================================================================

class TestTimeScope:
    """远近筛选测试"""

    def test_short_scope_excludes_year(self):
        """短期排除年级候选"""
        h = Hexagram([8, 7, 7, 9, 7, 8], 2024, 1, 15)
        ws = analyze_hexagram_wangshuai(h)
        db = analyze_dongbian(h, ws)
        yong_lines = find_yong_shen_lines(h, "妻财")

        if yong_lines:
            results = analyze_yingqi(h, yong_lines, ws, db, time_scope="short")
            for r in results:
                ranked = r.get("ranked_candidates", [])
                # Should not have year-type candidates
                year_types = [c for c in ranked if c.timing_type == "year"]
                assert len(year_types) == 0 or len(ranked) == 0

    def test_medium_scope_boosts_month(self):
        """中期加权月级候选"""
        h = Hexagram([8, 7, 7, 9, 7, 8], 2024, 1, 15)
        ws = analyze_hexagram_wangshuai(h)
        db = analyze_dongbian(h, ws)
        yong_lines = find_yong_shen_lines(h, "妻财")

        if yong_lines:
            results = analyze_yingqi(h, yong_lines, ws, db, time_scope="medium")
            assert len(results) > 0

    def test_none_scope_no_filter(self):
        """无筛选保留全部"""
        h = Hexagram([8, 7, 7, 9, 7, 8], 2024, 1, 15)
        ws = analyze_hexagram_wangshuai(h)
        db = analyze_dongbian(h, ws)
        yong_lines = find_yong_shen_lines(h, "妻财")

        if yong_lines:
            results_none = analyze_yingqi(h, yong_lines, ws, db, time_scope=None)
            results_short = analyze_yingqi(h, yong_lines, ws, db, time_scope="short")
            # None scope should have >= candidates than short scope
            for rn, rs in zip(results_none, results_short):
                assert len(rn["ranked_candidates"]) >= len(rs["ranked_candidates"])


# =============================================================================
# Integration Tests
# =============================================================================

class TestYingqiIntegration:
    """应期集成测试"""

    def test_backward_compat_estimate(self):
        """estimate_yingqi返回字符串列表(向后兼容)"""
        h = Hexagram([7, 7, 7, 7, 7, 7], 2024, 1, 15)
        ws = analyze_hexagram_wangshuai(h)
        for i, line in enumerate(h.lines):
            candidates = estimate_yingqi(line, ws[i])
            assert isinstance(candidates, list)
            for c in candidates:
                assert isinstance(c, str)

    def test_backward_compat_analyze(self):
        """analyze_yingqi向后兼容"""
        h = Hexagram([8, 7, 7, 9, 7, 8], 2024, 1, 15)
        ws = analyze_hexagram_wangshuai(h)
        db = analyze_dongbian(h, ws)
        yong_lines = find_yong_shen_lines(h, "妻财")

        if yong_lines:
            results = analyze_yingqi(h, yong_lines, ws, db)
            for r in results:
                assert "position" in r
                assert "di_zhi" in r
                assert "liu_qin" in r
                assert "candidates" in r
                # candidates still has strings
                for c in r["candidates"]:
                    assert isinstance(c, str)

    def test_ranked_candidates_in_result(self):
        """结果中包含ranked_candidates"""
        h = Hexagram([8, 7, 7, 9, 7, 8], 2024, 1, 15)
        ws = analyze_hexagram_wangshuai(h)
        db = analyze_dongbian(h, ws)
        yong_lines = find_yong_shen_lines(h, "妻财")

        if yong_lines:
            results = analyze_yingqi(h, yong_lines, ws, db)
            for r in results:
                assert "ranked_candidates" in r
                for c in r["ranked_candidates"]:
                    assert isinstance(c, YingqiCandidate)

    def test_report_shows_formula_names(self):
        """报告显示公式名称"""
        h = Hexagram([8, 7, 7, 9, 7, 8], 2024, 1, 15)
        report = run_analysis(h, "cai")
        text = format_report(report)
        assert "应期推断" in text
        # Should have numbered candidates with formula names in brackets
        if report.yingqi_results:
            assert "[" in text  # formula name in brackets

    def test_full_pipeline_with_time_scope(self):
        """完整管道带时间范围"""
        h = Hexagram([9, 7, 7, 8, 7, 8], 2024, 3, 15)
        ws = analyze_hexagram_wangshuai(h)
        db = analyze_dongbian(h, ws)
        yong_lines = find_yong_shen_lines(h, "妻财")

        if yong_lines:
            for scope in ["short", "medium", "long", None]:
                results = analyze_yingqi(h, yong_lines, ws, db, time_scope=scope)
                assert len(results) > 0
                for r in results:
                    assert len(r["candidates"]) > 0

    def test_acceptance_moving_you(self):
        """验收: 动爻酉 -> 候选辰(逢合)和酉(逢值)"""
        candidates = formula_02_moving("酉")
        di_zhis = [c.di_zhi for c in candidates]
        assert "辰" in di_zhis
        assert "酉" in di_zhis

    def test_acceptance_hua_jin(self):
        """验收: 申->酉进神 -> 候选申(逢值), 巳(逢合), 酉(逢进)"""
        candidates = formula_10_hua_jin("申", "酉")
        di_zhis = [c.di_zhi for c in candidates]
        assert "申" in di_zhis
        assert "巳" in di_zhis
        assert "酉" in di_zhis

    def test_acceptance_ranking_frequency(self):
        """验收: 多次出现的候选排名更高"""
        candidates = [
            YingqiCandidate(di_zhi="丑", timing_type="day", formula_id=1,
                           formula_name="A", reasoning="r"),
            YingqiCandidate(di_zhi="寅", timing_type="day", formula_id=2,
                           formula_name="B", reasoning="r"),
            YingqiCandidate(di_zhi="丑", timing_type="month", formula_id=3,
                           formula_name="C", reasoning="r"),
            YingqiCandidate(di_zhi="丑", timing_type="day", formula_id=4,
                           formula_name="D", reasoning="r"),
            YingqiCandidate(di_zhi="寅", timing_type="day", formula_id=5,
                           formula_name="E", reasoning="r"),
        ]
        ranked = rank_yingqi_candidates(candidates, "子", "子")
        # 丑 appears 3 times, 寅 appears 2 times
        # First should be 丑
        assert ranked[0].di_zhi == "丑"

    def test_existing_tests_still_pass(self):
        """确保现有的应期逻辑仍然工作"""
        h = Hexagram([7, 7, 7, 7, 7, 7], 2024, 1, 15)
        ws = analyze_hexagram_wangshuai(h)
        # Test xun-kong still works
        for i, line in enumerate(h.lines):
            if line.is_xun_kong:
                candidates = estimate_yingqi(line, ws[i])
                assert any("填空" in c for c in candidates)
                assert any("冲空" in c for c in candidates)
                assert any("出空" in c for c in candidates)
                break

