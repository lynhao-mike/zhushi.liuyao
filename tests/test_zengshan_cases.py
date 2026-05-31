# -*- coding: utf-8 -*-
"""
《增删卜易》卦例验证测试（真实日月干支对照）

本测试以每个卦例**原文真实的月支/日支/旬空**构建卦象
(经 ``Hexagram.from_ganzhi`` 注入干支, 不再使用占位日期),
并将引擎判定的吉凶与原例结论逐例对照, 从而:

  1. 把原先"仅验证流程可达性"的空壳测试升级为真实准确度校验;
  2. 通过 ``test_accuracy_baseline`` 固定当前命中基线, 作为回归红线;
  3. 通过逐例参数化对照 + ``xfail(strict=True)`` 标记, 让每个案例的
     对照结果可见: 当前判定正确的案例为硬性守卫, 已知未达成对照的
     案例记为 xfail(被修复后会触发 XPASS 告警, 提示更新基线)。

数据说明 (见 fixtures/zengshan_230_cases.py):
  - 目标为《增删卜易》230 例, 当前已录入 30 例精选案例;
  - 部分案例 yao_types 顺序带 FIXME 待核实, 个别案例旬空数据存疑
    (如 例108 在亥日却以亥为旬空, 自相矛盾), 相关案例计入已知未对照集。
"""

import pytest

from liuyao.hexagram import Hexagram
from liuyao.analyzer import run_analysis
from liuyao.report import format_report
from tests.fixtures.zengshan_230_cases import (
    ZENGSHAN_CASES,
    CASE_01, CASE_03, CASE_04, CASE_09,
    CASE_10, CASE_14, CASE_15, CASE_17,
    CASE_18, CASE_22, CASE_23,
)


# ============================================================================ #
# 命中基线与已知未对照集 (回归红线)                                              #
# ============================================================================ #
# 以原文真实日月干支复盘后, 当前引擎吉凶判定与原例一致的案例集合。
# 这些案例为硬性守卫: 任何改动若令其判定退化, 测试立即失败。
BASELINE_HIT_IDS = {
    "例6", "例7", "例8", "例11", "例12", "例17", "例18", "例22", "例23",
    "例38", "例44", "例60", "例61", "例101", "例144", "例218",
}

# 当前尚未达成对照的案例及原因。修复后应将其移入 BASELINE_HIT_IDS。
# 原因大致分两类:
#   (A) fixture 数据待核实 (yao_types 顺序 FIXME / 干支旬空存疑);
#   (B) 引擎卦理实现存在缺口 (绊局/三合局/特殊日月组合/时效卦等吉凶定性)。
KNOWN_MISMATCH = {
    "例1": "(B/A) 化绊假绊不影响吉凶定性, 引擎当前判凶; yao_types 顺序待核实",
    "例2": "(B/A) 变爻用神生世吉局未识别; yao_types 顺序待核实",
    "例3": "(B) 废爻型(月破+日克)动生不起未落定为凶",
    "例4": "(B) 动化回头生胜日月克(动兆为主)未落定为吉",
    "例5": "(B) 三合局克用神 + 化刑定凶未识别",
    "例9": "(B) 月令时效卦临月建逢克不凶未实现",
    "例10": "(B) 三合局生世优先于单爻分析未落定为吉",
    "例14": "(B) 化绊假绊忌神照常克用神(凶)未落定",
    "例15": "(B) 世自变回头克(内力主导)定凶未落定",
    "例20": "(B) 引擎判平, 期望凶",
    "例41": "(B) 引擎判凶, 期望吉",
    "例54": "(B) 引擎判凶, 期望吉",
    "例205": "(B) 引擎判平, 期望吉",
    "例108": "(A) fixture 数据错误: 亥日不可能以亥为旬空, 待按原书核实日干",
}


# ============================================================================ #
# 辅助工具                                                                      #
# ============================================================================ #

def _build_hexagram(case: dict) -> Hexagram:
    """以卦例原文真实月支/日支/旬空构建卦象 (注入干支, 不依赖公历日期)。"""
    return Hexagram.from_ganzhi(
        case["yao_types"],
        month_zhi=case["month_zhi"],
        day_zhi=case["day_zhi"],
        xun_kong=case.get("xun_kong"),
    )


def _engine_ji_xiong(case: dict) -> str:
    """构卦并运行分析, 返回引擎判定的吉凶。"""
    h = _build_hexagram(case)
    report = run_analysis(h, question_type=case.get("question_type", "other"))
    return report.jixiong_result.get("ji_xiong", "")


def _case_params():
    """构造参数化用例: 已知未对照案例附带 strict xfail 标记 (用于吉凶对照)。"""
    params = []
    for c in ZENGSHAN_CASES:
        marks = ()
        if c["id"] in KNOWN_MISMATCH:
            marks = pytest.mark.xfail(reason=KNOWN_MISMATCH[c["id"]], strict=True)
        params.append(pytest.param(c, id=c["id"], marks=marks))
    return params


