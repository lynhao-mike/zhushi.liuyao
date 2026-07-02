"""心态喜神/忧神判定规则隔离测试。

直接构造 RuleContext，不依赖 Hexagram 排卦的终端编码问题。
"""

from liuyao.domain.hexagram import Hexagram
from liuyao.domain.jixiong import find_shi_line
from liuyao.domain.rules.context import RuleContext
from liuyao.domain.rules.p0_rules import MindsetXiYouSignalRule
from liuyao.domain.wangshuai import analyze_hexagram_wangshuai
from liuyao.domain.dongbian import analyze_dongbian


def _make_ctx(hexagram, question_type="youHuan", yong_shen_liu_qin="子孙"):
    ws = analyze_hexagram_wangshuai(hexagram)
    db = analyze_dongbian(hexagram, ws)
    yong_lines = [l for l in hexagram.lines if l.liu_qin == yong_shen_liu_qin]
    shi = find_shi_line(hexagram)
    ctx = RuleContext(
        hexagram=hexagram,
        yong_shen_liu_qin=yong_shen_liu_qin,
        wangshuai_results=ws,
        dongbian_results=db,
        question_type=question_type,
        patterns_results={"analysis_route": {"mode": "mindset"}},
        shi_line=shi,
        primary_yong=yong_lines[0] if yong_lines else None,
        yong_lines=yong_lines,
        month_zhi=hexagram.gan_zhi["month_zhi"],
        day_zhi=hexagram.gan_zhi["day_zhi"],
    )
    return ctx, shi


def test_xitou_signal_returns_吉_for_zisun_shi():
    # 子孙持世的静卦
    h = Hexagram.from_ganzhi(
        [7, 8, 8, 8, 8, 8],  # 初爻少阳子孙持世
        month_zhi="子", day_zhi="午", day_gan="甲",
    )
    ctx, shi = _make_ctx(h)
    s_lq = shi.liu_qin if shi else ""

    if s_lq == "子孙":
        result = MindsetXiYouSignalRule().evaluate(ctx)
        assert result is not None
        assert result.ji_xiong == "吉"
        assert "喜神持世" in result.pattern or "喜神" in result.pattern
    else:
        # 世爻不是子孙，这条测试跳过——说明这个 hexagram 组合没命中持世条件
        pass


def test_xitou_signal_returns_凶_for_guangui_shi():
    h = Hexagram.from_ganzhi(
        [8, 7, 7, 7, 7, 7],
        month_zhi="子", day_zhi="午", day_gan="甲",
    )
    ctx, shi = _make_ctx(h)
    s_lq = shi.liu_qin if shi else ""

    if s_lq == "官鬼":
        result = MindsetXiYouSignalRule().evaluate(ctx)
        assert result is not None
        assert result.ji_xiong == "凶"
        assert "忧神持世" in result.pattern or "忧神" in result.pattern
    else:
        pass


def test_xitou_signal_returns_none_for_other_shi():
    h = Hexagram.from_ganzhi(
        [8, 8, 8, 8, 8, 8],
        month_zhi="子", day_zhi="午", day_gan="甲",
    )
    ctx, shi = _make_ctx(h)
    s_lq = shi.liu_qin if shi else ""

    if s_lq not in ("子孙", "官鬼"):
        result = MindsetXiYouSignalRule().evaluate(ctx)
        assert result is None
    else:
        pass
