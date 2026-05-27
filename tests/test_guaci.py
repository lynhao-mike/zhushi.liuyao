"""
卦辞寓意模块测试 - Tests for Gua-Ci Yu-Yi Module
"""

import pytest
from liuyao.hexagram import Hexagram
from liuyao.wangshuai import analyze_hexagram_wangshuai
from liuyao.dongbian import analyze_dongbian
from liuyao.jixiong import judge_jixiong, determine_yong_shen, find_yong_shen_lines
from liuyao.guaci import (
    GUA_CI_YUYI,
    get_guaci_interpretation,
    analyze_liuchong_gua,
    analyze_liuhe_gua,
    get_bian_gua_guidance,
    detect_gua_fanyin_fuyin,
    analyze_guaci,
    _is_liuchong_gua,
    _is_liuhe_gua,
)
from liuyao.analyzer import run_analysis


class TestGuaCiYuyi:
    """测试卦辞寓意字典覆盖率"""

    def test_all_64_hexagrams_covered(self):
        """所有64卦都有卦辞寓意"""
        assert len(GUA_CI_YUYI) == 64

    def test_key_hexagram_qian(self):
        """乾为天: 启始, 刚健"""
        entry = GUA_CI_YUYI["乾为天"]
        assert "启始" in entry["keywords"]
        assert "刚健" in entry["keywords"]
        assert entry["polarity"] == "positive"

    def test_key_hexagram_kun(self):
        """坤为地: 包容, 承载"""
        entry = GUA_CI_YUYI["坤为地"]
        assert "包容" in entry["keywords"]
        assert "承载" in entry["keywords"]
        assert entry["polarity"] == "positive"

    def test_key_hexagram_kan(self):
        """坎为水: 陷入, 凹进"""
        entry = GUA_CI_YUYI["坎为水"]
        assert "陷入" in entry["keywords"]
        assert entry["polarity"] == "negative"

    def test_key_hexagram_li(self):
        """离为火: 艳丽, 显露"""
        entry = GUA_CI_YUYI["离为火"]
        assert "艳丽" in entry["keywords"]
        assert entry["polarity"] == "neutral"

    def test_key_hexagram_zhen(self):
        """震为雷: 动态, 出行"""
        entry = GUA_CI_YUYI["震为雷"]
        assert "动态" in entry["keywords"]
        assert entry["polarity"] == "neutral"

    def test_key_hexagram_xun(self):
        """巽为风: 诚信, 跟风"""
        entry = GUA_CI_YUYI["巽为风"]
        assert "诚信" in entry["keywords"]
        assert entry["polarity"] == "neutral"

    def test_key_hexagram_gen(self):
        """艮为山: 阻停, 堆积"""
        entry = GUA_CI_YUYI["艮为山"]
        assert "阻停" in entry["keywords"]
        assert entry["polarity"] == "negative"

    def test_key_hexagram_dui(self):
        """兑为泽: 言谈, 争讼"""
        entry = GUA_CI_YUYI["兑为泽"]
        assert "言谈" in entry["keywords"]
        assert entry["polarity"] == "neutral"

    def test_key_hexagram_pi(self):
        """天地否: 闭塞, 受阻"""
        entry = GUA_CI_YUYI["天地否"]
        assert "闭塞" in entry["keywords"]
        assert entry["polarity"] == "negative"

    def test_key_hexagram_tai(self):
        """地天泰: 安泰, 通畅"""
        entry = GUA_CI_YUYI["地天泰"]
        assert "安泰" in entry["keywords"]
        assert entry["polarity"] == "positive"

    def test_key_hexagram_xu(self):
        """水天需: 等待, 静观"""
        entry = GUA_CI_YUYI["水天需"]
        assert "等待" in entry["keywords"]
        assert "静观" in entry["guidance"]

    def test_key_hexagram_shi(self):
        """地水师: 深入, 追究"""
        entry = GUA_CI_YUYI["地水师"]
        assert "深入" in entry["keywords"]
        assert "深入" in entry["guidance"]

    def test_key_hexagram_guan(self):
        """风地观: 观察, 留意"""
        entry = GUA_CI_YUYI["风地观"]
        assert "观察" in entry["keywords"]
        assert "观察" in entry["guidance"]

    def test_key_hexagram_jiaren(self):
        """风火家人: 守家, 护财"""
        entry = GUA_CI_YUYI["风火家人"]
        assert "守家" in entry["keywords"]
        assert "钱袋" in entry["guidance"]

    def test_key_hexagram_daguo(self):
        """泽风大过: 过度, 超限"""
        entry = GUA_CI_YUYI["泽风大过"]
        assert "过度" in entry["keywords"]
        assert entry["polarity"] == "negative"

    def test_key_hexagram_mingyi(self):
        """地火明夷: 晦暗, 受伤"""
        entry = GUA_CI_YUYI["地火明夷"]
        assert "晦暗" in entry["keywords"]
        assert entry["polarity"] == "negative"

    def test_key_hexagram_heng(self):
        """雷风恒: 恒久, 持续"""
        entry = GUA_CI_YUYI["雷风恒"]
        assert "恒久" in entry["keywords"]
        assert entry["polarity"] == "positive"

    def test_key_hexagram_jian(self):
        """风山渐: 渐进, 稳步"""
        entry = GUA_CI_YUYI["风山渐"]
        assert "渐进" in entry["keywords"]
        assert entry["polarity"] == "positive"

    def test_get_guaci_interpretation_xu(self):
        """get_guaci_interpretation 对水天需返回等待/静观"""
        result = get_guaci_interpretation("水天需", "cai")
        assert result is not None
        assert "等待" in result["keywords"]

    def test_get_guaci_interpretation_unknown(self):
        """未知卦名返回None"""
        result = get_guaci_interpretation("不存在的卦")
        assert result is None

    def test_all_entries_have_required_keys(self):
        """所有条目都具备必要字段"""
        for name, entry in GUA_CI_YUYI.items():
            assert "keywords" in entry, f"{name} missing keywords"
            assert "guidance" in entry, f"{name} missing guidance"
            assert "polarity" in entry, f"{name} missing polarity"
            assert entry["polarity"] in ("positive", "negative", "neutral"), \
                f"{name} has invalid polarity: {entry['polarity']}"
            assert len(entry["keywords"]) >= 2, f"{name} has too few keywords"