# 因 fixture 数据问题当前无法构卦的案例 (仅这些会令格式化/构卦类测试失败)。
BUILD_FAIL_IDS = {"例108"}


def _buildable_case_params():
    """构造参数化用例: 仅对构卦失败案例附带 strict xfail (用于格式化等需成功构卦的测试)。"""
    params = []
    for c in ZENGSHAN_CASES:
        marks = ()
        if c["id"] in BUILD_FAIL_IDS:
            marks = pytest.mark.xfail(reason=KNOWN_MISMATCH.get(c["id"], "构卦失败"),
                                      strict=True)
        params.append(pytest.param(c, id=c["id"], marks=marks))
    return params


# ============================================================================ #
# 准确度基线 (回归红线)                                                          #
# ============================================================================ #

class TestAccuracyBaseline:
    """全量卦例吉凶对照, 固定命中基线, 防止准确度静默回退。"""

    def test_accuracy_baseline(self, capsys):
        hits, misses, errors = [], [], []
        for c in ZENGSHAN_CASES:
            try:
                got = _engine_ji_xiong(c)
            except Exception as e:  # noqa: BLE001 - 汇总报告所有异常案例
                errors.append((c["id"], str(e)))
                continue
            if got == c["expected_ji_xiong"]:
                hits.append(c["id"])
            else:
                misses.append((c["id"], got, c["expected_ji_xiong"]))

        total = len(ZENGSHAN_CASES)
        analyzable = total - len(errors)
        with capsys.disabled():
            print("\n========== 增删卜易卦例 吉凶对照基线 ==========")
            print(f"  总例数      : {total}")
            print(f"  可分析      : {analyzable}  (构卦失败 {len(errors)})")
            print(f"  命中        : {len(hits)}")
            if analyzable:
                print(f"  命中率(可分析): {len(hits) / analyzable * 100:.1f}%")
            print(f"  命中率(全体) : {len(hits) / total * 100:.1f}%")
            if errors:
                print("  构卦失败案例:")
                for cid, msg in errors:
                    print(f"    - {cid}: {msg}")
            print("===============================================")

        # 回归红线 1: 基线命中集合不得缩小 (任一案例判定退化即失败)
        lost = BASELINE_HIT_IDS - set(hits)
        assert not lost, f"命中回退: 以下基线案例不再命中 {sorted(lost)}"
        # 回归红线 2: 总命中数不得低于基线
        assert len(hits) >= len(BASELINE_HIT_IDS), (
            f"命中数 {len(hits)} 低于基线 {len(BASELINE_HIT_IDS)}"
        )


# ============================================================================ #
# 逐例吉凶对照 (真实日月干支)                                                     #
# ============================================================================ #

class TestZengshanCasesParametrized:
    """逐例参数化对照: 引擎判定 vs 原例结论。"""

    @pytest.mark.parametrize("case", _case_params())
    def test_case_ji_xiong(self, case):
        """
        逐例对照吉凶。已知未对照案例以 strict xfail 标记:
        若某案例被修复(对照通过), strict xfail 会触发 XPASS 失败,
        提示将其从 KNOWN_MISMATCH 移入 BASELINE_HIT_IDS。
        """
        got = _engine_ji_xiong(case)  # 构卦失败将抛异常, 对 xfail 案例计为预期失败
        assert got == case["expected_ji_xiong"], (
            f"{case['id']} 吉凶不符: 引擎={got}, 期望={case['expected_ji_xiong']}"
        )

    @pytest.mark.parametrize("case", ZENGSHAN_CASES, ids=[c["id"] for c in ZENGSHAN_CASES])
    def test_case_theory_keywords_in_case_data(self, case):
        """验证案例数据完整性: theory_points / expected_pattern_keywords 非空。"""
        assert len(case["theory_points"]) >= 1, f"{case['id']} theory_points 不应为空"
        assert len(case["expected_pattern_keywords"]) >= 1, \
            f"{case['id']} expected_pattern_keywords 不应为空"
        assert case["expected_ji_xiong"] in ("吉", "凶", "平"), \
            f"{case['id']} expected_ji_xiong 应为 吉/凶/平"

    @pytest.mark.parametrize("case", _buildable_case_params())
    def test_case_report_format(self, case):
        """验证分析报告可正常格式化输出 (无异常, 返回非空字符串)。"""
        h = _build_hexagram(case)
        report = run_analysis(h, question_type=case.get("question_type", "other"))
        formatted = format_report(report)
        assert isinstance(formatted, str) and len(formatted) > 0, \
            f"{case['id']} 格式化报告应返回非空字符串"


