"""
分析编排器 - Analysis Orchestrator

整合旺衰分析、动变分析、吉凶判断、应期推断, 生成完整分析报告。
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
from .yingqi import analyze_yingqi


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
    jixiong_result: Dict = field(default_factory=dict)
    yingqi_results: List[Dict] = field(default_factory=list)

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

    # 4. 吉凶判断
    report.jixiong_result = judge_jixiong(
        hexagram, report.yong_shen_liu_qin,
        report.wangshuai_results, report.dongbian_results,
        question_type
    )

    # 5. 应期推断
    report.yingqi_results = analyze_yingqi(
        hexagram, report.yong_shen_lines,
        report.wangshuai_results, report.dongbian_results
    )

    return report
