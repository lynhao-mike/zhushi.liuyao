# -*- coding: utf-8 -*-
"""CASE_1000 运行时调试测试。"""

from pprint import pformat

from liuyao.application.use_cases.analysis import run_analysis
from liuyao.domain.hexagram import Hexagram
from liuyao.domain.wangshuai import analyze_hexagram_wangshuai
from liuyao.domain.dongbian import analyze_dongbian
from tests.fixtures.zengshan_230_cases import CASE_1000


def test_case_1000_debug_dump():
    hexagram = Hexagram.from_ganzhi(
        CASE_1000["yao_types"],
        month_zhi=CASE_1000["month_zhi"],
        day_zhi=CASE_1000["day_zhi"],
        day_gan=CASE_1000["day_gan"],
        xun_kong=CASE_1000["xun_kong"],
    )
    ws = analyze_hexagram_wangshuai(hexagram)
    db = analyze_dongbian(hexagram, ws)
    report = run_analysis(
        hexagram,
        question_type=CASE_1000["question_type"],
        yong_shen_override=CASE_1000["yong_shen"],
    )

    payload = {
        "ben_gua": hexagram.ben_gua_name,
        "bian_gua": hexagram.bian_gua_name,
        "shi_pos": hexagram.shi_pos,
        "ying_pos": hexagram.ying_pos,
        "lines": [
            {
                "position": line.position,
                "di_zhi": line.di_zhi,
                "liu_qin": line.liu_qin,
                "is_shi": line.is_shi,
                "is_ying": line.is_ying,
                "is_moving": line.is_moving,
                "bian_di_zhi": line.bian_di_zhi,
                "bian_liu_qin": line.bian_liu_qin,
            }
            for line in hexagram.lines
        ],
        "compound_movement": db.get("compound_movement"),
        "jixiong_result": report.jixiong_result,
    }
    print("\nCASE_1000_DEBUG=\n" + pformat(payload, width=120, sort_dicts=False))
    assert True
