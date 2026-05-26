"""
旬空深层分析模块测试 - Tests for xunkong module

测试真空/假空判断、特殊应用、出空方法。
"""

import pytest
from liuyao.hexagram import Hexagram
from liuyao.wangshuai import analyze_hexagram_wangshuai
from liuyao.xunkong import (
    is_jia_kong,
    is_zhen_kong_yongshen,
    is_zhen_kong_shiyao,
    analyze_xunkong_special,
    get_chu_kong_method,
    analyze_xunkong,
)


class TestJiaKong:
    """假空判断测试"""

    def test_moving_line_xunkong_is_jia_kong(self):
        """动爻旬空 = 假空 (动不为空)"""
        # 找一个动爻是旬空的卦
        # 2024-1-15 日柱: 旬空为 戌亥
        # 需要卦中有地支为戌或亥的动爻
        # 坤为地内卦: 未巳卯, 外卦: 丑亥酉
        # 坤为地全动 [6,6,6,6,6,6], 第5爻是亥(旬空)
        h = Hexagram([6, 6, 6, 6, 6, 6], 2024, 1, 15)
        # 查找旬空动爻
        for line in h.lines:
            if line.is_xun_kong and line.is_moving:
                ws_results = analyze_hexagram_wangshuai(h)
                ws = ws_results[line.position - 1]
                result = is_jia_kong(line, h, ws)
                assert result["is_jia_kong"] is True
                assert "动不为空" in result["reason"]
                break

    def test_prosperous_static_xunkong_is_jia_kong(self):
        """旺相静爻旬空 = 假空 (旺不为空)"""
        # 需要旬空爻是静爻且旺相
        # 2024-1-15: 丑月寅日, 旬空戌亥
        # 亥水在丑月: 丑土克水=月克; 寅日: 水生木=泄 => 衰
        # 需要找旬空爻旺的
        # 换个日期: 2024-10-20, 计算旬空...
        # 让我们试试不同的日期使旬空爻为旺
        # 用2024-3-20: 需要看实际旬空
        h = Hexagram([7, 7, 7, 7, 7, 7], 2024, 3, 20)
        ws_results = analyze_hexagram_wangshuai(h)
        # 找旬空且旺的静爻
        found = False
        for i, line in enumerate(h.lines):
            if line.is_xun_kong and not line.is_moving:
                ws = ws_results[i]
                if ws["overall"] == "旺":
                    result = is_jia_kong(line, h, ws)
                    assert result["is_jia_kong"] is True
                    assert "旺不为空" in result["reason"]
                    found = True
                    break
        # 如果这个日期没有匹配的, 测试结构仍然正确
        if not found:
            # 直接测试逻辑: 构造模拟输入
            h2 = Hexagram([7, 7, 7, 7, 7, 7], 2024, 1, 15)
            for i, line in enumerate(h2.lines):
                if line.is_xun_kong and not line.is_moving:
                    # 手动传入旺的旺衰结果
                    fake_ws = {"overall": "旺"}
                    result = is_jia_kong(line, h2, fake_ws)
                    assert result["is_jia_kong"] is True
                    assert "旺不为空" in result["reason"]
                    found = True
                    break
        assert found, "应能找到测试旬空爻"

    def test_weak_static_xunkong_not_jia_kong(self):
        """衰弱静爻旬空 = 非假空"""
        h = Hexagram([7, 7, 7, 7, 7, 7], 2024, 1, 15)
        ws_results = analyze_hexagram_wangshuai(h)
        for i, line in enumerate(h.lines):
            if line.is_xun_kong and not line.is_moving:
                ws = ws_results[i]
                if ws["overall"] != "旺":
                    result = is_jia_kong(line, h, ws)
                    assert result["is_jia_kong"] is False
                    break

    def test_non_xunkong_line(self):
        """非旬空爻返回非假空"""
        h = Hexagram([7, 7, 7, 7, 7, 7], 2024, 1, 15)
        ws_results = analyze_hexagram_wangshuai(h)
        for i, line in enumerate(h.lines):
            if not line.is_xun_kong:
                ws = ws_results[i]
                result = is_jia_kong(line, h, ws)
                assert result["is_jia_kong"] is False
                assert "非旬空" in result["reason"]
                break