class TestLiuChongGua:
    """测试六冲卦检测"""

    def test_qian_is_liuchong(self):
        """乾为天是六冲卦"""
        assert _is_liuchong_gua("乾为天") is True

    def test_kun_is_liuchong(self):
        """坤为地是六冲卦"""
        assert _is_liuchong_gua("坤为地") is True

    def test_kan_is_liuchong(self):
        """坎为水是六冲卦"""
        assert _is_liuchong_gua("坎为水") is True

    def test_li_is_liuchong(self):
        """离为火是六冲卦"""
        assert _is_liuchong_gua("离为火") is True

    def test_zhen_is_liuchong(self):
        """震为雷是六冲卦"""
        assert _is_liuchong_gua("震为雷") is True

    def test_xun_is_liuchong(self):
        """巽为风是六冲卦"""
        assert _is_liuchong_gua("巽为风") is True

    def test_gen_is_liuchong(self):
        """艮为山是六冲卦"""
        assert _is_liuchong_gua("艮为山") is True

    def test_dui_is_liuchong(self):
        """兑为泽是六冲卦"""
        assert _is_liuchong_gua("兑为泽") is True

    def test_non_liuchong(self):
        """非纯卦不是六冲卦"""
        assert _is_liuchong_gua("天地否") is False
        assert _is_liuchong_gua("地天泰") is False

    def test_analyze_liuchong_ben_is_liuchong(self):
        """本卦为六冲卦的分析"""
        result = analyze_liuchong_gua("乾为天", "天风姤")
        assert result["ben_is_liuchong"] is True
        assert result["bian_is_liuchong"] is False
        assert result["liuchong_gua"] == "乾为天"
        assert result["implications"]["short_term"] != ""

    def test_analyze_liuchong_bian_is_liuchong(self):
        """变卦为六冲卦的分析"""
        result = analyze_liuchong_gua("天风姤", "乾为天")
        assert result["ben_is_liuchong"] is False
        assert result["bian_is_liuchong"] is True
        assert result["liuchong_gua"] == "乾为天"

    def test_analyze_liuchong_neither(self):
        """两卦都不是六冲卦"""
        result = analyze_liuchong_gua("天风姤", "天地否")
        assert result["ben_is_liuchong"] is False
        assert result["bian_is_liuchong"] is False
        assert result["liuchong_gua"] is None

    def test_chong_bian_he_pattern(self):
        """六冲变六合模式: 本卦六冲, 变卦六合"""
        # 找一个六合卦
        # 地天泰是六合卦
        result = analyze_liuchong_gua("乾为天", "地天泰")
        assert result["special_pattern"] == "chong_bian_he"
        assert "破后复合" in result["implications"]["short_term"]

    def test_he_bian_chong_pattern(self):
        """六合变六冲模式: 本卦六合, 变卦六冲"""
        result = analyze_liuchong_gua("地天泰", "乾为天")
        assert result["special_pattern"] == "he_bian_chong"
        assert "合后散离" in result["implications"]["short_term"]


