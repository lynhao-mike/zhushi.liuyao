# -*- coding: utf-8 -*-
"""日令时效卦最小回归测试。"""

from liuyao.application.use_cases.analysis import run_analysis
from liuyao.domain.hexagram import Hexagram
from liuyao.domain.rules.context import RuleContext
from liuyao.domain.wangshuai import analyze_hexagram_wangshuai
from liuyao.domain.dongbian import analyze_dongbian
from tests.fixtures.zengshan_230_cases import CASE_999


def _ctx(hexagram, yong_shen_liu_qin, question_type):
    ws = analyze_hexagram_wangshuai(hexagram)
    db = analyze_dongbian(hexagram, ws)
    yong_lines = [line for line in hexagram.lines if line.liu_qin == yong_shen_liu_qin]
    return RuleContext(
        hexagram=hexagram,
        yong_shen_liu_qin=yong_shen_liu_qin,
        wangshuai_results=ws,
        dongbian_results=db,
        question_type=question_type,
        patterns_results={},
        shi_line=hexagram.shi_line,
        primary_yong=yong_lines[0] if yong_lines else None,
        yong_lines=yong_lines,
        month_zhi=hexagram.gan_zhi["month_zhi"],
        day_zhi=hexagram.gan_zhi["day_zhi"],
    )


def test_day_shixiao_context_detects_short_term_day_window():
    hexagram = Hexagram.from_ganzhi(
        CASE_999["yao_types"],
        month_zhi=CASE_999["month_zhi"],
        day_zhi=CASE_999["day_zhi"],
        day_gan=CASE_999["day_gan"],
        xun_kong=CASE_999["xun_kong"],
    )
    ctx = _ctx(hexagram, CASE_999["yong_shen"], CASE_999["question_type"])
    # 例999 取三爻辰土为用神, 五爻巳火临日令发动
    day_line = hexagram.lines[4]
    shixiao = ctx.shixiao_context(day_line)
    assert shixiao["is_day_shixiao"] is True


def test_day_shixiao_rule_can_enter_main_judgement():
    hexagram = Hexagram.from_ganzhi(
        CASE_999["yao_types"],
        month_zhi=CASE_999["month_zhi"],
        day_zhi=CASE_999["day_zhi"],
        day_gan=CASE_999["day_gan"],
        xun_kong=CASE_999["xun_kong"],
    )
    report = run_analysis(hexagram, question_type=CASE_999["question_type"], yong_shen_override=CASE_999["yong_shen"])
    result = report.jixiong_result
    assert result["rule_id"] in {"P0_RI_LING_SHIXIAO", "P1_YUANSHEN_DUFA_BIANFEI"}
    assert result["pattern"] in {"日令时效卦", "元神独发变废(回头克)"}
