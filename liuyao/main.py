"""
六爻排卦CLI入口 - Liu Yao Hexagram CLI Entry Point

使用方式:
    python3 -m liuyao.main --date 2024-01-15 --yao 8 7 7 9 7 8
    python3 -m liuyao.main --date 2024-01-15 --yao 8 7 7 9 7 8 --question-type cai
    python3 -m liuyao.main --date 2024-01-15 --name 泽风大过 --moving 4
"""

import argparse
import sys

from .hexagram import Hexagram
from .data import HEXAGRAM_BY_NAME, BINARY_TO_GUA, BA_GUA
from .analyzer import run_analysis, run_dual_analysis
from .jixiong import DUAL_PERSPECTIVE_TABLE
from .report import format_report, format_dual_report


def parse_args():
    parser = argparse.ArgumentParser(
        description="六爻排卦分析系统 - Liu Yao Hexagram Analysis System"
    )
    parser.add_argument(
        "--date", required=True,
        help="日期, 格式: YYYY-MM-DD"
    )
    parser.add_argument(
        "--yao", nargs=6, type=int,
        help="六次摇卦结果 (从初爻到上爻), 每个值为6/7/8/9"
    )
    parser.add_argument(
        "--name",
        help="直接指定卦名 (如 '泽风大过')"
    )
    parser.add_argument(
        "--moving", nargs="*", type=int, default=[],
        help="动爻位置 (1-6), 仅与--name配合使用"
    )
    parser.add_argument(
        "--hour", type=int, default=12,
        help="时辰 (0-23), 默认12(午时)"
    )
    parser.add_argument(
        "--question-type", dest="question_type",
        choices=["cai", "guan", "hun_male", "hun_female", "bing",
                 "kaoshi", "zinv", "xingRen", "youHuan", "shiwu", "other"],
        default="other",
        help="问事类型: cai(财运), guan(官运), hun_male(婚姻男问), "
             "hun_female(婚姻女问), bing(疾病), kaoshi(考试), "
             "zinv(子女), xingRen(行人), youHuan(忧患), shiwu(失物), other(其他)"
    )
    parser.add_argument(
        "--dual", dest="dual", action="store_true",
        help="启用双(多)视角分析。失物、问病等多用神场景默认自动启用; "
             "其他类型若指定本开关, 会退化为单视角输出。"
    )
    parser.add_argument(
        "--no-dual", dest="no_dual", action="store_true",
        help="对默认启用双视角的占类(如失物、问病)强制使用单视角输出。"
    )
    return parser.parse_args()


def name_to_yao_values(gua_name, moving_lines):
    """
    根据卦名和动爻位置生成摇卦值列表。

    Args:
        gua_name: 卦名
        moving_lines: 动爻位置列表 (1-6)

    Returns:
        list: 6个摇卦值
    """
    if gua_name not in HEXAGRAM_BY_NAME:
        raise ValueError(f"未找到卦名: {gua_name}")

    info = HEXAGRAM_BY_NAME[gua_name]
    upper_binary = BA_GUA[info["upper"]]["binary"]
    lower_binary = BA_GUA[info["lower"]]["binary"]

    # 组合6爻 (下3 + 上3)
    all_lines = list(lower_binary) + list(upper_binary)

    yao_values = []
    for i in range(6):
        pos = i + 1
        if pos in moving_lines:
            # 动爻: 阳动=9(老阳), 阴动=6(老阴)
            yao_values.append(9 if all_lines[i] == 1 else 6)
        else:
            # 静爻: 阳静=7(少阳), 阴静=8(少阴)
            yao_values.append(7 if all_lines[i] == 1 else 8)

    return yao_values


def main():
    args = parse_args()

    # 解析日期
    try:
        parts = args.date.split("-")
        year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
    except (ValueError, IndexError):
        print(f"错误: 日期格式不正确, 请使用 YYYY-MM-DD 格式")
        sys.exit(1)

    # 确定摇卦值
    if args.yao:
        yao_values = args.yao
        # 验证输入
        for v in yao_values:
            if v not in (6, 7, 8, 9):
                print(f"错误: 摇卦值必须为6/7/8/9, 收到: {v}")
                sys.exit(1)
    elif args.name:
        try:
            yao_values = name_to_yao_values(args.name, args.moving)
        except ValueError as e:
            print(f"错误: {e}")
            sys.exit(1)
    else:
        print("错误: 必须提供 --yao 或 --name 参数")
        sys.exit(1)

    # 排卦
    try:
        h = Hexagram(yao_values, year, month, day, args.hour)
        h.display()
    except Exception as e:
        print(f"排卦错误: {e}")
        sys.exit(1)

    # 运行分析
    print()
    print(">>> 开始六爻分析 <<<")
    print()

    try:
        # 决定使用单视角还是双视角:
        #   - 显式 --no-dual: 强制单视角
        #   - 显式 --dual 或 该占类在 DUAL_PERSPECTIVE_TABLE 中: 双视角
        #   - 否则: 单视角
        use_dual = (
            (not args.no_dual) and
            (args.dual or args.question_type in DUAL_PERSPECTIVE_TABLE)
        )

        if use_dual:
            dual_report = run_dual_analysis(h, args.question_type)
            print(format_dual_report(dual_report))
        else:
            report = run_analysis(h, args.question_type)
            print(format_report(report))
    except Exception as e:
        print(f"分析错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