class TestLiuHeGua:
    """测试六合卦检测"""

    def test_tai_is_liuhe(self):
        """地天泰是六合卦"""
        assert _is_liuhe_gua("地天泰") is True

    def test_pi_is_liuhe(self):
        """天地否是六合卦"""
        assert _is_liuhe_gua("天地否") is True

    def test_pure_gua_not_liuhe(self):
        """纯卦(六冲)不是六合卦"""
        assert _is_liuhe_gua("乾为天") is False
        assert _is_liuhe_gua("坤为地") is False

    def test_analyze_liuhe_ben_is_liuhe(self):
        """本卦为六合卦的分析"""
        result = analyze_liuhe_gua("地天泰", "天风姤")
        assert result["ben_is_liuhe"] is True
        assert result["implications"]["short_term"] != ""

    def test_analyze_liuhe_negative_gua(self):
        """负面含义的六合卦"""
        result = analyze_liuhe_gua("天地否", "天风姤")
        assert result["ben_is_liuhe"] is True
        assert "困" in result["implications"]["short_term"] or "纠缠" in result["implications"]["short_term"]

    def test_analyze_liuhe_he_bian_chong(self):
        """六合变六冲模式"""
        result = analyze_liuhe_gua("地天泰", "乾为天")
        assert result["special_pattern"] == "he_bian_chong"
        assert "散离" in result["implications"]["short_term"]

    def test_analyze_liuhe_chong_bian_he(self):
        """六冲变六合模式 (从六合角度)"""
        result = analyze_liuhe_gua("乾为天", "地天泰")
        assert result["special_pattern"] == "chong_bian_he"
        assert "复合" in result["implications"]["short_term"]

    def test_analyze_liuhe_neither(self):
        """两卦都不是六合卦"""
        result = analyze_liuhe_gua("天风姤", "天山遁")
        assert result["ben_is_liuhe"] is False
        assert result["bian_is_liuhe"] is False


