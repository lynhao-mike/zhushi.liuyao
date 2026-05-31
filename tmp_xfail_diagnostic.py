# -*- coding: utf-8 -*-
"""临时输出剩余 xfail 的根因摘要。"""

from liuyao.analyzer import run_analysis
from liuyao.domain.jixiong import find_shi_line, find_yong_shen_lines
from tests.test_zengshan_cases import _build_hexagram
from tests.fixtures.zengshan_230_cases import (
    CASE_01,
    CASE_02,
    CASE_20,
    CASE_41,
    CASE_54,
    CASE_108,
    CASE_205,
)


def line_tuple(line):
    if line is None:
        return None
    return (
        line.position,
        line.di_zhi,
        line.wu_xing,
        line.liu_qin,
        line.is_shi,
        line.is_ying,
        line.is_moving,
        getattr(line, "bian_di_zhi", None),
        getattr(line, "bian_liu_qin", None),
    )


for case in (CASE_01, CASE_02, CASE_20, CASE_41, CASE_54, CASE_108, CASE_205):
    print("\n==", case["id"], case.get("ben_gua"), "->", case.get("bian_gua"))
    print("status:", case.get("data_status"), case.get("failure_type"))
    print("desc:", case.get("description"))
    try:
        h = _build_hexagram(case)
        report = run_analysis(h, question_type=case.get("question_type", "other"))
    except Exception as exc:
        print("BUILD/ANALYSIS ERROR:", type(exc).__name__, exc)
        continue
    shi = find_shi_line(h)
    yong_lines = find_yong_shen_lines(h, case["yong_shen"])
    print("expected/got:", case["expected_ji_xiong"], report.jixiong_result)
    print("shi:", line_tuple(shi))
    print("yong:", [line_tuple(line) for line in yong_lines])
    print("moving:", [line_tuple(line) for line in h.lines if line.is_moving])
    print("wangshuai:")
    for idx, ws in enumerate(report.wangshuai_results, start=1):
        print("  ", idx, ws["di_zhi"], ws["liu_qin"], ws["overall"], ws["month_wang"], ws["month_shuai"], ws["day_wang"], ws["day_shuai"])
    print("dongbian:", report.dongbian_results)
    print("patterns:", {
        "san_ban": report.patterns_results.get("san_ban"),
        "chong_he_gua": report.patterns_results.get("chong_he_gua"),
        "kuayi_patterns": report.patterns_results.get("kuayi_patterns"),
    })
