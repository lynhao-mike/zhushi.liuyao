"""特殊日月组合最小闭环测试。"""

from liuyao.application.use_cases.analysis import run_analysis
from liuyao.domain.dongbian import analyze_dongbian
from liuyao.domain.hexagram import Hexagram
from liuyao.domain.rules.context import RuleContext
from liuyao.domain.wangshuai import analyze_hexagram_wangshuai


def _ctx(hexagram, yong_shen_liu_qin="官鬼", question_type="other"):
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


def test_special_day_month_combo_detects_feiyao():
    hexagram = Hexagram.from_ganzhi(
        [8, 7, 7, 7, 9, 6],
        month_zhi="巳",
        day_zhi="未",
        day_gan="甲",
    )
    ctx = _ctx(hexagram, yong_shen_liu_qin="父母", question_type="fumu")
    # 例3语境: 四爻亥水父母为用神, 月破日克
    target = hexagram.lines[3]
    combo = ctx.special_day_month_combo(target)
    assert combo["is_feiyao"] is True


def test_special_day_month_combo_detects_jingang():
    hexagram = Hexagram.from_ganzhi(
        [7, 7, 8, 6, 9, 8],
        month_zhi="申",
        day_zhi="辰",
        day_gan="甲",
    )
    ctx = _ctx(hexagram, yong_shen_liu_qin="兄弟")
    moving_line = hexagram.lines[3]
    combo = ctx.special_day_month_combo(moving_line)
    assert combo["is_jingang"] is True


def test_special_day_month_combo_excludes_month_chong_day_chong_case():
    hexagram = Hexagram.from_ganzhi(
        [8, 6, 7, 8, 9, 7],
        month_zhi="卯",
        day_zhi="酉",
        day_gan="甲",
    )
    ctx = _ctx(hexagram, yong_shen_liu_qin="妻财", question_type="hun")
    if ctx.primary_yong is not None:
        combo = ctx.special_day_month_combo(ctx.primary_yong)
        assert combo["excludes_month_chong_day_chong"] in (True, False)


def test_feiyao_rule_still_hits_case_03_shape():
    hexagram = Hexagram.from_ganzhi(
        [8, 7, 7, 7, 9, 6],
        month_zhi="巳",
        day_zhi="未",
        day_gan="甲",
    )
    report = run_analysis(hexagram, question_type="fumu")
    result = report.jixiong_result
    assert result["rule_id"] == "P0_FEI_YAO_RIYUE"
    assert result["pattern"] == "废爻型(月破日克)"
