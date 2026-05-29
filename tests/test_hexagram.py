"""
六爻排卦系统测试 - Tests for Liu Yao Hexagram System
"""

import pytest
from liuyao.data import (
    NA_JIA, DI_ZHI_WU_XING, HEXAGRAM_BY_TRIGRAMS, HEXAGRAM_BY_NAME,
    PALACE_SHI_YING, get_liu_qin, get_liu_shen, get_xun_kong,
    WU_XING_SHENG, WU_XING_KE,
)
from liuyao.calendar_utils import get_gan_zhi
from liuyao.hexagram import Hexagram


class TestNaJia:
    """测试纳甲分配"""

    def test_qian_na_jia(self):
        """乾卦纳甲: 甲子寅辰/甲午申戌"""
        gan, inner, outer = NA_JIA["乾"]
        assert gan == "甲"
        assert inner == ["子", "寅", "辰"]
        assert outer == ["午", "申", "戌"]

    def test_kun_na_jia(self):
        """坤卦纳甲: 乙未巳卯/乙丑亥酉"""
        gan, inner, outer = NA_JIA["坤"]
        assert gan == "乙"
        assert inner == ["未", "巳", "卯"]
        assert outer == ["丑", "亥", "酉"]

    def test_kan_na_jia(self):
        """坎卦纳甲: 戊寅辰午/戊申戌子"""
        gan, inner, outer = NA_JIA["坎"]
        assert gan == "戊"
        assert inner == ["寅", "辰", "午"]
        assert outer == ["申", "戌", "子"]

    def test_li_na_jia(self):
        """离卦纳甲: 己卯丑亥/己酉未巳"""
        gan, inner, outer = NA_JIA["离"]
        assert gan == "己"
        assert inner == ["卯", "丑", "亥"]
        assert outer == ["酉", "未", "巳"]


class TestPalaceLookup:
    """测试64卦宫位查询"""

    def test_pure_hexagrams(self):
        """八纯卦应在对应宫的第0位"""
        pure_gua = [
            ("乾", "乾", "乾为天"),
            ("坤", "坤", "坤为地"),
            ("震", "震", "震为雷"),
            ("巽", "巽", "巽为风"),
            ("坎", "坎", "坎为水"),
            ("离", "离", "离为火"),
            ("艮", "艮", "艮为山"),
            ("兑", "兑", "兑为泽"),
        ]
        for upper, lower, name in pure_gua:
            info = HEXAGRAM_BY_TRIGRAMS[(upper, lower)]
            assert info["name"] == name
            assert info["palace"] == upper
            assert info["palace_order"] == 0

    def test_total_hexagrams(self):
        """总共应有64卦"""
        assert len(HEXAGRAM_BY_TRIGRAMS) == 64
        assert len(HEXAGRAM_BY_NAME) == 64

    def test_qian_palace_hexagrams(self):
        """乾宫8卦"""
        expected = [
            ("乾", "乾", "乾为天"),
            ("乾", "巽", "天风姤"),
            ("乾", "艮", "天山遁"),
            ("乾", "坤", "天地否"),
            ("巽", "坤", "风地观"),
            ("艮", "坤", "山地剥"),
            ("离", "坤", "火地晋"),
            ("离", "乾", "火天大有"),
        ]
        for upper, lower, name in expected:
            info = HEXAGRAM_BY_TRIGRAMS[(upper, lower)]
            assert info["name"] == name
            assert info["palace"] == "乾"

    def test_kun_palace_hexagrams(self):
        """坤宫8卦"""
        expected = [
            ("坤", "坤", "坤为地"),
            ("坤", "震", "地雷复"),
            ("坤", "兑", "地泽临"),
            ("坤", "乾", "地天泰"),
            ("震", "乾", "雷天大壮"),
            ("兑", "乾", "泽天夬"),
            ("坎", "乾", "水天需"),
            ("坎", "坤", "水地比"),
        ]
        for upper, lower, name in expected:
            info = HEXAGRAM_BY_TRIGRAMS[(upper, lower)]
            assert info["name"] == name
            assert info["palace"] == "坤"


