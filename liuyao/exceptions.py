"""
六爻分析系统自定义异常 - Custom Exception Hierarchy
"""


class LiuyaoError(Exception):
    """六爻分析系统基础异常"""
    pass


class ArrangementError(LiuyaoError, ValueError):
    """排卦错误 - Error during hexagram arrangement

    Inherits from ValueError for backward compatibility.
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
