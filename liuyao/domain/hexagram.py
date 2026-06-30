"""
六爻排卦引擎 - Hexagram Arrangement Engine

根据摇卦结果(6次铜钱结果)和日期, 生成完整的六爻卦象。
包括纳甲、六亲、世应、六神、旬空等所有标注。
"""

import calendar
from dataclasses import dataclass, field

from .calendar_utils import derive_day_gan, get_gan_zhi
from .data import (
    BINARY_TO_GUA,
    DI_ZHI,
    DI_ZHI_WU_XING,
    HEXAGRAM_BY_TRIGRAMS,
    NA_JIA,
    PALACE_SHI_YING,
    PALACE_WU_XING,
    TIAN_GAN,
    get_liu_qin,
    get_liu_shen,
    get_xun_kong,
)
from .exceptions import ArrangementError


@dataclass
class YaoLine:
    """单爻信息"""
    position: int          # 爻位 1-6 (从下到上)
    yao_type: int          # 原始摇卦值: 6=老阴, 7=少阳, 8=少阴, 9=老阳
    yin_yang: int           # 阴阳: 1=阳, 0=阴
    is_moving: bool        # 是否动爻
    tian_gan: str          # 纳甲天干
    di_zhi: str            # 纳甲地支
    wu_xing: str           # 地支五行
    liu_qin: str           # 六亲
    liu_shen: str          # 六神
    is_shi: bool = False   # 是否世爻
    is_ying: bool = False  # 是否应爻
    is_xun_kong: bool = False  # 是否旬空

    # 变爻信息 (仅动爻有)
    bian_tian_gan: str | None = None
    bian_di_zhi: str | None = None
    bian_wu_xing: str | None = None
    bian_liu_qin: str | None = None


