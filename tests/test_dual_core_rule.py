"""双核卦象最小主判规则测试。"""

from liuyao.application.use_cases.analysis import run_analysis
from liuyao.domain.hexagram import Hexagram


def test_dual_core_designated_target_rule_marks_non_committal_when_ying_moves_without_linking_shi_or_yong():
    """应爻自发动但不承接世/用时，不应把普通成局直接等同于指定对象成立。"""
    hexagram = Hexagram.from_ganzhi(
        [7, 8, 7, 9, 7, 8],
        month_zhi="卯",
        day_zhi="巳",
        day_gan="乙",
        xun_kong=["寅", "卯"],
    )
    report = run_analysis(hexagram, question_type="other", yong_shen_override="妻财")
    result = report.jixiong_result
    if result.get("rule_id") == "P1_DUAL_CORE_DESIGNATED_TARGET":
        assert result["pattern"] == "双核卦象(指定对象未承局)"
        assert result["ji_xiong"] == "平"
        assert result.get("evidence")
        first = result["evidence"][0]
        assert first["decision_path"] == "dual_core_designated_target_minimal_guard"
        assert "普通用旺/用神生世只说明事情可成, 不等于指定对象可成" in first["counter_signals"]
