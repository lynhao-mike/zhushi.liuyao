"""
分析编排器 - Analysis Orchestrator

整合旺衰分析、动变分析、连动分析、吉凶判断、应期推断, 生成完整分析报告。
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional

from .hexagram import Hexagram
from .wangshuai import analyze_hexagram_wangshuai
from .dongbian import analyze_dongbian
from .jixiong import (
    judge_jixiong, determine_yong_shen,
    find_yong_shen_lines, find_shi_line,
)
from .yingqi import analyze_yingqi, classify_event_duration
from .liuchong_liuhe import analyze_liuchong_liuhe
from .xunkong import analyze_xunkong
from .yuepo import analyze_yuepo
from .liandong import analyze_liandong
from .guayi import analyze_guayi
from .shiyao_rules import analyze_shiyao_dongbian


@dataclass
class AnalysisReport:
    """分析报告数据结构"""
    # 基本信息
    hexagram: Hexagram = None
    question_type: str = ""
    yong_shen_liu_qin: str = ""

    # 分析结果
    wangshuai_results: List[Dict] = field(default_factory=list)
    dongbian_results: Dict = field(default_factory=dict)
    liandong_results: Dict = field(default_factory=dict)
    jixiong_result: Dict = field(default_factory=dict)
    yingqi_results: List[Dict] = field(default_factory=list)
    liuchong_liuhe_results: Dict = field(default_factory=dict)
    xunkong_results: Dict = field(default_factory=dict)
    yuepo_results: Dict = field(default_factory=dict)
    guayi_results: list = field(default_factory=list)
    shiyao_analysis: Optional[Dict] = None

    # 用神信息
    yong_shen_lines: List = field(default_factory=list)
    shi_line: Optional[object] = None


def run_analysis(hexagram, question_type="other"):
    """
    执行完整六爻分析流程。

    Args:
        hexagram: 已排好的Hexagram对象
        question_type: 问事类型
            cai - 财运
            guan - 官运/工作
            hun_male - 婚姻(男问)
            hun_female - 婚姻(女问)
            bing - 疾病
            kaoshi - 考试/文书
            zinv - 子女
            xingRen - 行人
            youHuan - 忧患
            other - 其他

    Returns:
        AnalysisReport: 完整分析报告
    """
    report = AnalysisReport()
    report.hexagram = hexagram
    report.question_type = question_type

    # 1. 确定用神
    report.yong_shen_liu_qin = determine_yong_shen(question_type)
    report.yong_shen_lines = find_yong_shen_lines(hexagram, report.yong_shen_liu_qin)
    report.shi_line = find_shi_line(hexagram)

    # 2. 旺衰分析
    report.wangshuai_results = analyze_hexagram_wangshuai(hexagram)

    # 3. 动变分析
    report.dongbian_results = analyze_dongbian(hexagram, report.wangshuai_results)

    # 3.5 连动分析(在动变之后, 吉凶之前)
    report.liandong_results = analyze_liandong(
        hexagram, report.dongbian_results, report.wangshuai_results,
        report.yong_shen_lines, report.shi_line, question_type
    )

    # 4. 吉凶判断
    report.jixiong_result = judge_jixiong(
        hexagram, report.yong_shen_liu_qin,
        report.wangshuai_results, report.dongbian_results,
        question_type, liandong_results=report.liandong_results
    )

    # 4.5 六冲六合分析(移至应期前, 供应期参考)
    report.liuchong_liuhe_results = analyze_liuchong_liuhe(
        hexagram, report.dongbian_results, report.wangshuai_results
    )

    # 5. 应期推断
    report.yingqi_results = analyze_yingqi(
        hexagram, report.yong_shen_lines,
        report.wangshuai_results, report.dongbian_results,
        event_duration=classify_event_duration(question_type),
        jixiong_result=report.jixiong_result,
        liuchong_liuhe_results=report.liuchong_liuhe_results
    )

    # 5.5 卦意分析(解读层)
    report.guayi_results = analyze_guayi(
        hexagram, report.dongbian_results, report.wangshuai_results,
        report.yong_shen_liu_qin, question_type,
        report.shi_line, report.yong_shen_lines
    )

    # 5.6 世爻特殊规则
    if report.shi_line and report.shi_line.is_moving:
        report.shiyao_analysis = analyze_shiyao_dongbian(
            hexagram, report.shi_line, report.dongbian_results,
            report.wangshuai_results, report.yong_shen_liu_qin
        )

    # 7. 旬空分析
    report.xunkong_results = analyze_xunkong(
        hexagram, report.yong_shen_liu_qin, question_type,
        report.wangshuai_results
    )

    # 8. 月破真假分析
    report.yuepo_results = analyze_yuepo(
        hexagram, report.dongbian_results, report.wangshuai_results
    )

    return report