@dataclass
class Hexagram:
    """
    六爻卦象完整信息。

    使用方法:
        h = Hexagram([8, 7, 7, 9, 7, 8], 2024, 1, 15)
        h.display()
    """
    yao_values: list[int]   # 6个摇卦值 [初爻, ..., 上爻]
    year: int
    month: int
    day: int
    hour: int = 12

    # 干支注入 (可选)。提供时跳过公历->sxtwl 推导, 直接采用注入的干支。
    # 用于古籍卦例复盘(只知"X月Y日"干支)或脱离 sxtwl 的确定性测试。
    # 期望键: month_zhi, day_zhi, day_gan (必需);
    #         year_gan, year_zhi, month_gan, xun_kong (可选)。
    gan_zhi_override: dict | None = None

    # 排卦结果
    ben_gua_name: str = ""       # 本卦名称
    bian_gua_name: str = ""      # 变卦名称
    palace_name: str = ""        # 所属宫
    palace_wu_xing: str = ""     # 宫五行
    palace_order: int = 0        # 宫内序号

    lines: list[YaoLine] = field(default_factory=list)
    gan_zhi: dict = field(default_factory=dict)
    xun_kong: tuple[str, str] = ("", "")
    shi_pos: int = 0
    ying_pos: int = 0

    # 高频分析索引: 排卦后构建一次, 后续旺衰/动变/吉凶/应期复用。
    lines_by_position: dict[int, YaoLine] = field(default_factory=dict, init=False)
    lines_by_liu_qin: dict[str, list[YaoLine]] = field(default_factory=dict, init=False)
    moving_lines: list[YaoLine] = field(default_factory=list, init=False)
    static_lines: list[YaoLine] = field(default_factory=list, init=False)
    shi_line: YaoLine | None = field(default=None, init=False)
    ying_line: YaoLine | None = field(default=None, init=False)

    def __post_init__(self):
        """初始化后自动排卦"""
        if self.gan_zhi_override is None:
            self._validate_date()
        self._arrange()

    def __repr__(self) -> str:  # pragma: no cover
        gz = self.gan_zhi
        return (
            f"<Hexagram {self.ben_gua_name!r} "
            f"{gz.get('month_gan','')}{gz.get('month_zhi','')}月 "
            f"{gz.get('day_gan','')}{gz.get('day_zhi','')}日>"
        )

    @classmethod
    def from_ganzhi(cls, yao_values, *, month_zhi, day_zhi, day_gan=None,
                    xun_kong=None, year_gan="甲", year_zhi="子",
                    month_gan="甲", hour=12):
        """
        由干支直接构建卦象 (不依赖公历日期 / sxtwl)。

        适用于:
          - 复盘古籍卦例(原文常只记"辰月申日"之类干支与旬空, 无公历日期)
          - 需要精确控制日月干支的确定性单元测试

        Args:
            yao_values: 6个摇卦值 [初爻..上爻]
            month_zhi: 月支(月建), 必需
            day_zhi: 日支(日辰), 必需
            day_gan: 日干。若为 None 则尝试由 (day_zhi, xun_kong) 反推
            xun_kong: 旬空地支(长度2)。day_gan 缺省时用于反推日干;
                      若同时给出 day_gan, 则作为显式旬空覆盖计算值
            year_gan/year_zhi/month_gan: 年月柱(仅用于展示, 不影响吉凶), 可缺省
            hour: 时辰(0-23)

        Returns:
            Hexagram
        """
        if day_gan is None:
            if xun_kong is None:
                raise ArrangementError("from_ganzhi 需提供 day_gan 或 xun_kong 之一")
            day_gan = derive_day_gan(day_zhi, xun_kong)

        override = {
            "year_gan": year_gan, "year_zhi": year_zhi,
            "month_gan": month_gan, "month_zhi": month_zhi,
            "day_gan": day_gan, "day_zhi": day_zhi,
        }
        if xun_kong is not None:
            override["xun_kong"] = tuple(xun_kong)

        # 使用占位公历日期(不参与计算, 仅满足字段); 注入存在时跳过日期校验
        return cls(yao_values, 2000, 1, 1, hour=hour, gan_zhi_override=override)

    def _validate_date(self):
        """验证日期参数的基本范围"""
        if not isinstance(self.year, int) or self.year < 1 or self.year > 9999:
            raise ArrangementError(f"无效年份: {self.year}, 必须为1-9999的整数")
        if not isinstance(self.month, int) or self.month < 1 or self.month > 12:
            raise ArrangementError(f"无效月份: {self.month}, 必须为1-12的整数")
        max_day = calendar.monthrange(self.year, self.month)[1]
        if not isinstance(self.day, int) or self.day < 1 or self.day > max_day:
            raise ArrangementError(
                f"无效日期: {self.year}年{self.month}月{self.day}日, "
                f"日必须为1-{max_day}的整数"
            )

    def _normalize_ganzhi(self, override):
        """
        校验并补全注入的干支字典。

        必需键: month_zhi, day_zhi, day_gan。
        缺失的年月柱以占位值补全(不影响吉凶, 仅用于展示)。
        """
        required = ("month_zhi", "day_zhi", "day_gan")
        missing = [k for k in required if not override.get(k)]
        if missing:
            raise ArrangementError(f"注入干支缺少必需键: {missing}")

        for key, val in (("day_gan", override["day_gan"]),):
            if val not in TIAN_GAN:
                raise ArrangementError(f"无效天干 {key}={val}")
        for key in ("month_zhi", "day_zhi"):
            if override[key] not in DI_ZHI:
                raise ArrangementError(f"无效地支 {key}={override[key]}")

        return {
            "year_gan": override.get("year_gan", "甲"),
            "year_zhi": override.get("year_zhi", "子"),
            "month_gan": override.get("month_gan", "甲"),
            "month_zhi": override["month_zhi"],
            "day_gan": override["day_gan"],
            "day_zhi": override["day_zhi"],
        }

    def _arrange(self):
        """执行完整排卦流程"""
        # 1. 获取干支 (注入优先, 否则按公历推导)
        if self.gan_zhi_override is not None:
            self.gan_zhi = self._normalize_ganzhi(self.gan_zhi_override)
        else:
            self.gan_zhi = get_gan_zhi(self.year, self.month, self.day, self.hour)

        # 2. 确定本卦和变卦的阴阳
        ben_lines = []
        bian_lines = []
        for val in self.yao_values:
            if val == 9:       # 老阳 -> 阳动变阴
                ben_lines.append(1)
                bian_lines.append(0)
            elif val == 6:     # 老阴 -> 阴动变阳
                ben_lines.append(0)
                bian_lines.append(1)
            elif val == 7:     # 少阳 -> 阳静
                ben_lines.append(1)
                bian_lines.append(1)
            elif val == 8:     # 少阴 -> 阴静
                ben_lines.append(0)
                bian_lines.append(0)
            else:
                raise ArrangementError(f"无效摇卦值: {val}, 必须为6/7/8/9")

        # 3. 确定上下卦
        lower_binary = tuple(ben_lines[0:3])
        upper_binary = tuple(ben_lines[3:6])
        lower_name = BINARY_TO_GUA[lower_binary]
        upper_name = BINARY_TO_GUA[upper_binary]

        # 4. 查找本卦信息
        ben_info = HEXAGRAM_BY_TRIGRAMS[(upper_name, lower_name)]
        self.ben_gua_name = ben_info["name"]
        self.palace_name = ben_info["palace"]
        self.palace_wu_xing = PALACE_WU_XING[self.palace_name]
        self.palace_order = ben_info["palace_order"]

        # 5. 确定变卦
        bian_lower_binary = tuple(bian_lines[0:3])
        bian_upper_binary = tuple(bian_lines[3:6])
        bian_lower_name = BINARY_TO_GUA[bian_lower_binary]
        bian_upper_name = BINARY_TO_GUA[bian_upper_binary]
        bian_info = HEXAGRAM_BY_TRIGRAMS[(bian_upper_name, bian_lower_name)]
        self.bian_gua_name = bian_info["name"]

        # 6. 确定世应位置
        shi_ying = PALACE_SHI_YING[self.palace_order]
        self.shi_pos = shi_ying[0]
        self.ying_pos = shi_ying[1]

        # 7. 计算旬空 (注入可显式覆盖)
        override_kong = (self.gan_zhi_override or {}).get("xun_kong")
        if override_kong is not None:
            self.xun_kong = tuple(override_kong)
        else:
            self.xun_kong = get_xun_kong(
                self.gan_zhi["day_gan"], self.gan_zhi["day_zhi"]
            )

        # 8. 获取六神
        liu_shen_list = get_liu_shen(self.gan_zhi["day_gan"])

        # 9. 纳甲 - 为每爻赋予天干地支
        lower_na_jia = NA_JIA[lower_name]
        upper_na_jia = NA_JIA[upper_name]

        # 变卦纳甲
        bian_lower_na_jia = NA_JIA[bian_lower_name]
        bian_upper_na_jia = NA_JIA[bian_upper_name]

        # 10. 构建每爻信息
        self.lines = []
        for i in range(6):
            pos = i + 1  # 爻位 1-6

            # 本卦纳甲
            if i < 3:
                tian_gan = lower_na_jia[0]
                di_zhi = lower_na_jia[1][i]
            else:
                tian_gan = upper_na_jia[0]
                di_zhi = upper_na_jia[2][i - 3]

            wu_xing = DI_ZHI_WU_XING[di_zhi]
            liu_qin_val = get_liu_qin(self.palace_wu_xing, wu_xing)

            # 动爻判断
            is_moving = (self.yao_values[i] == 6 or self.yao_values[i] == 9)

            # 变爻纳甲
            bian_tg = None
            bian_dz = None
            bian_wx = None
            bian_lq = None
            if is_moving:
                if i < 3:
                    bian_tg = bian_lower_na_jia[0]
                    bian_dz = bian_lower_na_jia[1][i]
                else:
                    bian_tg = bian_upper_na_jia[0]
                    bian_dz = bian_upper_na_jia[2][i - 3]
                bian_wx = DI_ZHI_WU_XING[bian_dz]
                bian_lq = get_liu_qin(self.palace_wu_xing, bian_wx)

            line = YaoLine(
                position=pos,
                yao_type=self.yao_values[i],
                yin_yang=ben_lines[i],
                is_moving=is_moving,
                tian_gan=tian_gan,
                di_zhi=di_zhi,
                wu_xing=wu_xing,
                liu_qin=liu_qin_val,
                liu_shen=liu_shen_list[i],
                is_shi=(pos == self.shi_pos),
                is_ying=(pos == self.ying_pos),
                is_xun_kong=(di_zhi in self.xun_kong),
                bian_tian_gan=bian_tg,
                bian_di_zhi=bian_dz,
                bian_wu_xing=bian_wx,
                bian_liu_qin=bian_lq,
            )
            self.lines.append(line)

        self._build_analysis_indexes()

    def _build_analysis_indexes(self):
        """构建分析期高频查找索引, 避免各模块重复扫描六爻。"""
        self.lines_by_position = {line.position: line for line in self.lines}
        self.lines_by_liu_qin = {}
        self.moving_lines = []
        self.static_lines = []
        self.shi_line = None
        self.ying_line = None

        for line in self.lines:
            self.lines_by_liu_qin.setdefault(line.liu_qin, []).append(line)
            if line.is_moving:
                self.moving_lines.append(line)
            else:
                self.static_lines.append(line)
            if line.is_shi:
                self.shi_line = line
            if line.is_ying:
                self.ying_line = line

    def display(self):
        """以传统格式显示排卦结果"""
        print("=" * 60)
        print(f"  本卦: {self.ben_gua_name}  ({self.palace_name}宫 - {self.palace_wu_xing})")
        print(f"  变卦: {self.bian_gua_name}")
        print(f"  日期: {self.year}年{self.month}月{self.day}日")
        print(f"  干支: {self.gan_zhi['year_gan']}{self.gan_zhi['year_zhi']}年"
              f" {self.gan_zhi['month_gan']}{self.gan_zhi['month_zhi']}月"
              f" {self.gan_zhi['day_gan']}{self.gan_zhi['day_zhi']}日")
        print(f"  旬空: {self.xun_kong[0]}{self.xun_kong[1]}")
        print("=" * 60)
        print()

        # 从上爻到初爻显示 (传统顺序)
        print(f"{'六神':<6}{'本卦':<20}{'变卦'}")
        print("-" * 60)

        for line in reversed(self.lines):
            # 爻符号
            if line.yin_yang == 1:
                yao_sym = "-------"  # 阳爻
            else:
                yao_sym = "-- -- --"  # 阴爻

            # 动爻标记
            dong_mark = "○" if (line.is_moving and line.yin_yang == 1) else \
                        "×" if (line.is_moving and line.yin_yang == 0) else " "

            # 世应标记
            shi_ying_mark = "世" if line.is_shi else "应" if line.is_ying else "  "

            # 旬空标记
            kong_mark = "空" if line.is_xun_kong else "  "

            # 变爻信息
            bian_str = ""
            if line.is_moving:
                bian_sym = "-- -- --" if line.yin_yang == 1 else "-------"
                bian_str = f"{bian_sym} {line.bian_liu_qin}{line.bian_tian_gan}{line.bian_di_zhi}{DI_ZHI_WU_XING[line.bian_di_zhi]}"

            # 主行
            line_str = (
                f"{line.liu_shen:<4}"
                f" {line.liu_qin}{line.tian_gan}{line.di_zhi}{line.wu_xing}"
                f" {yao_sym} {dong_mark}"
                f" {shi_ying_mark} {kong_mark}"
            )
            if bian_str:
                line_str += f"  -> {bian_str}"

            print(line_str)

        print()
        print("=" * 60)
        # 标注说明
        moving_lines = [l for l in self.lines if l.is_moving]
        if moving_lines:
            print("  动爻: ", end="")
            for l in moving_lines:
                print(f"第{l.position}爻({l.di_zhi})", end=" ")
            print()
