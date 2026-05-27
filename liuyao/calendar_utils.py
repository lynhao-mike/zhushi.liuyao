"""
干支历法工具 - Gan-Zhi Calendar Utilities

使用 sxtwl 库将公历日期转换为干支纪年纪月纪日。
处理节气换月、年柱以立春为界等特殊规则。
"""

import sxtwl
from .data import TIAN_GAN, DI_ZHI
from .exceptions import CalendarError, LiuyaoError


def get_gan_zhi(year, month, day, hour=12):
    """
    获取指定日期的年月日干支。

    Args:
        year: 公历年
        month: 公历月
        day: 公历日
        hour: 小时(0-23), 用于判断子时归属, 默认12(午时)

    Returns:
        dict: {
            "year_gan": 年干, "year_zhi": 年支,
            "month_gan": 月干, "month_zhi": 月支,
            "day_gan": 日干, "day_zhi": 日支,
        }

    Note:
        - 年柱以立春为界(sxtwl已处理)
        - 月柱以节气为界(sxtwl已处理)
        - 23:00-次日01:00 为子时, 但日柱以子时(23:00)换日
          sxtwl 默认以0点换日, 此处做特殊处理
    """
    try:
        if hour >= 23:
            from datetime import date, timedelta
            next_date = date(year, month, day) + timedelta(days=1)
            day_obj = sxtwl.fromSolar(next_date.year, next_date.month, next_date.day)
        else:
            day_obj = sxtwl.fromSolar(year, month, day)

        year_gz = day_obj.getYearGZ()
        year_gan = TIAN_GAN[year_gz.tg]
        year_zhi = DI_ZHI[year_gz.dz]

        month_gz = day_obj.getMonthGZ()
        month_gan = TIAN_GAN[month_gz.tg]
        month_zhi = DI_ZHI[month_gz.dz]

        day_gz = day_obj.getDayGZ()
        day_gan = TIAN_GAN[day_gz.tg]
        day_zhi = DI_ZHI[day_gz.dz]

        return {
            "year_gan": year_gan, "year_zhi": year_zhi,
            "month_gan": month_gan, "month_zhi": month_zhi,
            "day_gan": day_gan, "day_zhi": day_zhi,
        }
    except (LiuyaoError, ValueError):
        raise
    except Exception as e:
        raise CalendarError(f"干支计算失败({year}-{month}-{day}): {e}") from e


def get_month_zhi(year, month, day):
    """获取月支 (月建), 用于旺衰判断"""
    gz = get_gan_zhi(year, month, day)
    return gz["month_zhi"]


def get_day_zhi(year, month, day):
    """获取日支 (日辰), 用于旺衰判断"""
    gz = get_gan_zhi(year, month, day)
    return gz["day_zhi"]
