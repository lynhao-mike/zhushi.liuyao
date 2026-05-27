"""
分析编排器 - Analysis Orchestrator

整合旺衰分析、动变分析、卦象模式识别、吉凶判断、卦意分析法、
应期推断, 生成完整分析报告。

支持单视角(run_analysis)与双视角(run_dual_analysis)两种模式。
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional

from .hexagram import Hexagram
from .data import get_star_spirits
from .wangshuai import analyze_hexagram_wangshuai
from .dongbian import analyze_dongbian
from .jixiong import (
    judge_jixiong, determine_yong_shen,
    find_yong_shen_lines, find_shi_line,
    get_dual_perspectives,
    JI_SHEN_TABLE,
)
from .yingqi import analyze_yingqi
from .patterns import analyze_all_patterns
from .fushen import analyze_fushen
from .exceptions import AnalysisError


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
    fushen_analysis: Optional[Dict] = None  # 伏神分析(仅用神不上卦时存在)
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


def _find_ying_line(hexagram):
    for line in hexagram.lines:
        if line.is_ying:
            return line
    return None


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
    report.ying_line = _find_ying_line(hexagram)

    # 2. 旺衰分析
    report.wangshuai_results = analyze_hexagram_wangshuai(hexagram)

    # 3. 动变分析
    try:
        report.dongbian_results = analyze_dongbian(hexagram, report.wangshuai_results)
    except Exception as e:
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
        report.patterns_results = {}

    # 5. 13星煞计算
    try:
        report.star_spirits = get_star_spirits(
            hexagram.gan_zhi["day_gan"],
            hexagram.gan_zhi["day_zhi"],
            hexagram.gan_zhi["month_zhi"],
        )
    except Exception:
        report.star_spirits = {}

    # 6. 伏神分析 (仅当用神不上卦时启用)
    if not report.yong_shen_lines:
        try:
            report.fushen_analysis = analyze_fushen(
                hexagram, report.yong_shen_liu_qin,
                report.wangshuai_results, report.dongbian_results,
                question_type,
            )
        except Exception:
            report.fushen_analysis = None

    # 7. 吉凶判断
    try:
        report.jixiong_result = judge_jixiong(
            hexagram, report.yong_shen_liu_qin,
            report.wangshuai_results, report.dongbian_results,
            question_type
        )
        # 注入卦意法附加判断
        kuayi_patterns = report.patterns_results.get("kuayi_patterns", [])
        if kuayi_patterns:
            report.jixiong_result["kuayi_supplements"] = kuayi_patterns
        # 注入伏神判断作为补充 (用神不上卦时)
        if report.fushen_analysis:
            report.jixiong_result["fushen_supplement"] = report.fushen_analysis
    except Exception as e:
        report.jixiong_result = {
            "pattern": "分析异常", "ji_xiong": "平",
            "explanation": f"吉凶判断过程异常: {e}",
        }

    # 8. 应期推断 (使用 patterns 结果增强 + 伏神应期)
    try:
        report.yingqi_results = analyze_yingqi(
            hexagram, report.yong_shen_lines,
            report.wangshuai_results, report.dongbian_results,
            patterns_results=report.patterns_results,
        )
        # 追加伏神应期
        if report.fushen_analysis:
            fa = report.fushen_analysis
            report.yingqi_results.append({
                "position": fa["fushen_info"]["position"],
                "di_zhi": fa["fushen_info"]["fu_di_zhi"],
                "liu_qin": f"伏神{report.yong_shen_liu_qin}",
                "candidates": fa["yingqi_candidates"],
            })
    except Exception as e:
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
    ying_line = _find_ying_line(hexagram)

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
        dual.star_spirits = {}

    # 4-7. 各视角分别完成模式/卦意/吉凶/应期
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

        # 各视角的模式识别 (用神不同, 卦意法/心态卦判定不同)
        try:
            report.patterns_results = analyze_all_patterns(
                hexagram, shared_ws, shared_db,
                yong_shen, report.ji_shen_liu_qin,
                report.yong_shen_lines, question_type,
            )
        except Exception:
            report.patterns_results = {}

        # 各视角的伏神分析 (仅用神不上卦时)
        if not report.yong_shen_lines:
            try:
                report.fushen_analysis = analyze_fushen(
                    hexagram, yong_shen, shared_ws, shared_db, question_type
                )
            except Exception:
                report.fushen_analysis = None

        try:
            report.jixiong_result = judge_jixiong(
                hexagram, yong_shen, shared_ws, shared_db, question_type
            )
            kuayi_patterns = report.patterns_results.get("kuayi_patterns", [])
            if kuayi_patterns:
                report.jixiong_result["kuayi_supplements"] = kuayi_patterns
            if report.fushen_analysis:
                report.jixiong_result["fushen_supplement"] = report.fushen_analysis
        except Exception as e:
            report.jixiong_result = {
                "pattern": "分析异常", "ji_xiong": "平",
                "explanation": f"吉凶判断过程异常: {e}",
            }

        try:
            report.yingqi_results = analyze_yingqi(
                hexagram, report.yong_shen_lines, shared_ws, shared_db,
                patterns_results=report.patterns_results,
            )
            if report.fushen_analysis:
                fa = report.fushen_analysis
                report.yingqi_results.append({
                    "position": fa["fushen_info"]["position"],
                    "di_zhi": fa["fushen_info"]["fu_di_zhi"],
                    "liu_qin": f"伏神{yong_shen}",
                    "candidates": fa["yingqi_candidates"],
                })
        except Exception as e:
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
