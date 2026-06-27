"""
分析编排器 - Analysis Orchestrator

整合旺衰分析、动变分析、卦象模式识别、吉凶判断、卦意分析法、
应期推断, 生成完整分析报告。

支持单视角(run_analysis)与双视角(run_dual_analysis)两种模式。
"""

import logging
from dataclasses import dataclass, field
from typing import List, Dict, Optional

from liuyao.domain.hexagram import Hexagram
from liuyao.domain.data import get_star_spirits
from liuyao.domain.wangshuai import analyze_hexagram_wangshuai
from liuyao.domain.dongbian import analyze_dongbian
from liuyao.domain.jixiong import (
    judge_jixiong, determine_yong_shen,
    find_yong_shen_lines, find_shi_line,
    find_ying_line,
    get_dual_perspectives,
    JI_SHEN_TABLE,
)
from liuyao.domain.yingqi import analyze_yingqi
from liuyao.domain.yimao_imagery import analyze_yimao_imagery
from liuyao.domain.patterns import (
    analyze_all_patterns,
    analyze_perspective_patterns,
    analyze_structural_patterns,
    merge_pattern_results,
)
from liuyao.domain.exceptions import AnalysisError

log = logging.getLogger(__name__)


@dataclass
class AnalysisReport:
    """单视角分析报告"""
    # 基本信息
    hexagram: Hexagram = None
    question_type: str = ""
    yong_shen_liu_qin: str = ""
    ji_shen_liu_qin: str = ""
    perspective_label: str = ""  # 视角标签 (如"物件本相视角"), 单视角时为空

    # 分析结果
    wangshuai_results: List[Dict] = field(default_factory=list)
    dongbian_results: Dict = field(default_factory=dict)
    patterns_results: Dict = field(default_factory=dict)
    star_spirits: Dict = field(default_factory=dict)
    yimao_imagery: Dict = field(default_factory=dict)
    jixiong_result: Dict = field(default_factory=dict)
    yingqi_results: List[Dict] = field(default_factory=list)

    # 用神信息
    yong_shen_lines: List = field(default_factory=list)
    shi_line: Optional[object] = None
    ying_line: Optional[object] = None


@dataclass
class DualPerspectiveReport:
    """
    双(多)视角分析报告。

    共享: 排卦信息、日月、各爻旺衰、动变分析、模式识别、星煞 (只算一次)。
    各自: 用神选定、卦意分析、吉凶判断、应期推断。

    适用于多个合理用神并存的占类(失物、问病等)。
    """
    hexagram: Hexagram = None
    question_type: str = ""

    # 共享部分
    wangshuai_results: List[Dict] = field(default_factory=list)
    dongbian_results: Dict = field(default_factory=dict)
    star_spirits: Dict = field(default_factory=dict)
    shi_line: Optional[object] = None
    ying_line: Optional[object] = None

    # 各视角分析结果
    perspectives: List[AnalysisReport] = field(default_factory=list)

    # 综合结论 (一致吉/一致凶/分歧)
    consensus: str = ""


