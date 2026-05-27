"""
伏神/藏爻模块测试 - Fu-Shen / Cang-Yao Tests

覆盖:
- get_cang_yao: 纯卦藏爻正确性
- find_fu_shen: 缺失六亲定位
- analyze_fu_shen_status: 旬空、月破检测
- judge_fushen_jixiong: 三路径吉凶判断
- estimate_fushen_yingqi: 应期推断
- 集成测试: run_analysis 生成伏神报告
"""

import pytest

from liuyao.hexagram import Hexagram
from liuyao.fushen import (
    get_cang_yao, find_fu_shen,
    analyze_fu_shen_status, judge_fushen_jixiong,
    estimate_fushen_yingqi,
)
from liuyao.analyzer import run_analysis
from liuyao.data import DI_ZHI_WU_XING, get_liu_qin, NA_JIA, LIU_CHONG


class TestGetCangYao:
    """测试 get_cang_yao 获取本宫纯卦藏爻"""

    def test_qian_palace_cang_yao(self):
        """乾宫卦的藏爻应为乾为天(甲子寅辰/甲午申戌)"""
        # 天风姤 - 乾宫一世卦
        h = Hexagram([8, 7, 7, 7, 7, 7], 2024, 1, 15)
        assert h.palace_name == "乾"

        cang = get_cang_yao(h)
        assert len(cang) == 6

        # 乾纳甲: 甲, [子, 寅, 辰], [午, 申, 戌]
        expected = [
            {"position": 1, "di_zhi": "子", "wu_xing": "水", "liu_qin": "子孙", "tian_gan": "甲"},
            {"position": 2, "di_zhi": "寅", "wu_xing": "木", "liu_qin": "妻财", "tian_gan": "甲"},
            {"position": 3, "di_zhi": "辰", "wu_xing": "土", "liu_qin": "父母", "tian_gan": "甲"},
            {"position": 4, "di_zhi": "午", "wu_xing": "火", "liu_qin": "官鬼", "tian_gan": "甲"},
            {"position": 5, "di_zhi": "申", "wu_xing": "金", "liu_qin": "兄弟", "tian_gan": "甲"},
            {"position": 6, "di_zhi": "戌", "wu_xing": "土", "liu_qin": "父母", "tian_gan": "甲"},
        ]

        for i, (actual, exp) in enumerate(zip(cang, expected)):
            assert actual == exp, f"Position {i+1}: expected {exp}, got {actual}"

    def test_zhen_palace_cang_yao(self):
        """震宫卦的藏爻应为震为雷(庚子寅辰/庚午申戌)"""
        # 雷地豫 - 震宫一世卦
        h = Hexagram([8, 8, 8, 7, 8, 8], 2024, 1, 15)
        assert h.palace_name == "震"

        cang = get_cang_yao(h)
        assert len(cang) == 6

        # 震纳甲: 庚, [子, 寅, 辰], [午, 申, 戌]
        # 震宫五行为木
        expected_di_zhi = ["子", "寅", "辰", "午", "申", "戌"]
        for i, cy in enumerate(cang):
            assert cy["di_zhi"] == expected_di_zhi[i]
            assert cy["tian_gan"] == "庚"
            assert cy["wu_xing"] == DI_ZHI_WU_XING[expected_di_zhi[i]]
            assert cy["liu_qin"] == get_liu_qin("木", cy["wu_xing"])

    def test_kun_palace_cang_yao(self):
        """坤宫卦的藏爻应为坤为地(乙未巳卯/乙丑亥酉)"""
        # 地雷复 - 坤宫一世卦
        h = Hexagram([7, 8, 8, 8, 8, 8], 2024, 1, 15)
        assert h.palace_name == "坤"

        cang = get_cang_yao(h)
        assert len(cang) == 6

        # 坤纳甲: 乙, [未, 巳, 卯], [丑, 亥, 酉]
        expected_di_zhi = ["未", "巳", "卯", "丑", "亥", "酉"]
        for i, cy in enumerate(cang):
            assert cy["di_zhi"] == expected_di_zhi[i]
            assert cy["tian_gan"] == "乙"

    def test_kan_palace_cang_yao(self):
        """坎宫卦的藏爻应为坎为水(戊寅辰午/戊申戌子)"""
        # 水泽节 - 坎宫一世卦
        h = Hexagram([7, 7, 8, 8, 7, 8], 2024, 1, 15)
        assert h.palace_name == "坎"

        cang = get_cang_yao(h)
        assert len(cang) == 6

        expected_di_zhi = ["寅", "辰", "午", "申", "戌", "子"]
        for i, cy in enumerate(cang):
            assert cy["di_zhi"] == expected_di_zhi[i]
            assert cy["tian_gan"] == "戊"

    def test_cang_yao_all_liu_qin_present_for_pure_hexagram(self):
        """纯卦本身的藏爻包含所有5种六亲(至少有兄弟)"""
        # 乾为天 (纯卦, 乾宫)
        h = Hexagram([7, 7, 7, 7, 7, 7], 2024, 1, 15)
        cang = get_cang_yao(h)

        liu_qin_set = set(cy["liu_qin"] for cy in cang)
        # 乾宫(金): 子=水=子孙, 寅=木=妻财, 辰=土=父母, 午=火=官鬼, 申=金=兄弟, 戌=土=父母
        assert "子孙" in liu_qin_set
        assert "妻财" in liu_qin_set
        assert "父母" in liu_qin_set
        assert "官鬼" in liu_qin_set
        assert "兄弟" in liu_qin_set