class TestShiYing:
    """测试世应位置"""

    def test_pure_hexagram_shi_ying(self):
        """纯卦: 世在6, 应在3"""
        assert PALACE_SHI_YING[0] == (6, 3)

    def test_yi_shi_gua(self):
        """一世卦: 世在1, 应在4"""
        assert PALACE_SHI_YING[1] == (1, 4)

    def test_you_hun_gua(self):
        """游魂卦: 世在4, 应在1"""
        assert PALACE_SHI_YING[6] == (4, 1)

    def test_gui_hun_gua(self):
        """归魂卦: 世在3, 应在6"""
        assert PALACE_SHI_YING[7] == (3, 6)

    def test_qian_gua_shi_at_6(self):
        """乾为天(纯卦)世爻在第6爻"""
        h = Hexagram([7, 7, 7, 7, 7, 7], 2024, 1, 15)
        assert h.shi_pos == 6
        assert h.ying_pos == 3


class TestCalendar:
    """测试干支历法转换"""

    def test_2024_jan_15(self):
        """2024年1月15日: 癸卯年乙丑月戊寅日 (立春前仍为癸卯年)"""
        gz = get_gan_zhi(2024, 1, 15)
        assert gz["year_gan"] == "癸"
        assert gz["year_zhi"] == "卯"
        assert gz["month_gan"] == "乙"
        assert gz["month_zhi"] == "丑"
        assert gz["day_gan"] == "戊"
        assert gz["day_zhi"] == "寅"

    def test_2024_feb_4_after_lichun(self):
        """2024年2月4日立春后应为甲辰年"""
        gz = get_gan_zhi(2024, 2, 5)
        assert gz["year_gan"] == "甲"
        assert gz["year_zhi"] == "辰"

    def test_month_branch_before_lichun(self):
        """立春前月支为丑月"""
        gz = get_gan_zhi(2024, 1, 15)
        assert gz["month_zhi"] == "丑"


class TestLiuQin:
    """测试六亲计算"""

    def test_same_element(self):
        """同我者为兄弟"""
        assert get_liu_qin("金", "金") == "兄弟"

    def test_wo_sheng(self):
        """我生者为子孙 (金生水)"""
        assert get_liu_qin("金", "水") == "子孙"

    def test_sheng_wo(self):
        """生我者为父母 (土生金)"""
        assert get_liu_qin("金", "土") == "父母"

    def test_wo_ke(self):
        """我克者为妻财 (金克木)"""
        assert get_liu_qin("金", "木") == "妻财"

    def test_ke_wo(self):
        """克我者为官鬼 (火克金)"""
        assert get_liu_qin("金", "火") == "官鬼"


class TestLiuShen:
    """测试六神分配"""

    def test_jia_yi_day(self):
        """甲乙日起青龙"""
        shen = get_liu_shen("甲")
        assert shen[0] == "青龙"
        assert shen[5] == "玄武"

    def test_bing_ding_day(self):
        """丙丁日起朱雀"""
        shen = get_liu_shen("丙")
        assert shen[0] == "朱雀"
        assert shen[5] == "青龙"

    def test_wu_day(self):
        """戊日起勾陈"""
        shen = get_liu_shen("戊")
        assert shen[0] == "勾陈"

    def test_ji_day(self):
        """己日起螣蛇"""
        shen = get_liu_shen("己")
        assert shen[0] == "螣蛇"

    def test_geng_xin_day(self):
        """庚辛日起白虎"""
        shen = get_liu_shen("庚")
        assert shen[0] == "白虎"

    def test_ren_gui_day(self):
        """壬癸日起玄武"""
        shen = get_liu_shen("壬")
        assert shen[0] == "玄武"


class TestXunKong:
    """测试旬空计算"""

    def test_jia_zi_xun(self):
        """甲子旬空戌亥"""
        assert get_xun_kong("甲", "子") == ("戌", "亥")

    def test_jia_xu_xun(self):
        """甲戌旬空申酉"""
        assert get_xun_kong("甲", "戌") == ("申", "酉")

    def test_jia_shen_xun(self):
        """甲申旬空午未"""
        assert get_xun_kong("甲", "申") == ("午", "未")

    def test_jia_wu_xun(self):
        """甲午旬空辰巳"""
        assert get_xun_kong("甲", "午") == ("辰", "巳")

    def test_jia_chen_xun(self):
        """甲辰旬空寅卯"""
        assert get_xun_kong("甲", "辰") == ("寅", "卯")

    def test_jia_yin_xun(self):
        """甲寅旬空子丑"""
        assert get_xun_kong("甲", "寅") == ("子", "丑")

    def test_wu_yin_day(self):
        """戊寅日属甲戌旬, 空申酉"""
        assert get_xun_kong("戊", "寅") == ("申", "酉")


