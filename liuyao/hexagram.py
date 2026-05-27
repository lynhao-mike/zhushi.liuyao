"""
六爻排卦引擎 - Hexagram Arrangement Engine

根据摇卦结果(6次铜钱结果)和日期, 生成完整的六爻卦象。
包括纳甲、六亲、世应、六神、旬空等所有标注。
"""

from dataclasses import dataclass, field
from typing import List, Tuple, Optional

from .data import (
    TIAN_GAN, DI_ZHI, DI_ZHI_WU_XING,
    BA_GUA, BINARY_TO_GUA, NA_JIA,
    HEXAGRAM_BY_TRIGRAMS, HEXAGRAM_BY_NAME,
    PALACE_SHI_YING, PALACE_WU_XING,
    get_liu_qin, get_liu_shen, get_xun_kong,
)
from .calendar_utils import get_gan_zhi
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
    bian_tian_gan: Optional[str] = None
    bian_di_zhi: Optional[str] = None
    bian_wu_xing: Optional[str] = None
    bian_liu_qin: Optional[str] = None


@dataclass
class CangYao:
    """
    藏爻 - 主卦下藏伏的本宫纯卦对应位置之爻。

    据《古筮真诠》第三十九章: 藏爻是把整个本宫纯卦的爻套入主卦相应爻位之下,
    用于补全五行六亲缺漏, 同时也是细节分析层面"读心术"的重要工具。

    伏神 = 藏爻中被取为用神者; 伏爻 = 藏爻中作为补缺存在但非用神者。
    """
    position: int          # 爻位 1-6
    tian_gan: str          # 纳甲天干 (本宫纯卦的纳甲)
    di_zhi: str            # 纳甲地支
    wu_xing: str           # 地支五行
    liu_qin: str           # 六亲 (与本宫五行计算)
    is_xun_kong: bool = False  # 是否旬空 (藏爻也受日令旬空影响)


@dataclass
class Hexagram:
    """
    六爻卦象完整信息。

    使用方法:
        h = Hexagram([8, 7, 7, 9, 7, 8], 2024, 1, 15)
        h.display()
    """
    yao_values: List[int]   # 6个摇卦值 [初爻, ..., 上爻]
    year: int
    month: int
    day: int
    hour: int = 12

    # 排卦结果
    ben_gua_name: str = ""       # 本卦名称
    bian_gua_name: str = ""      # 变卦名称
    palace_name: str = ""        # 所属宫
    palace_wu_xing: str = ""     # 宫五行
    palace_order: int = 0        # 宫内序号

    lines: List[YaoLine] = field(default_factory=list)
    cang_yao: List[CangYao] = field(default_factory=list)  # 6个藏爻 (本宫纯卦各爻)
    gan_zhi: dict = field(default_factory=dict)
    xun_kong: Tuple[str, str] = ("", "")
    shi_pos: int = 0
    ying_pos: int = 0

    def __post_init__(self):
        """初始化后自动排卦"""
        self._validate_date()
        self._arrange()

    def _validate_date(self):
        """验证日期参数的基本范围"""
        if not isinstance(self.year, int) or self.year < 1 or self.year > 9999:
            raise ArrangementError(f"无效年份: {self.year}, 必须为1-9999的整数")
        if not isinstance(self.month, int) or self.month < 1 or self.month > 12:
            raise ArrangementError(f"无效月份: {self.month}, 必须为1-12的整数")
        # 每月最大天数检查
        days_in_month = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        max_day = days_in_month[self.month - 1]
        if not isinstance(self.day, int) or self.day < 1 or self.day > max_day:
            raise ArrangementError(f"无效日期: {self.year}年{self.month}月{self.day}日, 日必须为1-{max_day}的整数")
        # 闰年2月检查
        if self.month == 2 and self.day == 29:
            is_leap = (self.year % 4 == 0 and self.year % 100 != 0) or (self.year % 400 == 0)
            if not is_leap:
                raise ArrangementError(f"无效日期: {self.year}年不是闰年, 2月没有29日")

    def _arrange(self):
        """执行完整排卦流程"""
        # 1. 获取干支
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

        # 7. 计算旬空
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

        # 11. 计算藏爻 (本宫纯卦的6爻)
        self._compute_cang_yao()

    def _compute_cang_yao(self):
        """
        计算藏爻: 本宫纯卦各爻的纳甲六亲。

        据《古筮真诠》第三十九章: 藏爻是把本宫纯卦的全部爻套入主卦相应爻位下,
        无论主卦五行六亲是否缺漏, 都计算完整的6个藏爻。

        伏神 = 藏爻中所取的用神。当主卦中找不到所需用神(六亲), 即从藏爻中查找。
        """
        # 本宫纯卦的上下卦都是 palace_name 经卦
        pure_na_jia = NA_JIA[self.palace_name]
        # pure_na_jia = (天干, [初/二/三爻地支], [四/五/上爻地支])
        # 注: 纯卦上下卦同, 但纳甲遵循同一经卦的内外两套 (内卦下半, 外卦上半)

        cang_lines = []
        for i in range(6):
            pos = i + 1
            if i < 3:
                tian_gan = pure_na_jia[0]
                di_zhi = pure_na_jia[1][i]
            else:
                tian_gan = pure_na_jia[0]
                di_zhi = pure_na_jia[2][i - 3]

            wu_xing = DI_ZHI_WU_XING[di_zhi]
            liu_qin_val = get_liu_qin(self.palace_wu_xing, wu_xing)

            cang = CangYao(
                position=pos,
                tian_gan=tian_gan,
                di_zhi=di_zhi,
                wu_xing=wu_xing,
                liu_qin=liu_qin_val,
                is_xun_kong=(di_zhi in self.xun_kong),
            )
            cang_lines.append(cang)
        self.cang_yao = cang_lines

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
            print(f"  动爻: ", end="")
            for l in moving_lines:
                print(f"第{l.position}爻({l.di_zhi})", end=" ")
            print()
