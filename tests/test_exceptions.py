"""
自定义异常测试 - Custom Exception Hierarchy Tests

验证异常继承关系、向后兼容性、以及排卦时的异常行为。
"""

import pytest
from liuyao.exceptions import LiuyaoError, ArrangementError, AnalysisError, CalendarError
from liuyao.hexagram import Hexagram


class TestExceptionHierarchy:
    """测试异常继承关系"""

    def test_arrangement_error_is_liuyao_error(self):
        """ArrangementError 是 LiuyaoError 的子类"""
        assert issubclass(ArrangementError, LiuyaoError)

    def test_arrangement_error_is_value_error(self):
        """ArrangementError 是 ValueError 的子类（向后兼容）"""
        assert issubclass(ArrangementError, ValueError)

    def test_analysis_error_is_liuyao_error(self):
        """AnalysisError 是 LiuyaoError 的子类"""
        assert issubclass(AnalysisError, LiuyaoError)

    def test_analysis_error_not_value_error(self):
        """AnalysisError 不是 ValueError 的子类"""
        assert not issubclass(AnalysisError, ValueError)

    def test_calendar_error_is_liuyao_error(self):
        """CalendarError 是 LiuyaoError 的子类"""
        assert issubclass(CalendarError, LiuyaoError)

    def test_calendar_error_is_value_error(self):
        """CalendarError 是 ValueError 的子类（向后兼容）"""
        assert issubclass(CalendarError, ValueError)

    def test_liuyao_error_is_exception(self):
        """LiuyaoError 是 Exception 的子类"""
        assert issubclass(LiuyaoError, Exception)

    def test_isinstance_arrangement_error(self):
        """ArrangementError 实例同时是 LiuyaoError 和 ValueError"""
        err = ArrangementError("test")
        assert isinstance(err, LiuyaoError)
        assert isinstance(err, ValueError)
        assert isinstance(err, Exception)

    def test_isinstance_calendar_error(self):
        """CalendarError 实例同时是 LiuyaoError 和 ValueError"""
        err = CalendarError("test")
        assert isinstance(err, LiuyaoError)
        assert isinstance(err, ValueError)
        assert isinstance(err, Exception)

    def test_isinstance_analysis_error(self):
        """AnalysisError 实例是 LiuyaoError 但不是 ValueError"""
        err = AnalysisError("test")
        assert isinstance(err, LiuyaoError)
        assert not isinstance(err, ValueError)


class TestBackwardCompatibility:
    """测试向后兼容性：catching ValueError 仍然有效"""

    def test_catch_arrangement_error_as_value_error(self):
        """用 ValueError 可以捕获 ArrangementError"""
        with pytest.raises(ValueError):
            raise ArrangementError("test error")

    def test_catch_calendar_error_as_value_error(self):
        """用 ValueError 可以捕获 CalendarError"""
        with pytest.raises(ValueError):
            raise CalendarError("test error")

    def test_catch_arrangement_error_as_liuyao_error(self):
        """用 LiuyaoError 可以捕获 ArrangementError"""
        with pytest.raises(LiuyaoError):
            raise ArrangementError("test error")

    def test_invalid_yao_raises_arrangement_error_caught_as_valueerror(self):
        """无效摇卦值触发的 ArrangementError 可被 ValueError 捕获"""
        with pytest.raises(ValueError):
            Hexagram([1, 2, 3, 4, 5, 6], 2024, 1, 1)


class TestArrangementErrorRaised:
    """测试排卦时触发 ArrangementError"""

    def test_invalid_yao_values(self):
        """无效摇卦值触发 ArrangementError"""
        with pytest.raises(ArrangementError):
            Hexagram([1, 2, 3, 4, 5, 6], 2024, 1, 1)

    def test_invalid_month(self):
        """无效月份触发 ArrangementError"""
        with pytest.raises(ArrangementError):
            Hexagram([7, 7, 7, 7, 7, 7], 2024, 13, 1)

    def test_invalid_day(self):
        """无效日期触发 ArrangementError"""
        with pytest.raises(ArrangementError):
            Hexagram([7, 7, 7, 7, 7, 7], 2024, 1, 32)

    def test_invalid_year_zero(self):
        """无效年份触发 ArrangementError"""
        with pytest.raises(ArrangementError):
            Hexagram([7, 7, 7, 7, 7, 7], 0, 1, 1)

    def test_non_leap_year_feb29(self):
        """非闰年2月29日触发 ArrangementError"""
        with pytest.raises(ArrangementError):
            Hexagram([7, 7, 7, 7, 7, 7], 2023, 2, 29)

    def test_error_message_preserved(self):
        """错误信息内容不变"""
        with pytest.raises(ArrangementError, match="无效摇卦值"):
            Hexagram([1, 7, 7, 7, 7, 7], 2024, 1, 1)

    def test_invalid_month_message(self):
        """月份错误信息内容不变"""
        with pytest.raises(ArrangementError, match="无效月份"):
            Hexagram([7, 7, 7, 7, 7, 7], 2024, 13, 1)


class TestExceptionImportFromPackage:
    """测试从 liuyao 包顶层导入异常类"""

    def test_import_from_package(self):
        """可以从 liuyao 包顶层导入所有异常类"""
        from liuyao import LiuyaoError, ArrangementError, AnalysisError, CalendarError
        assert LiuyaoError is not None
        assert ArrangementError is not None
        assert AnalysisError is not None
        assert CalendarError is not None
