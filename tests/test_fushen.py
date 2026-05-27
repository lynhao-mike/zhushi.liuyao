"""
伏神(藏伏)系统测试 - Fu Shen / Cang Yao System Tests

验证《古筮真诠》第三十九章理论实现的正确性。
"""

import pytest
from liuyao.hexagram import Hexagram, CangYao
from liuyao.fushen import (
    find_fu_shen,
    determine_fei_fu_relation,
    evaluate_fushen_jixiong,
    fushen_yingqi,
    analyze_fushen,
)
from liuyao.analyzer import run_analysis


# =============================================================================
# 藏爻计算测试
# =============================================================================

def test_cang_yao_count():
    """藏爻必有 6 个"""
    h = Hexagram([7, 7, 7, 8, 8, 8], 2024, 9, 29)  # 地天泰
    assert len(h.cang_yao) == 6
    for i, c in enumerate(h.cang_yao):
        assert isinstance(c, CangYao)
        assert c.position == i + 1


def test_cang_yao_坤宫():
    """坤宫地天泰: 藏爻应为坤为地各爻 (未巳卯丑亥酉)"""
    h = Hexagram([7, 7, 7, 8, 8, 8], 2024, 9, 29)
    assert h.palace_name == "坤"
    expected_zhi = ["未", "巳", "卯", "丑", "亥", "酉"]
    for i, expected in enumerate(expected_zhi):
        assert h.cang_yao[i].di_zhi == expected, (
            f"位置{i+1}: 期望{expected}, 实际{h.cang_yao[i].di_zhi}"
        )


def test_cang_yao_乾宫():
    """乾宫天风姤(一世): 藏爻应为乾为天各爻 (子寅辰午申戌)"""
    # 天风姤 = 上乾下巽 = 巽(0,1,1)+乾(1,1,1)
    h = Hexagram([8, 7, 7, 7, 7, 7], 2024, 9, 29)
    assert h.palace_name == "乾"
    expected_zhi = ["子", "寅", "辰", "午", "申", "戌"]
    for i, expected in enumerate(expected_zhi):
        assert h.cang_yao[i].di_zhi == expected


def test_cang_yao_liu_qin_consistent():
    """藏爻的六亲应基于本宫五行计算"""
    h = Hexagram([7, 7, 7, 8, 8, 8], 2024, 9, 29)  # 坤宫
    # 坤五行=土, 第2爻巳火: 火生土, 应为父母
    cang_2 = h.cang_yao[1]
    assert cang_2.di_zhi == "巳"
    assert cang_2.wu_xing == "火"
    assert cang_2.liu_qin == "父母"


def test_cang_yao_xun_kong():
    """藏爻地支若在旬空内, 标记为旬空"""
    # 2024-09-29 = 丙申日 = 甲午旬, 旬空辰巳
    h = Hexagram([7, 7, 7, 8, 8, 8], 2024, 9, 29)
    assert h.xun_kong == ("辰", "巳")
    # 第2爻藏爻 = 巳火, 应在旬空中
    assert h.cang_yao[1].di_zhi == "巳"
    assert h.cang_yao[1].is_xun_kong == True


# =============================================================================
# 伏神查找测试
# =============================================================================

def test_find_fushen_when_yongshen_in_main():
    """用神在主卦中存在时, 不应找伏神"""
    h = Hexagram([7, 7, 7, 8, 8, 8], 2024, 9, 29)  # 地天泰, 坤宫
    # 妻财在主卦第1爻(子)和第5爻(亥)中存在
    result = find_fu_shen(h, "妻财")
    assert result is None


def test_find_fushen_when_yongshen_missing():
    """用神在主卦不存在时, 从藏爻取伏神"""
    h = Hexagram([7, 7, 7, 8, 8, 8], 2024, 9, 29)  # 地天泰, 坤宫
    # 主卦无父母爻, 应从藏爻取伏神 (巳火, 第2爻)
    result = find_fu_shen(h, "父母")
    assert result is not None
    assert result["position"] == 2
    assert result["fu_di_zhi"] == "巳"
    assert result["fu_wu_xing"] == "火"
    assert result["fei_di_zhi"] == "寅"
    assert result["fei_wu_xing"] == "木"