def run_analysis(hexagram, question_type="other",
                 yong_shen_override=None, perspective_label=""):
    """
    执行完整六爻分析流程。

    Args:
        hexagram: 已排好的Hexagram对象
        question_type: 问事类型
        yong_shen_override: 可选, 覆盖默认用神六亲
        perspective_label: 可选, 视角标签

    Returns:
        AnalysisReport: 完整分析报告
    """
    report = AnalysisReport()
    report.hexagram = hexagram
    report.question_type = question_type
    report.perspective_label = perspective_label

    # 1. 确定用神 (允许覆盖)
    if yong_shen_override:
        report.yong_shen_liu_qin = yong_shen_override
    else:
        report.yong_shen_liu_qin = determine_yong_shen(question_type)
    report.ji_shen_liu_qin = JI_SHEN_TABLE.get(report.yong_shen_liu_qin, "")
    report.yong_shen_lines = find_yong_shen_lines(hexagram, report.yong_shen_liu_qin)
    report.shi_line = find_shi_line(hexagram)
    report.ying_line = find_ying_line(hexagram)

    # 2. 旺衰分析
    report.wangshuai_results = analyze_hexagram_wangshuai(hexagram)

    # 3. 动变分析
    try:
        report.dongbian_results = analyze_dongbian(hexagram, report.wangshuai_results)
    except Exception as e:
        log.error("dongbian_analysis_failed", exc_info=True,
                  gua=hexagram.ben_gua_name, question_type=question_type)
        report.dongbian_results = {
            "moving_analyses": {}, "san_he_ju": [], "an_dong": [],
            "useful_moving": [], "useless_moving": [], "interactions": {},
        }

    # 4. 卦象结构模式识别 (入墓/三绊/反吟/伏吟/六冲六合卦/三刑/六害/三会/心态卦/卦意法)
    try:
        report.patterns_results = analyze_all_patterns(
            hexagram, report.wangshuai_results, report.dongbian_results,
            report.yong_shen_liu_qin, report.ji_shen_liu_qin,
            report.yong_shen_lines, question_type,
        )
    except Exception as e:
        log.error("patterns_analysis_failed", exc_info=True,
                  gua=hexagram.ben_gua_name, question_type=question_type)
        report.patterns_results = {}

    # 5. 13星煞计算
    try:
        report.star_spirits = get_star_spirits(
            hexagram.gan_zhi["day_gan"],
            hexagram.gan_zhi["day_zhi"],
            hexagram.gan_zhi["month_zhi"],
        )
    except Exception:
        log.error("star_spirits_failed", exc_info=True,
                  gua=hexagram.ben_gua_name)
        report.star_spirits = {}

    # 6. 《易冒》象法摘要(只作报告层细节, 不参与吉凶)
    report.yimao_imagery = analyze_yimao_imagery(
        hexagram, report.yong_shen_lines,
        report.wangshuai_results, report.dongbian_results,
        patterns_results=report.patterns_results,
        question_type=question_type,
    )

    # 7. 吉凶判断
    try:
        report.jixiong_result = judge_jixiong(
            hexagram, report.yong_shen_liu_qin,
            report.wangshuai_results, report.dongbian_results,
            question_type,
            patterns_results=report.patterns_results,
        )
        # 注入卦意法附加判断
        kuayi_patterns = report.patterns_results.get("kuayi_patterns", [])
        if kuayi_patterns:
            report.jixiong_result["kuayi_supplements"] = kuayi_patterns
        # 注入象法软信号（不覆盖吉凶裁决，只作解释层补充）
        yimao_sentences = report.yimao_imagery.get("sentences", [])
        if yimao_sentences:
            report.jixiong_result["yimao_signals"] = yimao_sentences
    except Exception as e:
        log.error("jixiong_analysis_failed", exc_info=True,
                  gua=hexagram.ben_gua_name, question_type=question_type)
        report.jixiong_result = {
            "pattern": "分析异常", "ji_xiong": "平",
            "explanation": f"吉凶判断过程异常: {e}",
        }

    # 8. 应期推断 (使用 patterns 结果增强)
    try:
        report.yingqi_results = analyze_yingqi(
            hexagram, report.yong_shen_lines,
            report.wangshuai_results, report.dongbian_results,
            patterns_results=report.patterns_results,
        )
    except Exception as e:
        log.error("yingqi_analysis_failed", exc_info=True,
                  gua=hexagram.ben_gua_name, question_type=question_type)
        report.yingqi_results = []

    return report