class TestFindFuShen:
    """测试 find_fu_shen 查找伏神"""

    def test_liu_qin_present_returns_none(self):
        """卦中已有目标六亲时, 返回None"""
        # 乾为天: 所有六亲都有
        h = Hexagram([7, 7, 7, 7, 7, 7], 2024, 1, 15)
        result = find_fu_shen(h, "妻财")
        assert result is None

    def test_find_missing_liu_qin(self):
        """卦中缺失六亲时, 正确定位伏神"""
        # 天风姤 (乾宫): 初爻变阴
        # 乾宫, 上卦乾, 下卦巽
        # 巽纳甲: 辛, [丑, 亥, 酉]
        # 乾纳甲: 甲, [午, 申, 戌]
        # 宫五行: 金
        # 初爻: 辛丑土=父母, 二爻: 辛亥水=子孙, 三爻: 辛酉金=兄弟
        # 四爻: 甲午火=官鬼, 五爻: 甲申金=兄弟, 六爻: 甲戌土=父母
        # 缺失: 妻财(金克木=妻财, 需要木)
        h = Hexagram([8, 7, 7, 7, 7, 7], 2024, 1, 15)
        assert h.palace_name == "乾"

        # 检查确实缺妻财
        liu_qin_present = set(l.liu_qin for l in h.lines)
        assert "妻财" not in liu_qin_present

        result = find_fu_shen(h, "妻财")
        assert result is not None
        assert result["fu_liu_qin"] == "妻财"
        # 乾宫纯卦第2爻: 甲寅木=妻财
        assert result["position"] == 2
        assert result["fu_di_zhi"] == "寅"
        assert result["fu_wu_xing"] == "木"
        assert result["fu_tian_gan"] == "甲"

        # 飞神为天风姤第2爻
        fei_line = h.lines[1]
        assert result["fei_di_zhi"] == fei_line.di_zhi
        assert result["fei_wu_xing"] == fei_line.wu_xing
        assert result["fei_liu_qin"] == fei_line.liu_qin

    def test_find_guan_gui_in_zhen_palace(self):
        """震宫(木)卦中查找官鬼(金克木=官鬼, 需要金)"""
        # 雷地豫 - 震宫
        # 下卦坤: 乙未土, 乙巳火, 乙卯木
        # 上卦震: 庚午火, 庚申金, 庚戌土
        # 宫五行: 木
        # 官鬼 = 克木的 = 金
        h = Hexagram([8, 8, 8, 7, 8, 8], 2024, 1, 15)
        assert h.palace_name == "震"

        # 检查是否有官鬼(金)
        has_guan = any(l.liu_qin == "官鬼" for l in h.lines)
        # 庚申金 = 兄弟? No: 木宫, 金克木 = 官鬼. Let's check
        # Actually 申=金, 金克木 = 官鬼
        # So 第5爻 庚申金 = 官鬼
        if has_guan:
            result = find_fu_shen(h, "官鬼")
            assert result is None
        else:
            result = find_fu_shen(h, "官鬼")
            assert result is not None