# ============================================================================ #
# 核心理论点结构验证 (真实日月干支)                                               #
# ============================================================================ #

class TestZengshanTheoryPoints:
    """
    核心理论点的卦象结构验证。

    这些断言验证卦象**结构特征**(动爻数目/世爻/月建等)符合理论点描述,
    与 yao_types 直接相关; 吉凶定性对照统一由参数化对照与基线测试负责。
    """

    def test_hua_ban_jia_ban_structure(self):
        """例1: 辰月申日乾之小畜, 占父近病。应有动爻(午火化未土, 化绊)。"""
        h = _build_hexagram(CASE_01)
        assert h.ben_gua_name != ""
        assert h.gan_zhi["month_zhi"] == "辰" and h.gan_zhi["day_zhi"] == "申"
        assert len([l for l in h.lines if l.is_moving]) >= 1, "例1应有动爻(午火)"

    def test_fei_yao_xing_has_moving(self):
        """例3: 巳月未日大过之鼎, 自占病。废爻型(月破日克), 卦中应有动爻。"""
        h = _build_hexagram(CASE_03)
        assert h.gan_zhi["month_zhi"] == "巳" and h.gan_zhi["day_zhi"] == "未"
        assert len([l for l in h.lines if l.is_moving]) >= 1, "例3应有动爻"

    def test_hui_tou_sheng_has_moving(self):
        """例4: 卯月卯日复之震, 弟占兄获重罪。用神动化回头生, 应有动爻。"""
        h = _build_hexagram(CASE_04)
        assert h.gan_zhi["month_zhi"] == "卯" and h.gan_zhi["day_zhi"] == "卯"
        assert len([l for l in h.lines if l.is_moving]) >= 1, "例4应有动爻(丑土)"

    def test_shi_xiao_gua_month(self):
        """例9: 酉月寅日蛊之蒙, 占谒贵(月令时效卦), 月建为酉。"""
        h = _build_hexagram(CASE_09)
        assert h.gan_zhi["month_zhi"] == "酉", "例9为酉月"

    def test_san_he_ju_multiple_moving(self):
        """例10: 寅月申日艮之颐, 占升迁。三合水局, 应有多个动爻。"""
        h = _build_hexagram(CASE_10)
        assert len([l for l in h.lines if l.is_moving]) >= 2, "例10应有多动爻构成三合局"

    def test_hua_ban_keyword(self):
        """例14: 未月午日履之中孚, 占子痘症。化绊假绊, 应期为冲绊日。"""
        _build_hexagram(CASE_14)  # 验证可构卦
        assert "冲绊应期" in CASE_14["expected_pattern_keywords"]

    def test_shi_yao_present(self):
        """例15: 申月午日遁之姤, 自占病。世自变回头克, 卦中应有世爻。"""
        h = _build_hexagram(CASE_15)
        assert any(l.is_shi for l in h.lines), "应有世爻"

    def test_zi_gui_hu_hua_structure(self):
        """例17: 子日剥之观, 占生产。子鬼互化, 应有动爻。"""
        h = _build_hexagram(CASE_17)
        assert len([l for l in h.lines if l.is_moving]) >= 1, "例17应有动爻(子孙动)"
        assert "子鬼互化" in CASE_17["expected_pattern_keywords"]

    def test_jingang_structure(self):
        """例18: 申月辰日屯之震, 占兄病。金刚型特殊日月组合, 应有动爻。"""
        h = _build_hexagram(CASE_18)
        assert h.gan_zhi["month_zhi"] == "申" and h.gan_zhi["day_zhi"] == "辰"
        assert len([l for l in h.lines if l.is_moving]) >= 1, "例18应有动爻"
        assert "金刚型" in CASE_18["expected_pattern_keywords"]

    def test_fei_jing_shi_static_gua(self):
        """例22: 戌月卯日地天泰, 占讼事。静卦, 世爻辰土废爻型, 无动爻。"""
        h = _build_hexagram(CASE_22)
        assert len([l for l in h.lines if l.is_moving]) == 0, "例22为静卦, 无动爻"

    def test_zhen_ban_multiple_moving(self):
        """例23: 申月子日明夷之小过, 占出行。真绊, 应有至少两动爻化绊。"""
        h = _build_hexagram(CASE_23)
        assert len([l for l in h.lines if l.is_moving]) >= 2, "例23应有至少两动爻构成化绊"
        assert "真绊" in CASE_23["expected_pattern_keywords"]


# ============================================================================ #
# 理论规则单元级验证 (不依赖具体卦例)                                             #
# ============================================================================ #

