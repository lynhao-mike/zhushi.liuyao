"""
分析路由层 - Analysis Router

在不改写既有吉凶主判管线的前提下，补充一个轻量前置路由器，
为后续 staged clean path 提供结构化分析上下文。

职责:
- 识别卦种/分析模式的最小集合
- 识别时效范围标签
- 给出目标候选与说明

注意:
- 当前模块只产出元信息，不直接改判
- 规则层后续可逐步消费这些路由结果
"""

from __future__ import annotations

from liuyao.domain.jixiong import determine_yong_shen, find_ying_line, find_yong_shen_lines

LIFETIME_TYPES = {"zhongshen_gongming", "zhongshen_caifu", "zhongshen_yunshi", "shouming"}
DAY_TIMING_TYPES = {"dangri", "mashang", "jinshi"}
MONTH_TIMING_TYPES = {"guan", "kaoshi", "cai", "shengyi", "bing", "other"}
REPEATED_DIVINATION_TYPES = {"zaizhan"}
WORRY_TYPES = {"youHuan"}
DESIGNATED_TARGET_TYPES = {"hun_male", "hun_female", "xingren", "xingren_gui"}


def _detect_analysis_mode(hexagram, question_type, yong_shen_lines, yong_shen_liu_qin):
    if question_type in LIFETIME_TYPES:
        return "lifetime"
    if question_type in DAY_TIMING_TYPES:
        return "timing"
    if question_type in REPEATED_DIVINATION_TYPES:
        return "repeated_divination"
    if question_type in WORRY_TYPES:
        return "mindset"

    zi_sun_visible = any(line.liu_qin == "子孙" and (line.is_moving or line.is_shi) for line in hexagram.lines)
    guan_gui_visible = any(line.liu_qin == "官鬼" and (line.is_moving or line.is_shi) for line in hexagram.lines)
    if not yong_shen_lines:
        if yong_shen_liu_qin != "官鬼" and (zi_sun_visible or guan_gui_visible):
            return "mindset"
    else:
        if yong_shen_liu_qin != "官鬼" and zi_sun_visible and guan_gui_visible:
            return "mindset"

    if question_type in DESIGNATED_TARGET_TYPES:
        ying_line = find_ying_line(hexagram)
        if ying_line is not None:
            return "designated_target"

    return "event"


def _detect_time_scope(question_type):
    if question_type in LIFETIME_TYPES:
        return "lifetime"
    if question_type in DAY_TIMING_TYPES:
        return "day"
    if question_type in MONTH_TIMING_TYPES:
        return "month"
    if question_type in REPEATED_DIVINATION_TYPES:
        return "repeated"
    return "normal"


def _build_target_candidates(hexagram, yong_shen_liu_qin, yong_shen_lines, mode):
    candidates = []
    if yong_shen_lines:
        candidates.append({
            "kind": "yong_shen",
            "liu_qin": yong_shen_liu_qin,
            "positions": [line.position for line in yong_shen_lines],
            "reason": "默认六亲取用",
        })
    else:
        candidates.append({
            "kind": "yong_shen_missing",
            "liu_qin": yong_shen_liu_qin,
            "positions": [],
            "reason": "默认六亲用神不上卦",
        })

    if mode == "designated_target":
        ying_line = find_ying_line(hexagram)
        if ying_line is not None:
            candidates.append({
                "kind": "designated_target",
                "liu_qin": ying_line.liu_qin,
                "positions": [ying_line.position],
                "reason": "特指定向场景，应爻列为并行目标候选",
            })

    return candidates


def route_analysis(hexagram, question_type, yong_shen_override=None):
    yong_shen_liu_qin = yong_shen_override or determine_yong_shen(question_type)
    yong_shen_lines = find_yong_shen_lines(hexagram, yong_shen_liu_qin)
    mode = _detect_analysis_mode(hexagram, question_type, yong_shen_lines, yong_shen_liu_qin)
    time_scope = _detect_time_scope(question_type)
    target_candidates = _build_target_candidates(hexagram, yong_shen_liu_qin, yong_shen_lines, mode)

    return {
        "mode": mode,
        "time_scope": time_scope,
        "yong_shen_liu_qin": yong_shen_liu_qin,
        "target_candidates": target_candidates,
        "summary": {
            "mode_label": {
                "event": "事卦",
                "mindset": "心态卦",
                "timing": "应期卦",
                "lifetime": "终身卦",
                "designated_target": "特指定向卦",
                "repeated_divination": "连占卦",
            }.get(mode, "事卦"),
            "time_scope_label": {
                "day": "日内时效",
                "month": "月内时效",
                "normal": "常规时效",
                "lifetime": "终身时效",
                "repeated": "连占时效",
            }.get(time_scope, "常规时效"),
        },
    }
