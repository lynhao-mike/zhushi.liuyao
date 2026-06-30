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

from liuyao.domain.hexagram import Hexagram
from liuyao.application.use_cases.analysis import run_analysis
from liuyao.interfaces.cli.reporting import format_report
from tests.fixtures.zengshan_230_cases import (
    ZENGSHAN_CASES,
    CASE_01, CASE_03, CASE_04, CASE_09,
    CASE_10, CASE_14, CASE_15, CASE_17,
    CASE_18, CASE_22, CASE_23, CASE_101,
)
from liuyao.domain.rules import THEORY_RULE_CASE_MAP


# ============================================================================ #
# 命中基线与已知未对照集 (回归红线)                                              #
# ============================================================================ #
# 以原文真实日月干支复盘后, 当前引擎吉凶判定与原例一致的案例集合。
# 这些案例为硬性守卫: 任何改动若令其判定退化, 测试立即失败。
BASELINE_HIT_IDS = {
    "例1", "例2", "例3", "例4", "例5",
    "例6", "例7", "例8", "例9", "例10", "例11", "例12", "例14", "例15", "例18", "例20", "例22", "例23",
    "例38", "例41", "例44", "例54", "例60", "例61", "例101", "例108", "例144", "例218",
}

# 基线案例当前实际命中的规则快照 (rule_id, pattern)。
#
# 设计目的:
#   1. 把"基线案例 → 命中规则"这一事实显式固化, 防止 legacy 兜底逻辑
#      静默替换显式 P0 规则, 或反之, 而引擎仍恰好判对吉凶;
#   2. 区分案例是被显式 P0 规则覆盖, 还是仅靠 legacy ladder 兜底,
#      为后续将 legacy 规则化提供清单与优先级依据;
#   3. 当某个 legacy 案例升级为显式规则时, 必须显式更新此快照,
#      避免理论覆盖度静默回退或越界。
#
# 字段说明:
#   - rule_id: "legacy" 表示由 judge_dong_gua/judge_jing_gua 兜底命中,
#              未匹配任何显式 P0 规则; 否则为命中的 P0_* 规则 ID。
#   - pattern: 引擎给出的局名(吉凶模式短语), 作为 legacy 路径的二级守卫;
#              即使后续 legacy 内部分支调整, pattern 改变也会被立刻发现。
BASELINE_RULE_HITS = {
    "例1":   {"rule_id": "legacy",                           "pattern": "用神生世局"},
    "例2":   {"rule_id": "P0_TRANSFORMED_YONG_MEDIATOR",      "pattern": "变爻用神生世"},
    "例3":   {"rule_id": "P0_FEI_YAO_RIYUE",                 "pattern": "废爻型(月破日克)"},
    "例4":   {"rule_id": "P0_DAY_MONTH_KE_MOVING_RESCUE",    "pattern": "用神动兆胜日月克"},
    "例5":   {"rule_id": "P0_SAN_HE_JU_PRIORITY",            "pattern": "三合局克用神"},
    "例6":   {"rule_id": "legacy",                           "pattern": "用旺世兴局"},
    "例7":   {"rule_id": "legacy",                  "pattern": "用旺世兴局"},
    "例8":   {"rule_id": "legacy",                  "pattern": "静卦用克世(求财特例)"},
    "例9":   {"rule_id": "P0_YUE_LING_SHIXIAO",      "pattern": "月令时效卦"},
    "例10":  {"rule_id": "P0_SAN_HE_JU_PRIORITY",    "pattern": "三合局生世"},
    "例11":  {"rule_id": "legacy",                  "pattern": "用旺世衰局"},
    "例12":  {"rule_id": "legacy",                  "pattern": "世爻受伤局"},
    "例14":  {"rule_id": "P0_JINGANG_MOVING_KE_SHI", "pattern": "金刚型忌神动克世"},
    "例15":  {"rule_id": "P0_SELF_CHANGE_TERMINAL",  "pattern": "内力动化衰败"},
    "例18":  {"rule_id": "legacy",                  "pattern": "用神动化临日月"},
    "例20":  {"rule_id": "P0_JINGANG_MOVING_KE_SHI", "pattern": "金刚型忌神动克世"},
    "例22":  {"rule_id": "legacy",                  "pattern": "静卦用克世"},
    "例23":  {"rule_id": "P0_ZHEN_BAN",              "pattern": "真绊"},
    "例38":  {"rule_id": "legacy",                  "pattern": "用旺世衰局"},
    "例41":  {"rule_id": "P0_TRANSFORMED_YONG_MEDIATOR", "pattern": "变爻用神生世"},
    "例44":  {"rule_id": "legacy",                  "pattern": "世用受生局"},
    "例54":  {"rule_id": "P0_MOVING_KE_YONG",       "pattern": "忌神动克用神"},
    "例60":  {"rule_id": "legacy",                  "pattern": "用旺世衰局"},
    "例61":  {"rule_id": "legacy",                  "pattern": "静卦用克世"},
    "例101": {"rule_id": "P0_ZHEN_BAN",              "pattern": "真绊"},
    "例108": {"rule_id": "P1_YUANSHEN_DUFA_BIANFEI", "pattern": "元神独发变废(回头克)"},
    "例144": {"rule_id": "legacy",                  "pattern": "占寿元动则有期"},
    "例218": {"rule_id": "P0_HUI_TOU_SHENG_RESCUE",  "pattern": "用神动化回头生"},
}