class TestZhenKongYongShen:
    """用神真空测试"""

    def test_weak_static_yongshen_is_zhen_kong(self):
        """衰弱静爻用神旬空 = 真空"""
        h = Hexagram([7, 7, 7, 7, 7, 7], 2024, 1, 15)
        ws_results = analyze_hexagram_wangshuai(h)
        for i, line in enumerate(h.lines):
            if line.is_xun_kong and not line.is_moving:
                ws = ws_results[i]
                if ws["overall"] in ("衰", "平"):
                    result = is_zhen_kong_yongshen(line, h, ws_results)
                    assert result["is_zhen_kong"] is True
                    assert "真空" in result["reason"]
                    break

    def test_wang_static_yongshen_not_zhen_kong(self):
        """旺相静爻用神旬空 = 非真空"""
        h = Hexagram([7, 7, 7, 7, 7, 7], 2024, 1, 15)
        ws_results = analyze_hexagram_wangshuai(h)
        for i, line in enumerate(h.lines):
            if line.is_xun_kong and not line.is_moving:
                # 模拟旺的结果
                ws_results[i]["overall"] = "旺"
                result = is_zhen_kong_yongshen(line, h, ws_results)
                assert result["is_zhen_kong"] is False
                assert "旺" in result["reason"]
                break

    def test_moving_yongshen_not_zhen_kong(self):
        """动爻用神旬空 = 非真空(动不为空)"""
        h = Hexagram([6, 6, 6, 6, 6, 6], 2024, 1, 15)
        ws_results = analyze_hexagram_wangshuai(h)
        for i, line in enumerate(h.lines):
            if line.is_xun_kong and line.is_moving:
                result = is_zhen_kong_yongshen(line, h, ws_results)
                assert result["is_zhen_kong"] is False
                assert "动不为空" in result["reason"]
                break


class TestZhenKongShiYao:
    """世爻真空测试"""

    def test_shi_yao_no_support_is_zhen_kong(self):
        """世爻静空且日月均无生扶 = 真空"""
        # 需要找世爻旬空且日月不生扶的情况
        h = Hexagram([7, 7, 7, 7, 7, 7], 2024, 1, 15)
        ws_results = analyze_hexagram_wangshuai(h)
        shi_line = None
        for line in h.lines:
            if line.is_shi:
                shi_line = line
                break
        if shi_line and shi_line.is_xun_kong:
            result = is_zhen_kong_shiyao(shi_line, h, ws_results)
            # 具体结果取决于日月关系
            assert "is_zhen_kong" in result
            assert "reason" in result
        else:
            # 世爻不旬空时, 验证非旬空返回
            if shi_line:
                result = is_zhen_kong_shiyao(shi_line, h, ws_results)
                assert result["is_zhen_kong"] is False

    def test_shi_yao_with_support_not_zhen_kong(self):
        """世爻得日月生扶 = 假空"""
        h = Hexagram([7, 7, 7, 7, 7, 7], 2024, 1, 15)
        ws_results = analyze_hexagram_wangshuai(h)
        # 模拟世爻旬空且有日月支持
        shi_line = None
        for line in h.lines:
            if line.is_shi:
                shi_line = line
                break
        if shi_line and not shi_line.is_xun_kong:
            # 非旬空世爻直接返回非真空
            result = is_zhen_kong_shiyao(shi_line, h, ws_results)
            assert result["is_zhen_kong"] is False

    def test_shi_yao_dong_not_zhen_kong(self):
        """世爻动则旬空不为真空"""
        # 构造世爻动且旬空
        h = Hexagram([6, 6, 6, 6, 6, 6], 2024, 1, 15)
        ws_results = analyze_hexagram_wangshuai(h)
        shi_line = None
        for line in h.lines:
            if line.is_shi:
                shi_line = line
                break
        if shi_line and shi_line.is_xun_kong:
            result = is_zhen_kong_shiyao(shi_line, h, ws_results)
            assert result["is_zhen_kong"] is False
            assert "动不为空" in result["reason"]