def run_dual_analysis(hexagram, question_type="shiwu"):
    """
    执行双(多)视角分析流程。

    适用于失物、问病等多个合理用神并存的占类。
    共享部分(排卦、日月、旺衰、动变、模式识别、星煞)只计算一次,
    各视角各自完成用神选定、吉凶判断、应期推断。
    """
    perspectives_config = get_dual_perspectives(question_type)

    dual = DualPerspectiveReport()
    dual.hexagram = hexagram
    dual.question_type = question_type

    # 1-2. 共享计算: 旺衰 + 动变 (只算一次)
    shared_ws = analyze_hexagram_wangshuai(hexagram)
    shared_db = analyze_dongbian(hexagram, shared_ws)
    shi_line = find_shi_line(hexagram)
    ying_line = find_ying_line(hexagram)

    dual.wangshuai_results = shared_ws
    dual.dongbian_results = shared_db
    dual.shi_line = shi_line
    dual.ying_line = ying_line

    # 3. 13星煞 (只算一次)
    try:
        dual.star_spirits = get_star_spirits(
            hexagram.gan_zhi["day_gan"],
            hexagram.gan_zhi["day_zhi"],
            hexagram.gan_zhi["month_zhi"],
        )
    except Exception:
        log.error("star_spirits_failed", exc_info=True,
                  gua=hexagram.ben_gua_name)
        dual.star_spirits = {}

    # 4. 与用神无关的结构模式只计算一次, 各视角复用
    try:
        shared_structural_patterns = analyze_structural_patterns(
            hexagram, shared_ws, shared_db,
        )
    except Exception:
        log.error("structural_patterns_analysis_failed", exc_info=True,
                  gua=hexagram.ben_gua_name, question_type=question_type)
        shared_structural_patterns = {}

    # 5-8. 各视角分别完成视角模式/卦意/吉凶/应期
    for yong_shen, label in perspectives_config:
        report = AnalysisReport()
        report.hexagram = hexagram
        report.question_type = question_type
        report.perspective_label = label
        report.yong_shen_liu_qin = yong_shen
        report.ji_shen_liu_qin = JI_SHEN_TABLE.get(yong_shen, "")
        report.yong_shen_lines = find_yong_shen_lines(hexagram, yong_shen)
        report.shi_line = shi_line
        report.ying_line = ying_line
        report.wangshuai_results = shared_ws
        report.dongbian_results = shared_db
        report.star_spirits = dual.star_spirits
        report.yimao_imagery = analyze_yimao_imagery(
            hexagram, report.yong_shen_lines, shared_ws, shared_db,
            patterns_results=report.patterns_results,
            question_type=question_type,
        )

        # 各视角仅计算依赖用神/问事类型的模式, 再合并共享结构模式
        try:
            perspective_patterns = analyze_perspective_patterns(
                hexagram, shared_db,
                yong_shen, report.ji_shen_liu_qin,
                report.yong_shen_lines, question_type,
            )
            report.patterns_results = merge_pattern_results(
                shared_structural_patterns, perspective_patterns,
            )
        except Exception:
            log.error("patterns_analysis_failed", exc_info=True,
                      gua=hexagram.ben_gua_name, perspective=label)
            report.patterns_results = {}

        try:
            report.jixiong_result = judge_jixiong(
                hexagram, yong_shen, shared_ws, shared_db, question_type,
                patterns_results=report.patterns_results,
            )
            kuayi_patterns = report.patterns_results.get("kuayi_patterns", [])
            if kuayi_patterns:
                report.jixiong_result["kuayi_supplements"] = kuayi_patterns
            yimao_sentences = report.yimao_imagery.get("sentences", [])
            if yimao_sentences:
                report.jixiong_result["yimao_signals"] = yimao_sentences
        except Exception as e:
            log.error("jixiong_analysis_failed", exc_info=True,
                      gua=hexagram.ben_gua_name, perspective=label)
            report.jixiong_result = {
                "pattern": "分析异常", "ji_xiong": "平",
                "explanation": f"吉凶判断过程异常: {e}",
            }

        try:
            report.yingqi_results = analyze_yingqi(
                hexagram, report.yong_shen_lines, shared_ws, shared_db,
                patterns_results=report.patterns_results,
            )
        except Exception as e:
            log.error("yingqi_analysis_failed", exc_info=True,
                      gua=hexagram.ben_gua_name, perspective=label)
            report.yingqi_results = []

        dual.perspectives.append(report)

    # 综合结论
    ji_xiong_set = {p.jixiong_result.get("ji_xiong", "平") for p in dual.perspectives}
    if len(ji_xiong_set) == 1:
        result = ji_xiong_set.pop()
        dual.consensus = f"两视角一致定性: {result}"
    else:
        dual.consensus = "视角分歧: " + " / ".join(
            f"{p.perspective_label}={p.jixiong_result.get('ji_xiong', '平')}"
            for p in dual.perspectives
        )

    return dual


# ── Verdict computation (business logic, not formatting) ─────────────────────

