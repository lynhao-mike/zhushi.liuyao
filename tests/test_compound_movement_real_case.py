# -*- coding: utf-8 -*-
"""复合之动真实古籍案例回归。"""

from liuyao.application.use_cases.analysis import run_analysis
from liuyao.domain.hexagram import Hexagram
from tests.fixtures.zengshan_230_cases import CASE_1000


def test_case_1000_compound_sheng_real_fixture_keeps_favorable_direction():
    hexagram = Hexagram.from_ganzhi(
        CASE_1000["yao_types"],
        month_zhi=CASE_1000["month_zhi"],
        day_zhi=CASE_1000["day_zhi"],
        day_gan=CASE_1000["day_gan"],
        xun_kong=CASE_1000["xun_kong"],
    )
    report = run_analysis(hexagram, question_type=CASE_1000["question_type"], yong_shen_override=CASE_1000["yong_shen"])
    result = report.jixiong_result
    assert result["ji_xiong"] == "吉"
    assert result["rule_id"] in {"P0_COMPOUND_MOVEMENT_FINAL_TARGET", "legacy"}
    assert result["pattern"] in {"复合动生世", "用旺世兴局", "世用受生局"}