class TestHexagramArrangement:
    """测试完整排卦流程"""

    def test_basic_arrangement(self):
        """测试基本排卦: [8,7,7,9,7,8] 2024-01-15"""
        h = Hexagram([8, 7, 7, 9, 7, 8], 2024, 1, 15)
        assert h.ben_gua_name == "泽风大过"
        assert h.palace_name == "震"
        assert h.palace_wu_xing == "木"
        assert h.bian_gua_name == "水风井"

    def test_moving_line_detection(self):
        """老阳(9)和老阴(6)为动爻"""
        h = Hexagram([6, 7, 8, 9, 7, 8], 2024, 1, 15)
        moving = [l for l in h.lines if l.is_moving]
        assert len(moving) == 2
        assert moving[0].position == 1
        assert moving[1].position == 4

    def test_bian_gua_generation(self):
        """动爻变化生成变卦"""
        # 乾为天, 全动 -> 坤为地
        h = Hexagram([9, 9, 9, 9, 9, 9], 2024, 1, 15)
        assert h.ben_gua_name == "乾为天"
        assert h.bian_gua_name == "坤为地"

    def test_all_yin_static(self):
        """全阴静 -> 坤为地, 无变卦"""
        h = Hexagram([8, 8, 8, 8, 8, 8], 2024, 1, 15)
        assert h.ben_gua_name == "坤为地"
        assert h.bian_gua_name == "坤为地"  # 无动爻, 变卦等于本卦

    def test_qian_gua_na_jia(self):
        """乾为天纳甲验证: 甲子,甲寅,甲辰,甲午,甲申,甲戌"""
        h = Hexagram([7, 7, 7, 7, 7, 7], 2024, 1, 15)
        expected_zhi = ["子", "寅", "辰", "午", "申", "戌"]
        for i, line in enumerate(h.lines):
            assert line.tian_gan == "甲"
            assert line.di_zhi == expected_zhi[i]

    def test_qian_gua_liu_qin(self):
        """乾为天六亲: 乾宫金, 子水=子孙, 寅木=妻财, 辰土=父母, 午火=官鬼, 申金=兄弟, 戌土=父母"""
        h = Hexagram([7, 7, 7, 7, 7, 7], 2024, 1, 15)
        expected_lq = ["子孙", "妻财", "父母", "官鬼", "兄弟", "父母"]
        for i, line in enumerate(h.lines):
            assert line.liu_qin == expected_lq[i], \
                f"Line {i+1}: expected {expected_lq[i]}, got {line.liu_qin}"

    def test_shi_ying_marking(self):
        """验证世应标记正确"""
        # 乾为天 (纯卦): 世6应3
        h = Hexagram([7, 7, 7, 7, 7, 7], 2024, 1, 15)
        shi_line = [l for l in h.lines if l.is_shi][0]
        ying_line = [l for l in h.lines if l.is_ying][0]
        assert shi_line.position == 6
        assert ying_line.position == 3

    def test_xun_kong_marking(self):
        """验证旬空标记: 戊寅日空申酉"""
        h = Hexagram([7, 7, 7, 7, 7, 7], 2024, 1, 15)
        # 乾卦: 申在第5爻
        assert h.lines[4].di_zhi == "申"
        assert h.lines[4].is_xun_kong is True
        # 戌在第6爻, 不空
        assert h.lines[5].di_zhi == "戌"
        assert h.lines[5].is_xun_kong is False

    def test_liu_shen_assignment(self):
        """2024-01-15 戊日起勾陈"""
        h = Hexagram([8, 7, 7, 9, 7, 8], 2024, 1, 15)
        assert h.lines[0].liu_shen == "勾陈"
        assert h.lines[1].liu_shen == "螣蛇"
        assert h.lines[2].liu_shen == "白虎"
        assert h.lines[3].liu_shen == "玄武"
        assert h.lines[4].liu_shen == "青龙"
        assert h.lines[5].liu_shen == "朱雀"

    def test_display_runs_without_error(self):
        """display()方法不报错"""
        h = Hexagram([8, 7, 7, 9, 7, 8], 2024, 1, 15)
        # Just ensure it doesn't raise
        h.display()



