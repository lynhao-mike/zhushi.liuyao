"""克中带冲突破金刚型最小回归测试。"""

from liuyao.application.use_cases.analysis import run_analysis
from liuyao.domain.hexagram import Hexagram


def test_keshichong_breaks_gangjing():
    """动爻克中带冲世爻，应触发 P1_KESHICHONG_BREAKS_GANGJING 规则。"""
    h = Hexagram.from_ganzhi(
        [6, 6, 9, 6, 8, 9],
        month_zhi="子", day_zhi="子", day_gan="甲",
    )
    r = run_analysis(h, question_type="other")
    result = r.jixiong_result
    assert result.get("rule_id") == "P1_KESHICHONG_BREAKS_GANGJING"
    assert result.get("ji_xiong") == "凶"
    assert "忌神动克冲世爻" == result.get("pattern", "")
