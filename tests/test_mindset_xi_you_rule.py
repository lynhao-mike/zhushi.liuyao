"""心态喜神/忧神判定规则隔离测试。"""

from types import SimpleNamespace

from liuyao.domain.rules.context import RuleContext
from liuyao.domain.rules.p0_rules import MindsetXiYouSignalRule


def _line(position, liu_qin, *, is_shi=False, is_moving=False):
    return SimpleNamespace(
        position=position,
        liu_qin=liu_qin,
        di_zhi="子",
        is_shi=is_shi,
        is_ying=False,
        is_moving=is_moving,
    )


def _ctx(lines, shi):
    by_lq = {}
    for line in lines:
        by_lq.setdefault(line.liu_qin, []).append(line)
    return RuleContext(
        hexagram=SimpleNamespace(lines=lines, lines_by_liu_qin=by_lq),
        yong_shen_liu_qin="子孙",
        wangshuai_results=[],
        dongbian_results={},
        question_type="youHuan",
        patterns_results={"analysis_route": {"mode": "mindset"}},
        shi_line=shi,
        primary_yong=None,
        yong_lines=[],
        month_zhi="子",
        day_zhi="午",
    )


def test_xi_signal_returns_ji_for_zisun_shi():
    shi = _line(1, "子孙", is_shi=True)
    ctx = _ctx([shi], shi)

    result = MindsetXiYouSignalRule().evaluate(ctx)

    assert result is not None
    assert result.rule_id == "P1_MINDSET_XI_YOU_SIGNAL"
    assert result.pattern == "心态卦喜神持世"
    assert result.ji_xiong == "吉"


def test_you_signal_returns_xiong_for_guangui_shi():
    shi = _line(1, "官鬼", is_shi=True)
    ctx = _ctx([shi], shi)

    result = MindsetXiYouSignalRule().evaluate(ctx)

    assert result is not None
    assert result.rule_id == "P1_MINDSET_XI_YOU_SIGNAL"
    assert result.pattern == "心态卦忧神持世"
    assert result.ji_xiong == "凶"


def test_xi_signal_returns_ji_for_zisun_moving_only():
    shi = _line(1, "兄弟", is_shi=True)
    zi = _line(2, "子孙", is_moving=True)
    ctx = _ctx([shi, zi], shi)

    result = MindsetXiYouSignalRule().evaluate(ctx)

    assert result is not None
    assert result.pattern == "心态卦喜神发动"
    assert result.ji_xiong == "吉"


def test_you_signal_returns_xiong_for_guangui_moving_only():
    shi = _line(1, "兄弟", is_shi=True)
    gui = _line(2, "官鬼", is_moving=True)
    ctx = _ctx([shi, gui], shi)

    result = MindsetXiYouSignalRule().evaluate(ctx)

    assert result is not None
    assert result.pattern == "心态卦忧神发动"
    assert result.ji_xiong == "凶"


def test_xi_you_signal_returns_none_when_both_zisun_and_guangui_move():
    shi = _line(1, "兄弟", is_shi=True)
    zi = _line(2, "子孙", is_moving=True)
    gui = _line(3, "官鬼", is_moving=True)
    ctx = _ctx([shi, zi, gui], shi)

    result = MindsetXiYouSignalRule().evaluate(ctx)

    assert result is None


def test_xi_you_signal_ignores_non_mindset_route():
    shi = _line(1, "子孙", is_shi=True)
    ctx = _ctx([shi], shi)
    ctx.patterns_results["analysis_route"]["mode"] = "event"

    result = MindsetXiYouSignalRule().evaluate(ctx)

    assert result is None
