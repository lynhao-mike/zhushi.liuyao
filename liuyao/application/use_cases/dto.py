"""
分析用例 DTO。

保持分析结果的数据结构独立，避免在编排逻辑文件里同时承载 DTO 定义。
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from liuyao.domain.hexagram import Hexagram


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
