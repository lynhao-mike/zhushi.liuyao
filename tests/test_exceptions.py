"""
异常层级测试 - Tests for custom exception hierarchy
"""

import pytest
from liuyao.exceptions import (
    LiuyaoError,
    ArrangementError,
    AnalysisError,
    CalendarError,
)
from liuyao.hexagram import Hexagram


class TestExceptionHierarchy:
    """异常继承关系"""

    def test_arrangement_is_liuyao(self):
        assert issubclass(ArrangementError, LiuyaoError)

    def test_arrangement_is_value_error(self):
        assert issubclass(ArrangementError, ValueError)

    def test_analysis_is_liuyao(self):
        assert issubclass(AnalysisError, LiuyaoError)

    def test_calendar_is_liuyao(self):
        assert issubclass(CalendarError, LiuyaoError)

    def test_calendar_is_value_error(self):
        assert issubclass(CalendarError, ValueError)


class TestArrangementError:
    """排卦错误"""

    def test_invalid_yao_value(self):
        with pytest.raises(ArrangementError):
            Hexagram([1, 2, 3, 4, 5, 6], 2024, 1, 15)

    def test_invalid_month(self):
        with pytest.raises(ArrangementError):
            Hexagram([7, 7, 7, 7, 7, 7], 2024, 13, 15)

    def test_invalid_day(self):
        with pytest.raises(ArrangementError):
            Hexagram([7, 7, 7, 7, 7, 7], 2024, 1, 32)

    def test_backward_compat_value_error(self):
        """ValueError still catches ArrangementError"""
        with pytest.raises(ValueError):
            Hexagram([1, 2, 3, 4, 5, 6], 2024, 1, 15)