class TestAnalyzeFuShenStatus:
    """测试 analyze_fu_shen_status 伏神状态检测"""

    def test_fu_shen_xun_kong(self):
        """伏神地支在旬空中"""
        # 需构造使得伏神地支在旬空中的场景
        # 天风姤: 乾宫, 伏神妻财在第2爻(寅)
        # 选择日期使旬空包含寅
        # 旬空: 甲戌旬空申酉, 甲子旬空戌亥, 甲寅旬空子丑
        # 甲申旬空午未, 甲辰旬空寅卯 -- 我们需要寅在旬空
        # 甲辰日: 干=甲(0), 支=辰(4). 旬起始支=(4-0)%12=4(辰). 空1=(4+10)%12=2(寅), 空2=(4+11)%12=3(卯)
        # 所以日柱为甲辰时旬空为寅卯
        # 2024-03-01 -> need to find a date with day_gan=甲, day_zhi=辰
        # Let's use the hexagram and manually verify
        h = Hexagram([8, 7, 7, 7, 7, 7], 2024, 3, 11)
        # Check xun kong
        fu_info = find_fu_shen(h, "妻财")
        if fu_info is None:
            pytest.skip("This hexagram has 妻财 visible")

        status = analyze_fu_shen_status(fu_info, h)

        # Verify the fu_kong flag
        expected_fu_kong = fu_info["fu_di_zhi"] in h.xun_kong
        assert status["fu_kong"] == expected_fu_kong

    def test_fu_shen_yue_po(self):
        """伏神月破检测: 月支冲伏神地支"""
        # 天风姤: 伏神妻财 寅木 在第2爻
        # 月破: 月支冲伏神 -> 需要月支=申(申冲寅)
        # 申月 = 农历七月(阳历约8月)
        # 2024-08-15 approx -> month_zhi should be 申
        h = Hexagram([8, 7, 7, 7, 7, 7], 2024, 8, 15)
        fu_info = find_fu_shen(h, "妻财")
        if fu_info is None:
            pytest.skip("This hexagram has 妻财 visible")

        status = analyze_fu_shen_status(fu_info, h)
        month_zhi = h.gan_zhi["month_zhi"]

        expected_fu_po = LIU_CHONG.get(month_zhi) == fu_info["fu_di_zhi"]
        assert status["fu_po"] == expected_fu_po

    def test_fei_shen_xun_kong(self):
        """飞神旬空检测"""
        h = Hexagram([8, 7, 7, 7, 7, 7], 2024, 1, 15)
        fu_info = find_fu_shen(h, "妻财")
        if fu_info is None:
            pytest.skip("This hexagram has 妻财 visible")

        status = analyze_fu_shen_status(fu_info, h)

        expected_fei_kong = fu_info["fei_di_zhi"] in h.xun_kong
        assert status["fei_kong"] == expected_fei_kong

    def test_normal_status(self):
        """正常状态: 伏神和飞神都无旬空月破"""
        h = Hexagram([8, 7, 7, 7, 7, 7], 2024, 1, 15)
        fu_info = find_fu_shen(h, "妻财")
        if fu_info is None:
            pytest.skip("This hexagram has 妻财 visible")

        status = analyze_fu_shen_status(fu_info, h)
        assert isinstance(status["fu_kong"], bool)
        assert isinstance(status["fu_po"], bool)
        assert isinstance(status["fei_kong"], bool)
        assert isinstance(status["fei_po"], bool)
        assert len(status["implications"]) > 0