class TestBianGuaGuidance:
    """测试变卦指导建议"""

    def test_ji_returns_none(self):
        """吉不提供指导"""
        h = Hexagram([7, 7, 7, 7, 7, 7], 2024, 1, 15)
        jixiong = {"ji_xiong": "吉", "pattern": "test", "explanation": "test"}
        dongbian = {}
        result = get_bian_gua_guidance(h, jixiong, dongbian)
        assert result is None

    def test_xiong_liuhe_guidance(self):
        """凶 + 变卦六合: 暂缓搁置"""
        # 地天泰是六合卦, 构造变卦为地天泰的情况
        # 坤为地[8,8,8,8,8,8] -> 变卦需要是地天泰
        # 用[6,6,6,8,8,8]: 初三爻动(老阴), 上三爻静(少阴)
        # 本卦: 下坤(000)上坤(000)=坤为地
        # 变: 下乾(111)上坤(000)=地天泰? No, 上坤下乾=地天泰
        # [6,6,6,8,8,8]: ben=(0,0,0,0,0,0) bian=(1,1,1,0,0,0)
        # ben: lower=(0,0,0)=坤 upper=(0,0,0)=坤 -> 坤为地
        # bian: lower=(1,1,1)=乾 upper=(0,0,0)=坤 -> (坤,乾)=地天泰
        h = Hexagram([6, 6, 6, 8, 8, 8], 2024, 1, 15)
        assert h.bian_gua_name == "地天泰"
        jixiong = {"ji_xiong": "凶", "pattern": "test", "explanation": "test"}
        dongbian = {}
        result = get_bian_gua_guidance(h, jixiong, dongbian)
        assert result == "卦变六合, 宜暂缓搁置, 不宜急进"

    def test_xiong_liuchong_guidance(self):
        """凶 + 变卦六冲: 中止放弃"""
        # 构造变卦为乾为天的情况
        # [8,8,8,6,6,6]: ben=(0,0,0,0,0,0) bian=(0,0,0,1,1,1)
        # ben: lower=坤 upper=坤 -> 坤为地
        # bian: lower=坤(0,0,0) upper=乾(1,1,1) -> (乾,坤)=天地否 (NOT 乾为天)
        # Need both upper and lower to be same for liuchong
        # [6,6,6,6,6,6]: ben=(0,0,0,0,0,0) bian=(1,1,1,1,1,1) = 乾为天
        h = Hexagram([6, 6, 6, 6, 6, 6], 2024, 1, 15)
        assert h.bian_gua_name == "乾为天"
        jixiong = {"ji_xiong": "凶", "pattern": "test", "explanation": "test"}
        dongbian = {}
        result = get_bian_gua_guidance(h, jixiong, dongbian)
        assert result == "卦变六冲, 宜中止放弃, 不宜继续"

    def test_ping_returns_guidance_from_guaci(self):
        """平时返回变卦的卦辞指导"""
        h = Hexagram([7, 7, 7, 7, 7, 7], 2024, 1, 15)
        # 乾为天 静卦 - 变卦也是乾为天
        jixiong = {"ji_xiong": "平", "pattern": "test", "explanation": "test"}
        dongbian = {}
        result = get_bian_gua_guidance(h, jixiong, dongbian)
        # 乾为天的guidance: "宜主动进取, 刚健有力"
        assert result is not None
        assert "进取" in result