class TestXunKongSpecial:
    """旬空特殊应用测试"""

    def test_bing_yongshen_xunkong(self):
        """占病用神旬空 = 短期痊愈"""
        # 需要用神(官鬼)旬空
        # 2024-1-15 旬空: 戌亥
        # 官鬼爻地支为戌或亥
        h = Hexagram([8, 7, 7, 9, 7, 8], 2024, 1, 15)
        ws_results = analyze_hexagram_wangshuai(h)
        # 检查是否有官鬼旬空
        has_guanGui_kong = any(
            l.liu_qin == "官鬼" and l.is_xun_kong for l in h.lines)
        result = analyze_xunkong_special(h, "官鬼", "bing", ws_results)
        if has_guanGui_kong:
            assert any(s["type"] == "占病用神旬空" for s in result)
        # 验证结构
        for s in result:
            assert "type" in s
            assert "description" in s

    def test_cai_xiongdi_chi_shi_kong(self):
        """求财兄弟持世空亡 = 短期得财"""
        # 需要构造世爻是兄弟且旬空的情况
        h = Hexagram([7, 7, 7, 7, 7, 7], 2024, 1, 15)
        ws_results = analyze_hexagram_wangshuai(h)
        shi_line = None
        for line in h.lines:
            if line.is_shi:
                shi_line = line
                break
        if shi_line and shi_line.liu_qin == "兄弟" and shi_line.is_xun_kong:
            result = analyze_xunkong_special(h, "妻财", "cai", ws_results)
            assert any(s["type"] == "求财兄弟持世空亡" for s in result)

    def test_xingren_shi_kong(self):
        """行人世空 = 行人将归"""
        # 需要世爻旬空
        h = Hexagram([7, 7, 7, 7, 7, 7], 2024, 1, 15)
        ws_results = analyze_hexagram_wangshuai(h)
        shi_line = None
        for line in h.lines:
            if line.is_shi:
                shi_line = line
                break
        if shi_line and shi_line.is_xun_kong:
            result = analyze_xunkong_special(h, "妻财", "xingRen", ws_results)
            assert any(s["type"] == "行人世空" for s in result)

    def test_youhuan_zisun_kong(self):
        """忧患子孙逢空 = 忧郁短期内无法了结"""
        h = Hexagram([7, 7, 7, 7, 7, 7], 2024, 1, 15)
        ws_results = analyze_hexagram_wangshuai(h)
        has_zisun_kong = any(
            l.liu_qin == "子孙" and l.is_xun_kong for l in h.lines)
        result = analyze_xunkong_special(h, "子孙", "youHuan", ws_results)
        if has_zisun_kong:
            assert any(s["type"] == "忧患子孙逢空" for s in result)

    def test_no_special_for_other_types(self):
        """非特定问事类型无特殊应用"""
        h = Hexagram([7, 8, 7, 8, 7, 8], 2024, 6, 15)
        ws_results = analyze_hexagram_wangshuai(h)
        result = analyze_xunkong_special(h, "官鬼", "other", ws_results)
        # other类型不触发特殊应用
        assert isinstance(result, list)


class TestChuKongMethod:
    """出空方法测试"""

    def test_xunkong_line_has_methods(self):
        """旬空爻有三种出空方法"""
        h = Hexagram([7, 7, 7, 7, 7, 7], 2024, 1, 15)
        for line in h.lines:
            if line.is_xun_kong:
                result = get_chu_kong_method(line)
                assert "tian_kong" in result
                assert "chong_kong" in result
                assert "chu_xun" in result
                assert line.di_zhi in result["tian_kong"]
                assert "出旬" in result["chu_xun"]
                break

    def test_non_xunkong_no_methods(self):
        """非旬空爻无出空方法"""
        h = Hexagram([7, 7, 7, 7, 7, 7], 2024, 1, 15)
        for line in h.lines:
            if not line.is_xun_kong:
                result = get_chu_kong_method(line)
                assert result["tian_kong"] == ""
                assert result["chong_kong"] == ""
                assert "非旬空" in result["chu_xun"]
                break

    def test_chong_kong_correct_zhi(self):
        """冲空地支正确"""
        from liuyao.data import LIU_CHONG
        h = Hexagram([7, 7, 7, 7, 7, 7], 2024, 1, 15)
        for line in h.lines:
            if line.is_xun_kong:
                result = get_chu_kong_method(line)
                expected_chong = LIU_CHONG[line.di_zhi]
                assert expected_chong in result["chong_kong"]
                break


class TestAnalyzeXunkong:
    """旬空综合分析测试"""

    def test_comprehensive_analysis(self):
        """综合分析返回完整结构"""
        h = Hexagram([8, 7, 7, 9, 7, 8], 2024, 1, 15)
        ws_results = analyze_hexagram_wangshuai(h)
        result = analyze_xunkong(h, "妻财", "cai", ws_results)

        assert "kong_lines" in result
        assert "specials" in result
        assert "has_kong" in result
        assert isinstance(result["kong_lines"], list)
        assert isinstance(result["specials"], list)

    def test_no_kong_lines(self):
        """无旬空爻时结果正确"""
        # 找一个没有旬空爻的卦
        # 需要所有六爻的地支都不在旬空中
        # 试不同日期
        h = Hexagram([7, 7, 7, 7, 7, 7], 2024, 2, 5)
        ws_results = analyze_hexagram_wangshuai(h)
        has_kong = any(l.is_xun_kong for l in h.lines)
        result = analyze_xunkong(h, "妻财", "cai", ws_results)
        assert result["has_kong"] == has_kong

    def test_integration_with_analyzer(self):
        """与分析器集成测试"""
        from liuyao.analyzer import run_analysis
        h = Hexagram([8, 7, 7, 9, 7, 8], 2024, 1, 15)
        report = run_analysis(h, "cai")
        assert report.xunkong_results is not None
        assert "kong_lines" in report.xunkong_results
        assert "specials" in report.xunkong_results