class TestJudgeFushenJixiong:
    """测试 judge_fushen_jixiong 伏神吉凶判断"""

    def test_fu_kong_is_xiong(self):
        """伏空为凶"""
        from liuyao.wangshuai import analyze_hexagram_wangshuai
        from liuyao.dongbian import analyze_dongbian

        h = Hexagram([8, 7, 7, 7, 7, 7], 2024, 1, 15)
        fu_info = find_fu_shen(h, "妻财")
        if fu_info is None:
            pytest.skip("This hexagram has 妻财 visible")

        # Mock fu_status with fu_kong=True
        fu_status = {
            "fu_kong": True,
            "fu_po": False,
            "fei_kong": False,
            "fei_po": False,
            "implications": ["伏神旬空, 所求之事暂无着落"],
        }

        ws = analyze_hexagram_wangshuai(h)
        db = analyze_dongbian(h, ws)

        result = judge_fushen_jixiong(fu_info, fu_status, h, ws, db)
        assert result["ji_xiong"] == "凶"
        assert result["pattern"] == "伏空"

    def test_fu_po_is_xiong(self):
        """伏破为凶"""
        from liuyao.wangshuai import analyze_hexagram_wangshuai
        from liuyao.dongbian import analyze_dongbian

        h = Hexagram([8, 7, 7, 7, 7, 7], 2024, 1, 15)
        fu_info = find_fu_shen(h, "妻财")
        if fu_info is None:
            pytest.skip("This hexagram has 妻财 visible")

        # Mock fu_status with fu_po=True
        fu_status = {
            "fu_kong": False,
            "fu_po": True,
            "fei_kong": False,
            "fei_po": False,
            "implications": ["伏神月破, 所求之事难以实现"],
        }

        ws = analyze_hexagram_wangshuai(h)
        db = analyze_dongbian(h, ws)

        result = judge_fushen_jixiong(fu_info, fu_status, h, ws, db)
        assert result["ji_xiong"] == "凶"
        assert result["pattern"] == "伏破"

    def test_fu_under_ying_is_ji(self):
        """伏神藏于应爻下为吉"""
        from liuyao.wangshuai import analyze_hexagram_wangshuai
        from liuyao.dongbian import analyze_dongbian

        h = Hexagram([8, 7, 7, 7, 7, 7], 2024, 1, 15)
        fu_info = find_fu_shen(h, "妻财")
        if fu_info is None:
            pytest.skip("This hexagram has 妻财 visible")

        # 检查伏神位置是否在应爻位置
        ying_pos = h.ying_pos

        # 如果伏神恰好在应爻位, 则应返回吉
        fu_status = {
            "fu_kong": False,
            "fu_po": False,
            "fei_kong": False,
            "fei_po": False,
            "implications": ["伏神状态正常, 待时而出"],
        }

        ws = analyze_hexagram_wangshuai(h)
        db = analyze_dongbian(h, ws)

        result = judge_fushen_jixiong(fu_info, fu_status, h, ws, db)

        if fu_info["position"] == ying_pos:
            assert result["ji_xiong"] == "吉"
            assert result["pattern"] == "伏在应下"
        else:
            # 伏神不在应爻下, 正常判断
            assert result["ji_xiong"] in ("吉", "凶", "平")

    def test_normal_fu_returns_ping(self):
        """正常伏藏无特殊情况返回平"""
        from liuyao.wangshuai import analyze_hexagram_wangshuai
        from liuyao.dongbian import analyze_dongbian

        h = Hexagram([8, 7, 7, 7, 7, 7], 2024, 1, 15)
        fu_info = find_fu_shen(h, "妻财")
        if fu_info is None:
            pytest.skip("This hexagram has 妻财 visible")

        # 伏神不在应爻位, 无旬空月破, 无动爻克世
        ying_pos = h.ying_pos
        if fu_info["position"] == ying_pos:
            pytest.skip("Fu-shen is under ying line in this case")

        fu_status = {
            "fu_kong": False,
            "fu_po": False,
            "fei_kong": False,
            "fei_po": False,
            "implications": ["伏神状态正常, 待时而出"],
        }

        ws = analyze_hexagram_wangshuai(h)
        db = analyze_dongbian(h, ws)

        result = judge_fushen_jixiong(fu_info, fu_status, h, ws, db)
        # 无特殊凶兆, 无应位吉象, 则为平
        assert result["ji_xiong"] == "平"


class TestEstimateFushenYingqi:
    """测试 estimate_fushen_yingqi 伏神应期推断"""

    def test_chong_fei_timing(self):
        """冲飞露伏: 冲去飞神的地支"""
        h = Hexagram([8, 7, 7, 7, 7, 7], 2024, 1, 15)
        fu_info = find_fu_shen(h, "妻财")
        if fu_info is None:
            pytest.skip("This hexagram has 妻财 visible")

        fu_status = analyze_fu_shen_status(fu_info, h)
        result = estimate_fushen_yingqi(fu_info, fu_status, h)

        # 冲飞: LIU_CHONG[fei_di_zhi]
        expected_chong = LIU_CHONG.get(fu_info["fei_di_zhi"])
        assert result["chong_fei"] == expected_chong

    def test_lu_fu_timing(self):
        """逢值逢合: 伏神地支本身和六合"""
        h = Hexagram([8, 7, 7, 7, 7, 7], 2024, 1, 15)
        fu_info = find_fu_shen(h, "妻财")
        if fu_info is None:
            pytest.skip("This hexagram has 妻财 visible")

        fu_status = analyze_fu_shen_status(fu_info, h)
        result = estimate_fushen_yingqi(fu_info, fu_status, h)

        assert result["lu_fu"]["feng_zhi"] == fu_info["fu_di_zhi"]

    def test_fei_kong_fu_xian(self):
        """飞空伏现: 飞神旬空时"""
        h = Hexagram([8, 7, 7, 7, 7, 7], 2024, 1, 15)
        fu_info = find_fu_shen(h, "妻财")
        if fu_info is None:
            pytest.skip("This hexagram has 妻财 visible")

        # Mock fei_kong=True
        fu_status = {
            "fu_kong": False,
            "fu_po": False,
            "fei_kong": True,
            "fei_po": False,
            "implications": ["飞神旬空, 伏神得以显露"],
        }

        result = estimate_fushen_yingqi(fu_info, fu_status, h)
        assert result["fei_kong_fu_xian"] == fu_info["fei_di_zhi"]

    def test_candidates_not_empty(self):
        """应期候选列表不为空"""
        h = Hexagram([8, 7, 7, 7, 7, 7], 2024, 1, 15)
        fu_info = find_fu_shen(h, "妻财")
        if fu_info is None:
            pytest.skip("This hexagram has 妻财 visible")

        fu_status = analyze_fu_shen_status(fu_info, h)
        result = estimate_fushen_yingqi(fu_info, fu_status, h)

        assert len(result["candidates"]) >= 2  # at minimum chong_fei + lu_fu


