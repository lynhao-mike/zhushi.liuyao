"""时效卦统一分类最小测试。"""

from liuyao.application.use_cases.analysis import run_analysis
from liuyao.domain.dongbian import analyze_dongbian
from liuyao.domain.hexagram import Hexagram
from liuyao.domain.rules.context import RuleContext
from liuyao.domain.wangshuai import analyze_hexagram_wangshuai


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


def test_month_shixiao_context_detects_case_09_shape():
    hexagram = Hexagram.from_ganzhi(
        [8, 7, 9, 8, 8, 7],
        month_zhi="酉",
        day_zhi="寅",
        day_gan="甲",
    )
    ctx = _ctx(hexagram, "官鬼", "guan")
    shixiao = ctx.shixiao_context(ctx.primary_yong)
    assert shixiao["is_month_shixiao"] is True


def test_lifetime_shixiao_context_detects_question_type():
    hexagram = Hexagram.from_ganzhi(
        [6, 6, 6, 8, 7, 6],
        month_zhi="子",
        day_zhi="子",
        day_gan="甲",
    )
    ctx = _ctx(hexagram, "官鬼", "zhongshen_gongming")
    shixiao = ctx.shixiao_context()
    assert shixiao["is_lifetime_shixiao"] is True


def test_month_shixiao_rule_still_hits_case_09_shape():
    hexagram = Hexagram.from_ganzhi(
        [8, 7, 9, 8, 8, 7],
        month_zhi="酉",
        day_zhi="寅",
        day_gan="甲",
    )
    report = run_analysis(hexagram, question_type="guan")
    result = report.jixiong_result
    assert result["rule_id"] == "P0_YUE_LING_SHIXIAO"
    assert result["pattern"] == "月令时效卦"