class TestGanZhiInjection:
    """测试干支注入 (Hexagram.from_ganzhi / derive_day_gan)。"""

    def test_derive_day_gan_basic(self):
        """由日支 + 旬空唯一反推日干。"""
        from liuyao.calendar_utils import derive_day_gan
        # 甲辰旬(空寅卯): 戊申
        assert derive_day_gan("申", ["寅", "卯"]) == "戊"
        # 甲子旬(空戌亥): 甲子
        assert derive_day_gan("子", ["戌", "亥"]) == "甲"
        # 甲午旬(空辰巳): 乙未
        assert derive_day_gan("未", ["辰", "巳"]) == "乙"
        # 甲寅旬(空子丑): 癸亥
        assert derive_day_gan("亥", ["子", "丑"]) == "癸"

    def test_derive_day_gan_invalid(self):
        """矛盾/非法的日支旬空组合应报错。"""
        from liuyao.calendar_utils import derive_day_gan
        from liuyao.exceptions import CalendarError
        # 日支不可能落在自身旬空内
        with pytest.raises(CalendarError):
            derive_day_gan("亥", ["戌", "亥"])
        with pytest.raises(CalendarError):
            derive_day_gan("无", ["子", "丑"])

    def test_from_ganzhi_injects_month_and_day(self):
        """from_ganzhi 注入的月支/日支应进入 gan_zhi, 供旺衰使用。"""
        h = Hexagram.from_ganzhi(
            [7, 7, 9, 7, 7, 7],
            month_zhi="辰", day_zhi="申", xun_kong=["寅", "卯"],
        )
        assert h.gan_zhi["month_zhi"] == "辰"
        assert h.gan_zhi["day_zhi"] == "申"
        assert h.gan_zhi["day_gan"] == "戊"   # 由旬空反推
        assert h.xun_kong == ("寅", "卯")
        assert h.ben_gua_name == "乾为天"
        assert len(h.lines) == 6

    def test_from_ganzhi_explicit_day_gan(self):
        """显式提供 day_gan 时直接采用, 旬空按其计算。"""
        h = Hexagram.from_ganzhi(
            [7, 8, 7, 8, 7, 8],
            month_zhi="子", day_zhi="子", day_gan="甲",
        )
        assert h.gan_zhi["day_gan"] == "甲"
        assert h.gan_zhi["day_zhi"] == "子"
        # 甲子日旬空为戌亥
        assert set(h.xun_kong) == {"戌", "亥"}

    def test_from_ganzhi_requires_day_gan_or_xunkong(self):
        """既无 day_gan 又无 xun_kong 应报错。"""
        from liuyao.exceptions import ArrangementError
        with pytest.raises(ArrangementError):
            Hexagram.from_ganzhi([7, 7, 7, 7, 7, 7], month_zhi="子", day_zhi="午")

    def test_from_ganzhi_matches_gregorian(self):
        """注入干支与等价公历日期构卦, 旺衰相关字段应一致。"""
        from liuyao.calendar_utils import get_gan_zhi
        # 取一个真实公历日期的干支, 再用其月支/日支/日干注入, 结果应等价
        gz = get_gan_zhi(2024, 1, 15)
        h_greg = Hexagram([8, 7, 7, 9, 7, 8], 2024, 1, 15)
        h_inj = Hexagram.from_ganzhi(
            [8, 7, 7, 9, 7, 8],
            month_zhi=gz["month_zhi"], day_zhi=gz["day_zhi"], day_gan=gz["day_gan"],
        )
        assert h_inj.gan_zhi["month_zhi"] == h_greg.gan_zhi["month_zhi"]
        assert h_inj.gan_zhi["day_zhi"] == h_greg.gan_zhi["day_zhi"]
        assert h_inj.xun_kong == h_greg.xun_kong
        assert h_inj.ben_gua_name == h_greg.ben_gua_name

    def test_backward_compatible_gregorian_constructor(self):
        """原公历构造方式保持可用 (向后兼容)。"""
        h = Hexagram([8, 7, 7, 9, 7, 8], 2024, 1, 15)
        assert h.ben_gua_name != ""
        assert h.gan_zhi["month_zhi"] and h.gan_zhi["day_zhi"]