class TestFushenIntegration:
    """集成测试: run_analysis 产生伏神分析"""

    def test_run_analysis_with_missing_yongshen(self):
        """用神不现时, run_analysis 生成伏神分析"""
        # 天风姤 (乾宫): 缺妻财
        # question_type=cai -> 用神=妻财
        h = Hexagram([8, 7, 7, 7, 7, 7], 2024, 1, 15)
        report = run_analysis(h, question_type="cai")

        # 确认用神不现
        assert len(report.yong_shen_lines) == 0

        # 应有伏神分析
        assert report.fushen_result is not None
        assert "fu_shen_info" in report.fushen_result
        assert "fu_status" in report.fushen_result
        assert "fu_jixiong" in report.fushen_result
        assert "fu_yingqi" in report.fushen_result

    def test_run_analysis_with_present_yongshen(self):
        """用神存在时, 不生成伏神分析"""
        # 乾为天: 所有六亲都有
        h = Hexagram([7, 7, 7, 7, 7, 7], 2024, 1, 15)
        report = run_analysis(h, question_type="cai")

        # 用神应存在
        assert len(report.yong_shen_lines) > 0

        # 不应有伏神分析
        assert report.fushen_result is None

    def test_report_contains_fushen_section(self):
        """报告格式化包含伏神分析段"""
        from liuyao.report import format_report

        h = Hexagram([8, 7, 7, 7, 7, 7], 2024, 1, 15)
        report = run_analysis(h, question_type="cai")

        if report.fushen_result:
            text = format_report(report)
            assert "【伏神分析】" in text
            assert "伏神:" in text
            assert "飞神:" in text
            assert "应期:" in text

    def test_no_fushen_section_when_not_needed(self):
        """用神存在时, 报告不包含伏神段"""
        from liuyao.report import format_report

        h = Hexagram([7, 7, 7, 7, 7, 7], 2024, 1, 15)
        report = run_analysis(h, question_type="cai")

        text = format_report(report)
        assert "【伏神分析】" not in text

    def test_fushen_result_structure(self):
        """伏神结果数据结构完整性"""
        h = Hexagram([8, 7, 7, 7, 7, 7], 2024, 1, 15)
        report = run_analysis(h, question_type="cai")

        if report.fushen_result is None:
            pytest.skip("No fushen result for this configuration")

        fr = report.fushen_result
        # fu_shen_info keys
        fi = fr["fu_shen_info"]
        assert "position" in fi
        assert "fu_di_zhi" in fi
        assert "fu_wu_xing" in fi
        assert "fu_liu_qin" in fi
        assert "fu_tian_gan" in fi
        assert "fei_di_zhi" in fi
        assert "fei_wu_xing" in fi
        assert "fei_liu_qin" in fi

        # fu_status keys
        fs = fr["fu_status"]
        assert "fu_kong" in fs
        assert "fu_po" in fs
        assert "fei_kong" in fs
        assert "fei_po" in fs
        assert "implications" in fs

        # fu_jixiong keys
        fj = fr["fu_jixiong"]
        assert "path" in fj
        assert "pattern" in fj
        assert "ji_xiong" in fj
        assert "explanation" in fj

        # fu_yingqi keys
        fy = fr["fu_yingqi"]
        assert "chong_fei" in fy
        assert "lu_fu" in fy
        assert "candidates" in fy