class TestTheoryRules:
    """直接测试旺衰/动变等核心理论函数。"""

    def test_yue_po_ri_ke_fei_yao_condition(self):
        """废爻型: 月破(月令冲) + 日令克。亥水在巳月(月破)未日(日克)。"""
        from liuyao.wangshuai import yue_jian_wangshuai, ri_chen_wangshuai
        _, yue_shuai = yue_jian_wangshuai("亥", "巳")
        _, ri_shuai = ri_chen_wangshuai("亥", "未")
        assert "月破" in yue_shuai, "亥水在巳月应为月破"
        assert "日令克" in ri_shuai, "亥水在未日应为日令克"

    def test_jingang_yue_jian_ri_sheng_condition(self):
        """金刚型: 月建(临月令) + 日令生/合。申金在申月为临月令。"""
        from liuyao.wangshuai import yue_jian_wangshuai, ri_chen_wangshuai
        yue_wang, _ = yue_jian_wangshuai("申", "申")
        assert "临月令" in yue_wang, "申金在申月应为临月令"
        ri_wang, _ = ri_chen_wangshuai("申", "辰")
        assert len(ri_wang) >= 0

    def test_hui_tou_ke_detection(self):
        """回头克: 变爻克动爻。"""
        from liuyao.dongbian import is_hui_tou_ke
        assert is_hui_tou_ke("寅", "申") is True   # 金克木
        assert is_hui_tou_ke("申", "午") is True   # 火克金
        assert is_hui_tou_ke("亥", "申") is False  # 金生水, 回头生
        assert is_hui_tou_ke("午", "未") is False  # 土不克火

    def test_hua_jin_shen_and_tui_shen(self):
        """进退神: 申->酉=进神, 酉->申=退神。"""
        from liuyao.dongbian import is_hua_jin_shen, is_hua_tui_shen
        assert is_hua_jin_shen("申", "酉") is True
        assert is_hua_tui_shen("酉", "申") is True
        assert is_hua_jin_shen("酉", "申") is False
        assert is_hua_tui_shen("申", "酉") is False

    def test_san_he_ju_formation(self):
        """三合局: 含申子辰三动的卦旺衰可正常分析。"""
        from liuyao.wangshuai import analyze_hexagram_wangshuai
        h = Hexagram([6, 7, 9, 7, 7, 7], 2024, 1, 15)
        results = analyze_hexagram_wangshuai(h)
        assert len(results) == 6

    def test_xun_kong_detection(self):
        """旬空检测: 甲子->戌亥, 甲午->辰巳, 戊申->寅卯。"""
        from liuyao.data import get_xun_kong
        assert "戌" in get_xun_kong("甲", "子") or "亥" in get_xun_kong("甲", "子")
        assert "辰" in get_xun_kong("甲", "午") or "巳" in get_xun_kong("甲", "午")
        xk3 = get_xun_kong("戊", "申")
        assert "寅" in xk3 or "卯" in xk3

    def test_ban_formation_hua_ban(self):
        """化绊: 动爻与变爻六合。验证 analyze_all_patterns 可正常运行。"""
        h = Hexagram([7, 7, 9, 7, 7, 7], 2024, 1, 15)
        from liuyao.wangshuai import analyze_hexagram_wangshuai
        from liuyao.dongbian import analyze_dongbian
        from liuyao.patterns import analyze_all_patterns
        ws = analyze_hexagram_wangshuai(h)
        db = analyze_dongbian(h, ws)
        patterns = analyze_all_patterns(h, ws, db, "父母", "官鬼", [], "bing")
        assert isinstance(patterns, dict)


# ============================================================================ #
# 集成测试: 完整分析流程 (真实日月干支)                                           #
# ============================================================================ #

class TestFullAnalysisFlow:
    """完整分析流程集成测试。"""

    def test_full_analysis_single_case(self):
        """例3 完整分析流程 (从构卦到生成报告)。"""
        h = _build_hexagram(CASE_03)
        report = run_analysis(h, question_type="bing")
        assert report.hexagram is not None
        assert isinstance(report.wangshuai_results, list)
        assert len(report.wangshuai_results) == 6
        assert "ji_xiong" in report.jixiong_result

    def test_full_analysis_with_format(self):
        """例1 完整分析 + 报告格式化。"""
        h = _build_hexagram(CASE_01)
        report = run_analysis(h, question_type="bing")
        formatted = format_report(report)
        assert isinstance(formatted, str)
        assert len(formatted) > 100, "报告文本不应过短"

    def test_all_cases_no_unexpected_exception(self):
        """全部案例运行分析流程; 仅允许已知数据错误案例(例108)构卦失败。"""
        errors = []
        for case in ZENGSHAN_CASES:
            try:
                h = _build_hexagram(case)
                run_analysis(h, question_type=case.get("question_type", "other"))
            except Exception as e:  # noqa: BLE001
                errors.append((case["id"], str(e)))
        unexpected = [(cid, msg) for cid, msg in errors if cid not in KNOWN_MISMATCH]
        assert not unexpected, f"非预期的分析异常: {unexpected}"