# 卦局白话解释 — 权威来源 (report.py 从此处导入, 不再重复定义)
GUA_JU_BAIHUA: dict = {
    "世用受克局":   "用神与世爻合一却遭受动爻克伤——失物与主人的缘分已断，凶。",
    "世爻受伤局":   "世爻被有力的动爻克伤——主人追寻此物的力量受阻，凶。",
    "世用受生局":   "用神与世爻合一且受动爻生扶——失物有归还之象，吉。",
    "用神生世局":   "用神主动生旺世爻——物与主人气场相连，有望寻回，吉。",
    "用旺世兴局":   "用神旺盛，世爻亦得日月扶助——天时地利俱备，可寻回，吉。",
    "用旺世衰局":   "用神虽旺，世爻却衰弱——物虽存在，主人无力追回，凶。",
    "用神克世局":   "用神动而克世——物事对主人有所伤损，凶（短期失物若世旺可酌情看吉）。",
    "用神衰败局":   "用神本身衰弱——所失之物已残损或难觅踪迹，凶。",
    "失物特例(用克世)": "用神动克世但世爻有日月扶助——短期内有望寻回（属特例之吉）。",
    "静卦用旺世兴": "静卦中用神旺、世爻兴——物在某处静候，可寻，吉。",
    "静卦用衰":     "静卦用神衰败——物已难觅，凶。",
    "静卦用克世":   "静卦用神克世——寻物对主人构成损耗，凶。",
    "用神持世":     "用神就是世爻——物与人同在，情形密切，可寻，吉。",
    "平局":         "卦局平和，吉凶未明，需结合细节综合研判。",
}


def build_verdict(analysis) -> dict:
    """
    从 AnalysisReport 或 DualPerspectiveReport 中提取综合断语。

    返回:
        {
            "verdict":      str,   # 断语文本，如 "凶——此物难以寻回"
            "tone":         str,   # 解释段落（多行）
            "yingqi_lines": list,  # 扁平化去重后的应期列表 [{position, di_zhi, ...}]
        }
    """
    is_dual = hasattr(analysis, "perspectives") and bool(analysis.perspectives)

    if is_dual:
        perspectives = analysis.perspectives
        j1 = perspectives[0].jixiong_result
        j2 = perspectives[1].jixiong_result if len(perspectives) > 1 else j1
        p1_label = perspectives[0].perspective_label
        p2_label = perspectives[1].perspective_label if len(perspectives) > 1 else ""

        both_xiong = j1.get("ji_xiong") == "凶" and j2.get("ji_xiong") == "凶"
        both_ji    = j1.get("ji_xiong") == "吉" and j2.get("ji_xiong") == "吉"

        if both_xiong:
            verdict = "凶——此物难以寻回"
            tone = (
                "从物件本相（父母爻）与财物价值（妻财爻）两个角度审视，"
                "卦象均指向同一结论：\n"
                f"  · {p1_label}：{GUA_JU_BAIHUA.get(j1['pattern'], j1.get('explanation',''))}\n"
                f"  · {p2_label}：{GUA_JU_BAIHUA.get(j2['pattern'], j2.get('explanation',''))}\n"
                "两路相验，结论趋同，说明卦象给出的信号相当确定。"
            )
        elif both_ji:
            verdict = "吉——此物有望寻回"
            tone = (
                "两个视角均显示吉象：\n"
                f"  · {p1_label}：{GUA_JU_BAIHUA.get(j1['pattern'], j1.get('explanation',''))}\n"
                f"  · {p2_label}：{GUA_JU_BAIHUA.get(j2['pattern'], j2.get('explanation',''))}\n"
                "双视角互证，寻回可期。"
            )
        else:
            v1 = j1.get("ji_xiong", "平")
            v2 = j2.get("ji_xiong", "平")
            p1_ys = perspectives[0].yong_shen_liu_qin
            p2_ys = perspectives[1].yong_shen_liu_qin if len(perspectives) > 1 else ""
            verdict = f"两视角分歧（{p1_ys}视角：{v1} / {p2_ys}视角：{v2}）"
            tone = (
                "两个用神角度给出不同信号，宜谨慎研判，\n"
                "建议以吉凶更明显的一方为主，结合问卦人实际情况综合判断。"
            )

        # Deduplicate yingqi across perspectives
        seen: set = set()
        yingqi_lines = []
        for p in perspectives:
            for yq in (p.yingqi_results or []):
                key = yq["position"]
                if key not in seen:
                    seen.add(key)
                    yingqi_lines.append(yq)

    else:
        jx = analysis.jixiong_result
        ji_xiong = jx.get("ji_xiong", "平")
        pattern  = jx.get("pattern", "")
        verdict_map = {"吉": "吉——事可成", "凶": "凶——事难成", "平": "平——尚待观望"}
        verdict = verdict_map.get(ji_xiong, ji_xiong)
        tone = GUA_JU_BAIHUA.get(pattern, jx.get("explanation", ""))
        yingqi_lines = analysis.yingqi_results or []

    return {"verdict": verdict, "tone": tone, "yingqi_lines": yingqi_lines}
