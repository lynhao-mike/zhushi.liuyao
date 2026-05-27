"""
六爻分析系统自定义异常 - Custom Exception Hierarchy

提供分层异常类型，便于调用方精确捕获和处理不同类型的错误。
"""


class LiuyaoError(Exception):
    """六爻分析系统基础异常 - Base exception for Liu Yao system"""
    pass


class ArrangementError(LiuyaoError, ValueError):
    """排卦错误 - Error during hexagram arrangement

    Inherits from ValueError for backward compatibility with existing
    code that catches ValueError.
    """
    pass


class AnalysisError(LiuyaoError):
    """分析错误 - Error during analysis computation"""
    pass


class CalendarError(LiuyaoError, ValueError):
    """历法计算错误 - Error in calendar/Gan-Zhi computation

    Inherits from ValueError for backward compatibility.
    """
    pass
