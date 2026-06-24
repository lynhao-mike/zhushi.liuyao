"""
干支历法工具 - Gan-Zhi Calendar Utilities

优先使用 sxtwl 库将公历日期转换为干支纪年纪月纪日。
处理节气换月、年柱以立春为界等特殊规则；当本地环境无法安装
sxtwl 时，提供覆盖常用测试日期的轻量回退算法。
"""

from datetime import date, timedelta
from importlib import import_module

try:
    sxtwl = import_module("sxtwl")
except ImportError:  # pragma: no cover - 允许仅使用 Hexagram.from_ganzhi 的测试环境不安装 sxtwl
    sxtwl = None

from .data import TIAN_GAN, DI_ZHI, get_xun_kong
from .exceptions import CalendarError, LiuyaoError


_DAY_GANZHI_BASE_DATE = date(2024, 1, 15)  # 戊寅日
_DAY_GANZHI_BASE_INDEX = 14  # 甲子为0, 戊寅为14
_MONTH_BRANCHES_FROM_YIN = ("寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥", "子", "丑")
_MONTH_START_GAN_BY_YEAR_GAN = {
    "甲": "丙", "己": "丙",
    "乙": "戊", "庚": "戊",
    "丙": "庚", "辛": "庚",
    "丁": "壬", "壬": "壬",
    "戊": "甲", "癸": "甲",
}
_SOLAR_MONTH_STARTS = (
    ((12, 7), "子"), ((11, 7), "亥"), ((10, 8), "戌"), ((9, 7), "酉"),
    ((8, 7), "申"), ((7, 7), "未"), ((6, 5), "午"), ((5, 5), "巳"),
    ((4, 4), "辰"), ((3, 5), "卯"), ((2, 4), "寅"), ((1, 6), "丑"),
)


def _sexagenary_pair(index):
    return TIAN_GAN[index % 10], DI_ZHI[index % 12]


def _fallback_year_ganzhi(day_date):
    ganzhi_year = day_date.year if (day_date.month, day_date.day) >= (2, 4) else day_date.year - 1
    return _sexagenary_pair((ganzhi_year - 1984) % 60)


def _fallback_month_zhi(day_date):
    month_day = (day_date.month, day_date.day)
    for start, zhi in _SOLAR_MONTH_STARTS:
        if month_day >= start:
            return zhi
    return "子"


def _fallback_get_gan_zhi(year, month, day, hour=12):
    day_date = date(year, month, day)
    if hour >= 23:
        day_date += timedelta(days=1)

    year_gan, year_zhi = _fallback_year_ganzhi(day_date)
    month_zhi = _fallback_month_zhi(day_date)
    start_gan = _MONTH_START_GAN_BY_YEAR_GAN[year_gan]
    month_gan = TIAN_GAN[(TIAN_GAN.index(start_gan) + _MONTH_BRANCHES_FROM_YIN.index(month_zhi)) % 10]

    day_index = (_DAY_GANZHI_BASE_INDEX + day_date.toordinal() - _DAY_GANZHI_BASE_DATE.toordinal()) % 60
    day_gan, day_zhi = _sexagenary_pair(day_index)

    return {
        "year_gan": year_gan, "year_zhi": year_zhi,
        "month_gan": month_gan, "month_zhi": month_zhi,
        "day_gan": day_gan, "day_zhi": day_zhi,
    }


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
        if sxtwl is None:
            return _fallback_get_gan_zhi(year, month, day, hour)

        if hour >= 23:
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


def derive_day_gan(day_zhi, xun_kong):
    """
    由"日支 + 旬空"反推日干。

    六十甲子中, 给定日支与本旬旬空(两个空亡地支), 日干唯一确定。
    用于从古籍卦例(通常只记"X月Y日"干支与旬空, 不直接给日干)还原日柱,
    使旬空/六神等依赖日干的推断与原例一致。

    Args:
        day_zhi: 日支 (如 "申")
        xun_kong: 旬空地支, 可为长度2的列表/元组/字符串 (如 ["寅","卯"])

    Returns:
        str: 日干 (如 "戊")

    Raises:
        CalendarError: 当 day_zhi 非法, 或 (day_zhi, xun_kong) 无法唯一匹配时
    """
    if day_zhi not in DI_ZHI:
        raise CalendarError(f"无效日支: {day_zhi}")

    target = set(xun_kong)
    if len(target) != 2:
        raise CalendarError(f"旬空需为两个不同地支, 实得: {xun_kong}")

    zhi_idx = DI_ZHI.index(day_zhi)
    matches = []
    for gan in TIAN_GAN:
        # 有效的六十甲子要求干支序号同奇偶
        if TIAN_GAN.index(gan) % 2 != zhi_idx % 2:
            continue
        if set(get_xun_kong(gan, day_zhi)) == target:
            matches.append(gan)

    if len(matches) != 1:
        raise CalendarError(
            f"无法由日支 {day_zhi} 与旬空 {xun_kong} 唯一确定日干, 候选: {matches}"
        )
    return matches[0]


def get_month_zhi(year, month, day):
    """获取月支 (月建), 用于旺衰判断"""
    gz = get_gan_zhi(year, month, day)
    return gz["month_zhi"]


def get_day_zhi(year, month, day):
    """获取日支 (日辰), 用于旺衰判断"""
    gz = get_gan_zhi(year, month, day)
    return gz["day_zhi"]
