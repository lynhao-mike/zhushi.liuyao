"""
六爻排卦分析系统 - Liu Yao (Six-Line) Divination Analysis System

基于《古筮真诠》理论体系的纳甲六爻自动排卦与断卦引擎。

公开 API:
    Hexagram            排卦核心对象
    run_analysis        单视角完整分析
    run_dual_analysis   双(多)视角分析（失物、问病等多用神场景）
    format_report       单视角报告格式化为文本
    format_dual_report  双视角报告格式化为文本

快速使用:
    from liuyao import Hexagram, run_analysis, format_report

    h = Hexagram([9, 8, 7, 9, 6, 6], 2026, 5, 25, hour=14)
    report = run_analysis(h, "shiwu")
    print(format_report(report))

双视角使用（失物/问病）:
    from liuyao import Hexagram, run_dual_analysis, format_dual_report

    h = Hexagram([9, 8, 7, 9, 6, 6], 2026, 5, 25, hour=14)
    dual = run_dual_analysis(h, "shiwu")
    print(format_dual_report(dual))
"""

__version__ = "0.2.0"

from .hexagram import Hexagram, YaoLine
from .analyzer import (
    run_analysis,
    run_dual_analysis,
    AnalysisReport,
    DualPerspectiveReport,
)
from .report import format_report, format_dual_report

__all__ = [
    "Hexagram",
    "YaoLine",
    "run_analysis",
    "run_dual_analysis",
    "AnalysisReport",
    "DualPerspectiveReport",
    "format_report",
    "format_dual_report",
]
