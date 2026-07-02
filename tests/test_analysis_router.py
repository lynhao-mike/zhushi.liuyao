"""前置分析路由层最小回归测试。"""

from liuyao.application.use_cases.analysis import run_analysis
from liuyao.domain.analysis_router import route_analysis
from liuyao.domain.hexagram import Hexagram


def test_route_marks_lifetime_mode_for_lifetime_question_type():
    hexagram = Hexagram.from_ganzhi(
        [6, 6, 6, 8, 7, 6],
        month_zhi="子",
        day_zhi="子",
        day_gan="甲",
    )

    route = route_analysis(hexagram, "zhongshen_gongming")

    assert route["mode"] == "lifetime"
    assert route["time_scope"] == "lifetime"
    assert route["summary"]["mode_label"] == "终身卦"


def test_route_marks_mindset_mode_for_youhuan_question_type():
    hexagram = Hexagram.from_ganzhi(
        [8, 7, 7, 9, 7, 8],
        month_zhi="丑",
        day_zhi="寅",
        day_gan="甲",
    )

    route = route_analysis(hexagram, "youHuan")

    assert route["mode"] == "mindset"
    assert route["summary"]["mode_label"] == "心态卦"


def test_run_analysis_attaches_route_metadata():
    hexagram = Hexagram.from_ganzhi(
        [8, 7, 9, 8, 8, 7],
        month_zhi="酉",
        day_zhi="寅",
        day_gan="甲",
    )

    report = run_analysis(hexagram, question_type="guan")

    assert report.analysis_route
    assert report.analysis_route["mode"] == "event"
    assert report.analysis_route["time_scope"] == "normal"
    assert report.analysis_route["yong_shen_liu_qin"] == report.yong_shen_liu_qin
