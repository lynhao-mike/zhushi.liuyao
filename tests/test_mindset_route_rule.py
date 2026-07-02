"""心态路由上下文与最小消费规则回归测试。"""

from liuyao.application.use_cases.analysis import run_analysis
from liuyao.domain.analysis_router import route_analysis
from liuyao.domain.hexagram import Hexagram


def test_explicit_youhuan_route_is_mindset():
    hexagram = Hexagram.from_ganzhi(
        [8, 8, 9, 7, 8, 8],
        month_zhi="子",
        day_zhi="午",
        day_gan="甲",
    )

    route = route_analysis(hexagram, "youHuan")

    assert route["mode"] == "mindset"
    assert route["summary"]["mode_label"] == "心态卦"


def test_run_analysis_injects_route_into_patterns_results():
    hexagram = Hexagram.from_ganzhi(
        [8, 8, 9, 7, 8, 8],
        month_zhi="子",
        day_zhi="午",
        day_gan="甲",
    )

    report = run_analysis(hexagram, question_type="youHuan")

    assert report.analysis_route["mode"] == "mindset"
    assert report.patterns_results["analysis_route"]["mode"] == "mindset"
    assert report.patterns_results["analysis_route"]["time_scope"] == report.analysis_route["time_scope"]


def test_hidden_mindset_route_rule_consumes_stable_fixture():
    hexagram = Hexagram.from_ganzhi(
        [6, 6, 6, 6, 6, 6],
        month_zhi="子",
        day_zhi="午",
        day_gan="甲",
    )

    report = run_analysis(hexagram, question_type="other", yong_shen_override="父母")

    assert report.analysis_route["mode"] == "mindset"
    assert report.patterns_results["analysis_route"]["mode"] == "mindset"
    assert report.jixiong_result["rule_id"] == "P1_MINDSET_ROUTE"
    assert report.jixiong_result["pattern"] == "心态卦路由"
    assert report.jixiong_result["ji_xiong"] == "平"


def test_explicit_youhuan_does_not_use_hidden_mindset_route_rule():
    hexagram = Hexagram.from_ganzhi(
        [6, 6, 6, 6, 6, 6],
        month_zhi="子",
        day_zhi="午",
        day_gan="甲",
    )

    report = run_analysis(hexagram, question_type="youHuan")

    assert report.analysis_route["mode"] == "mindset"
    assert report.jixiong_result.get("rule_id") != "P1_MINDSET_ROUTE"


def test_mindset_zisun_shi_is_auspicious_signal():
    hexagram = Hexagram.from_ganzhi(
        [6, 7, 7, 7, 7, 7],
        month_zhi="子",
        day_zhi="午",
        day_gan="甲",
    )

    report = run_analysis(hexagram, question_type="youHuan")

    assert report.analysis_route["mode"] == "mindset"
    assert report.jixiong_result["rule_id"] == "P1_MINDSET_XI_YOU_SIGNAL"
    assert report.jixiong_result["pattern"] == "心态卦喜神持世"
    assert report.jixiong_result["ji_xiong"] == "吉"


def test_mindset_guangui_shi_is_inauspicious_signal():
    hexagram = Hexagram.from_ganzhi(
        [8, 8, 9, 7, 8, 8],
        month_zhi="子",
        day_zhi="午",
        day_gan="甲",
    )

    report = run_analysis(hexagram, question_type="youHuan")

    assert report.analysis_route["mode"] == "mindset"
    assert report.jixiong_result["rule_id"] == "P1_MINDSET_XI_YOU_SIGNAL"
    assert report.jixiong_result["pattern"] == "心态卦忧神持世"
    assert report.jixiong_result["ji_xiong"] == "凶"