# =============================================================================
# 飞伏关系测试 (5种)
# =============================================================================

def test_feifu_relation_克():
    assert determine_fei_fu_relation("木", "土") == "飞神克伏神"
    assert determine_fei_fu_relation("土", "木") == "伏神克飞神"


def test_feifu_relation_生():
    assert determine_fei_fu_relation("木", "火") == "飞神生伏神"
    assert determine_fei_fu_relation("火", "木") == "伏神生飞神"


def test_feifu_relation_比和():
    assert determine_fei_fu_relation("木", "木") == "飞伏比和"


def test_feifu_relation_长生_例():
    """《古筮真诠》经典: 父母巳火伏于二爻寅木下 = 飞神生伏神(长生)"""
    h = Hexagram([7, 7, 7, 8, 8, 8], 2024, 9, 29)
    fi = find_fu_shen(h, "父母")
    rel = determine_fei_fu_relation(fi["fei_wu_xing"], fi["fu_wu_xing"])
    assert rel == "飞神生伏神"  # 木生火


# =============================================================================
# 伏神吉凶判断测试
# =============================================================================

def test_fushen_伏空():
    """《古筮真诠》经典案例: 丙申日占文书 - 伏神巳火逢旬空 = 凶"""
    h = Hexagram([7, 7, 7, 8, 8, 8], 2024, 9, 29)  # 丙申日
    fa = analyze_fushen(h, "父母", [
        {"overall": "平", "month_shuai": [], "day_shuai": [], "details": ""}
        for _ in range(6)
    ], {"moving_analyses": {}, "interactions": {}}, "kaoshi")
    assert fa is not None
    rules = [e["rule"] for e in fa["jixiong_evaluations"]]
    assert "伏空" in rules
    fu_kong_eval = next(e for e in fa["jixiong_evaluations"] if e["rule"] == "伏空")
    assert fu_kong_eval["result"] == "凶"


# =============================================================================
# 伏神应期测试
# =============================================================================

def test_fushen_yingqi_冲飞():
    """伏神应期应包含冲飞 (冲走飞神之时)"""
    h = Hexagram([7, 7, 7, 8, 8, 8], 2024, 9, 29)
    fi = find_fu_shen(h, "父母")
    candidates = fushen_yingqi(fi)
    # 飞神是寅, 应期应有冲寅 = 申
    chong_yingqi = [c for c in candidates if "冲飞" in c]
    assert len(chong_yingqi) > 0
    assert "申" in chong_yingqi[0]


def test_fushen_yingqi_露伏():
    """伏神应期应包含露伏 (伏神逢值/逢合)"""
    h = Hexagram([7, 7, 7, 8, 8, 8], 2024, 9, 29)
    fi = find_fu_shen(h, "父母")
    candidates = fushen_yingqi(fi)
    # 伏神是巳, 应期应有逢值巳, 逢合申
    lu_yingqi = [c for c in candidates if "露伏" in c]
    assert len(lu_yingqi) >= 2


# =============================================================================
# 端到端集成测试
# =============================================================================

def test_run_analysis_with_fushen():
    """run_analysis 在用神不上卦时, 应自动启用伏神分析"""
    h = Hexagram([7, 7, 7, 8, 8, 8], 2024, 9, 29)  # 坤宫地天泰
    report = run_analysis(h, question_type="kaoshi")  # 用神=父母
    assert report.yong_shen_liu_qin == "父母"
    assert len(report.yong_shen_lines) == 0  # 父母不在主卦
    assert report.fushen_analysis is not None
    fi = report.fushen_analysis["fushen_info"]
    assert fi["fu_di_zhi"] == "巳"


def test_run_analysis_no_fushen_when_yong_in_main():
    """用神在主卦时, 不应启用伏神分析"""
    h = Hexagram([7, 7, 7, 8, 8, 8], 2024, 9, 29)
    report = run_analysis(h, question_type="cai")  # 用神=妻财, 在主卦中
    assert len(report.yong_shen_lines) > 0
    assert report.fushen_analysis is None