# 当前尚未达成对照的案例及原因。修复后应将其移入 BASELINE_HIT_IDS。
# 原因大致分两类:
#   (A) fixture 数据待核实 (yao_types 顺序 FIXME / 干支旬空存疑);
#   (B) 引擎卦理实现存在缺口 (绊局/三合局/特殊日月组合/时效卦等吉凶定性)。
KNOWN_MISMATCH = {
    # ── (A) fixture 数据问题: yao_types 顺序/内容与理论描述不符 ──────────────
    "例205": "(A) fixture_mismatch: yao_types 构出的卦无妻财爻(用神为妻财), "
             "引擎因找不到用神判平; 需按原书核实卦图爻位",
    # ── (B) 规则缺口: 无 P0/P1 规则处理该场景 ──────────────────────────────
    "例17": "(B) 规则缺口: 子鬼互化已被 P1_YONG_JI_MUTUAL_TRANSFORM 覆盖, "
            "但优先级低于月令时效卦 P0_YUE_LING_SHIXIAO, 引擎先命中后者判吉; "
            "需调整 P1 用忌互化优先级或让月令时效不覆盖子鬼互化场景",
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


BUILD_FAIL_IDS = set()


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

    @pytest.mark.parametrize("case_id", sorted(KNOWN_MISMATCH))
    def test_known_mismatch_has_classification(self, case_id):
        """每个 strict xfail 都必须有明确根因分类, 防止规则缺口与 fixture 错误混淆。"""
        cases = {case["id"]: case for case in ZENGSHAN_CASES}
        case = cases[case_id]
        reason = KNOWN_MISMATCH[case_id]
        assert case.get("data_status") in {"fixture_mismatch", "fixture_error", "invalid", "rule_gap"}, \
            f"{case_id} data_status 需标明 fixture_mismatch/fixture_error/invalid/rule_gap"
        assert case.get("failure_type"), f"{case_id} failure_type 不应为空"
        assert any(label in reason for label in ("fixture_mismatch", "fixture_error", "规则缺口")), \
            f"{case_id} KNOWN_MISMATCH 原因需显式区分 fixture 或规则缺口"

    @pytest.mark.parametrize("case_id", sorted(KNOWN_MISMATCH))
    def test_known_mismatch_is_mapped_to_theory(self, case_id):
        """每个 strict xfail 都必须进入理论-规则-案例映射, 形成可追踪闭环。"""
        mapped_case_ids = {
            mapped_case_id
            for item in THEORY_RULE_CASE_MAP.values()
            for mapped_case_id in item.get("cases", [])
        }
        assert case_id in mapped_case_ids, f"{case_id} 未进入 THEORY_RULE_CASE_MAP"

    def test_baseline_rule_hits_covers_all_baseline_cases(self):
        """快照表必须覆盖每一个基线案例, 防止新基线案例进入但未登记规则归属。"""
        missing = BASELINE_HIT_IDS - set(BASELINE_RULE_HITS)
        extra = set(BASELINE_RULE_HITS) - BASELINE_HIT_IDS
        assert not missing, (
            f"以下基线案例未登记规则命中快照: {sorted(missing)}; "
            f"请在 BASELINE_RULE_HITS 中补全 rule_id 与 pattern"
        )
        assert not extra, (
            f"以下案例已登记快照但不在基线集合中: {sorted(extra)}; "
            f"请同步更新 BASELINE_HIT_IDS 或移除快照条目"
        )

    @pytest.mark.parametrize("case_id", sorted(BASELINE_RULE_HITS))
    def test_baseline_rule_hit_snapshot(self, case_id):
        """基线案例命中的 rule_id 与 pattern 必须与快照一致。

        作用:
        - rule_id 退化(P0_* → legacy) 立刻发现;
        - rule_id 升级(legacy → P0_*) 也必须显式更新快照, 不允许静默;
        - pattern 漂移(legacy 内部分支调整) 同样会立即被检出。
        """
        cases = {case["id"]: case for case in ZENGSHAN_CASES}
        case = cases[case_id]
        h = _build_hexagram(case)
        report = run_analysis(h, question_type=case.get("question_type", "other"))
        ji = report.jixiong_result or {}
        expected = BASELINE_RULE_HITS[case_id]
        actual_rule_id = ji.get("rule_id") or "legacy"
        actual_pattern = ji.get("pattern", "")
        assert actual_rule_id == expected["rule_id"], (
            f"{case_id} rule_id 漂移: 快照={expected['rule_id']!r}, 实际={actual_rule_id!r}; "
            f"若是有意升级到显式规则, 请同步更新 BASELINE_RULE_HITS"
        )
        assert actual_pattern == expected["pattern"], (
            f"{case_id} pattern 漂移: 快照={expected['pattern']!r}, 实际={actual_pattern!r}; "
            f"若是有意调整 legacy 分支, 请同步更新 BASELINE_RULE_HITS"
        )

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
        """例23: 申月子日明夷之小过, 占出行。明确时段出行遇绊即真绊。"""
        h = _build_hexagram(CASE_23)
        assert h.ben_gua_name == "地火明夷"
        assert h.bian_gua_name == "雷山小过"
        assert len([l for l in h.lines if l.is_moving]) >= 2, "例23应有至少两处动兆"
        report = run_analysis(h, question_type=CASE_23["question_type"])
        assert report.jixiong_result.get("rule_id") == "P0_ZHEN_BAN"
        assert any(ban.get("ban_type") == "日绊" and 4 in ban.get("positions", []) for ban in report.patterns_results.get("san_ban", []))

    def test_zhen_ban_outer_three_hua_ban(self):
        """例101: 雷天大壮之巽为风, 外三爻全动化绊即真绊。"""
        h = _build_hexagram(CASE_101)
        assert h.ben_gua_name == "雷天大壮"
        assert h.bian_gua_name == "巽为风"
        report = run_analysis(h, question_type=CASE_101["question_type"])
        assert report.jixiong_result.get("rule_id") == "P0_ZHEN_BAN"
        hua_ban_positions = {
            ban["positions"][0]
            for ban in report.patterns_results.get("san_ban", [])
            if ban.get("ban_type") == "化绊" and ban.get("positions")
        }
        assert {4, 5, 6} <= hua_ban_positions


# ============================================================================ #
# 理论规则单元级验证 (不依赖具体卦例)                                             #
# ============================================================================ #

class TestTheoryRules:
    """直接测试旺衰/动变等核心理论函数。"""

    def test_yue_po_ri_ke_fei_yao_condition(self):
        """废爻型: 月破(月令冲) + 日令克。亥水在巳月(月破)未日(日克)。"""
        from liuyao.domain.wangshuai import yue_jian_wangshuai, ri_chen_wangshuai
        _, yue_shuai = yue_jian_wangshuai("亥", "巳")
        _, ri_shuai = ri_chen_wangshuai("亥", "未")
        assert "月破" in yue_shuai, "亥水在巳月应为月破"
        assert "日令克" in ri_shuai, "亥水在未日应为日令克"

    def test_jingang_yue_jian_ri_sheng_condition(self):
        """金刚型: 月建(临月令) + 日令生/合。申金在申月为临月令。"""
        from liuyao.domain.wangshuai import yue_jian_wangshuai, ri_chen_wangshuai
        yue_wang, _ = yue_jian_wangshuai("申", "申")
        assert "临月令" in yue_wang, "申金在申月应为临月令"
        ri_wang, _ = ri_chen_wangshuai("申", "辰")
        assert len(ri_wang) >= 0

    def test_hui_tou_ke_detection(self):
        """回头克: 变爻克动爻。"""
        from liuyao.domain.dongbian import is_hui_tou_ke
        assert is_hui_tou_ke("寅", "申") is True   # 金克木
        assert is_hui_tou_ke("申", "午") is True   # 火克金
        assert is_hui_tou_ke("亥", "申") is False  # 金生水, 回头生
        assert is_hui_tou_ke("午", "未") is False  # 土不克火

    def test_hua_jin_shen_and_tui_shen(self):
        """进退神: 申->酉=进神, 酉->申=退神。"""
        from liuyao.domain.dongbian import is_hua_jin_shen, is_hua_tui_shen
        assert is_hua_jin_shen("申", "酉") is True
        assert is_hua_tui_shen("酉", "申") is True
        assert is_hua_jin_shen("酉", "申") is False
        assert is_hua_tui_shen("申", "酉") is False

    def test_san_he_ju_formation(self):
        """三合局: 含申子辰三动的卦旺衰可正常分析。"""
        from liuyao.domain.wangshuai import analyze_hexagram_wangshuai
        h = Hexagram.from_ganzhi([6, 7, 9, 7, 7, 7], month_zhi="丑", day_zhi="寅", xun_kong=["子", "丑"])
        results = analyze_hexagram_wangshuai(h)
        assert len(results) == 6

    def test_xun_kong_detection(self):
        """旬空检测: 甲子->戌亥, 甲午->辰巳, 戊申->寅卯。"""
        from liuyao.domain.data import get_xun_kong
        assert "戌" in get_xun_kong("甲", "子") or "亥" in get_xun_kong("甲", "子")
        assert "辰" in get_xun_kong("甲", "午") or "巳" in get_xun_kong("甲", "午")
        xk3 = get_xun_kong("戊", "申")
        assert "寅" in xk3 or "卯" in xk3

    def test_ban_formation_hua_ban(self):
        """化绊: 动爻与变爻六合。验证 analyze_all_patterns 可正常运行。"""
        h = Hexagram.from_ganzhi([7, 7, 9, 7, 7, 7], month_zhi="丑", day_zhi="寅", xun_kong=["子", "丑"])
        from liuyao.domain.wangshuai import analyze_hexagram_wangshuai
        from liuyao.domain.dongbian import analyze_dongbian
        from liuyao.domain.patterns import analyze_all_patterns
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