class TestFanYinFuYin:
    """测试反吟/伏吟检测"""

    def test_fuyin_static_gua(self):
        """静卦: 本卦=变卦, 伏吟"""
        h = Hexagram([7, 7, 7, 7, 7, 7], 2024, 1, 15)
        result = detect_gua_fanyin_fuyin(h)
        assert result["fu_yin"] is True
        assert result["fan_yin"] is False
        assert "停滞" in result["implications"]

    def test_fanyin_gua_level(self):
        """卦级反吟: 上下卦分别对冲"""
        # 需要本卦上下卦分别对冲变卦上下卦
        # 乾<->坤, 所以 乾为天(乾乾) fanyin -> 坤为地(坤坤)
        # [9,9,9,9,9,9]: ben=(1,1,1,1,1,1)=乾为天, bian=(0,0,0,0,0,0)=坤为地
        h = Hexagram([9, 9, 9, 9, 9, 9], 2024, 1, 15)
        assert h.ben_gua_name == "乾为天"
        assert h.bian_gua_name == "坤为地"
        result = detect_gua_fanyin_fuyin(h)
        assert result["fan_yin"] is True
        assert result["fan_yin_type"] == "gua"
        assert "反复" in result["implications"]

    def test_no_fanyin_no_fuyin(self):
        """无反吟无伏吟的普通变卦"""
        # 天风姤: ben=乾为天变到天风姤 (只有初爻动)
        # [9,7,7,7,7,7]: ben lower=(1,1,1)=乾 upper=(1,1,1)=乾 -> 乾为天
        # bian lower=(0,1,1)=巽 upper=(1,1,1)=乾 -> (乾,巽)=天风姤
        h = Hexagram([9, 7, 7, 7, 7, 7], 2024, 1, 15)
        assert h.ben_gua_name == "乾为天"
        assert h.bian_gua_name == "天风姤"
        result = detect_gua_fanyin_fuyin(h)
        assert result["fan_yin"] is False
        assert result["fu_yin"] is False

    def test_fanyin_zhen_xun(self):
        """震巽对冲: 震为雷 -> 巽为风"""
        # 震=(1,0,0), 巽=(0,1,1)
        # 震为雷: lower=震(1,0,0) upper=震(1,0,0) -> values [9,8,8,9,8,8]? No.
        # ben_lines = [1,0,0,1,0,0] -> lower=(1,0,0)=震, upper=(1,0,0)=震 -> 震为雷
        # bian要变成巽为风: (0,1,1,0,1,1) -> all flip
        # For all lines to flip: yao_values all 动
        # pos 1: ben=1(阳), need bian=0 -> old yang(9)
        # pos 2: ben=0(阴), need bian=1 -> old yin(6)
        # pos 3: ben=0(阴), need bian=1 -> old yin(6)
        # pos 4: ben=1(阳), need bian=0 -> old yang(9)
        # pos 5: ben=0(阴), need bian=1 -> old yin(6)
        # pos 6: ben=0(阴), need bian=1 -> old yin(6)
        h = Hexagram([9, 6, 6, 9, 6, 6], 2024, 1, 15)
        assert h.ben_gua_name == "震为雷"
        assert h.bian_gua_name == "巽为风"
        result = detect_gua_fanyin_fuyin(h)
        assert result["fan_yin"] is True
        assert result["fan_yin_type"] == "gua"


class TestAnalyzeGuaci:
    """测试综合分析入口"""

    def test_full_analysis_structure(self):
        """完整分析返回正确结构"""
        h = Hexagram([9, 7, 7, 7, 7, 7], 2024, 1, 15)
        ws = analyze_hexagram_wangshuai(h)
        db = analyze_dongbian(h, ws)
        yong_shen = determine_yong_shen("cai")
        yong_lines = find_yong_shen_lines(h, yong_shen)
        jx = judge_jixiong(h, yong_shen, ws, db, "cai")

        result = analyze_guaci(h, jx, db)
        assert "guaci_interpretation" in result
        assert "liuchong" in result
        assert "liuhe" in result
        assert "guidance" in result
        assert "fanyin_fuyin" in result

    def test_integration_with_pipeline(self):
        """集成到分析流水线"""
        h = Hexagram([8, 7, 7, 9, 7, 8], 2024, 1, 15)
        report = run_analysis(h, "cai")
        assert report.guaci_result is not None
        assert "liuchong" in report.guaci_result
        assert "liuhe" in report.guaci_result

    def test_integration_pipeline_static(self):
        """静卦的流水线集成"""
        h = Hexagram([7, 7, 7, 7, 7, 7], 2024, 1, 15)
        report = run_analysis(h, "guan")
        assert report.guaci_result is not None
        # 静卦应检测到伏吟
        assert report.guaci_result["fanyin_fuyin"]["fu_yin"] is True

    def test_report_format_includes_guaci(self):
        """报告格式包含卦辞寓意部分"""
        from liuyao.report import format_report
        h = Hexagram([8, 7, 7, 9, 7, 8], 2024, 1, 15)
        report = run_analysis(h, "cai")
        text = format_report(report)
        assert "【卦辞寓意】" in text
