#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
规则覆盖率检查

跑所有现有 fixture，报出哪些 rule_id 从未被命中。
命中 = jixiong_result 中出现该 rule_id。

用法：
    python scripts/check_rule_coverage.py

ponytail: 不做持续 CI 集成，手工触发。需要时加 --fail-under 参数。
"""

import sys
import inspect
from pathlib import Path

# 让 import 从项目根目录找包
sys.path.insert(0, str(Path(__file__).parent.parent))

from liuyao.domain.hexagram import Hexagram
from liuyao.application.use_cases.analysis import run_analysis
from liuyao.domain.rules import p0_rules
from tests.fixtures.zengshan_230_cases import ZENGSHAN_CASES
from tests.fixtures.feedback_cases import FEEDBACK_CASES


# ponytail: 规则覆盖率需要覆盖非古籍fixture的最小合成样本，避免为了触发规则硬造古籍案例。
SYNTHETIC_RULE_CASES = [
    {
        "id": "synthetic_zi_gui_hu_hua",
        "yao_types": [6, 8, 7, 8, 9, 9],
        "month_zhi": "子",
        "day_zhi": "子",
        "day_gan": "甲",
        "question_type": "shengchan",
    },
    {
        "id": "synthetic_fu_zi_hu_hua",
        "yao_types": [6, 6, 7, 6, 7, 8],
        "month_zhi": "子",
        "day_zhi": "子",
        "day_gan": "甲",
        "question_type": "kaoshi",
    },
    {
        "id": "synthetic_cai_gui_hu_hua",
        "yao_types": [6, 6, 6, 6, 6, 7],
        "month_zhi": "子",
        "day_zhi": "子",
        "day_gan": "甲",
        "question_type": "cai",
    },
    {
        "id": "synthetic_lifetime_shixiao",
        "yao_types": [6, 6, 6, 8, 7, 6],
        "month_zhi": "子",
        "day_zhi": "子",
        "day_gan": "甲",
        "question_type": "zhongshen_gongming",
    },
    {
        "id": "synthetic_traveler_return",
        "yao_types": [6, 7, 7, 7, 6, 8],
        "month_zhi": "子",
        "day_zhi": "子",
        "day_gan": "甲",
        "question_type": "xingren",
    },
    {
        "id": "synthetic_keshichong_breaks_gangjing",
        "yao_types": [6, 6, 9, 6, 8, 9],
        "month_zhi": "子",
        "day_zhi": "子",
        "day_gan": "甲",
        "question_type": "other",
    },
    {
        "id": "synthetic_short_term_no_jin_tui",
        "yao_types": [6, 8, 6, 7, 7, 9],
        "month_zhi": "子",
        "day_zhi": "子",
        "day_gan": "甲",
        "question_type": "jinshi",
    },
    {
        "id": "synthetic_yuanshen_dufa_bianfei",
        "yao_types": [7, 6, 7, 7, 8, 7],
        "month_zhi": "子",
        "day_zhi": "子",
        "day_gan": "甲",
        "question_type": "cai",
    },
    {
        "id": "synthetic_zaizhan_simplified",
        "yao_types": [6, 6, 6, 8, 6, 8],
        "month_zhi": "子",
        "day_zhi": "子",
        "day_gan": "甲",
        "question_type": "zaizhan",
    },
]


def collect_all_rule_ids() -> set[str]:
    """从 p0_rules 模块中收集所有 rule_id（排除 base）。"""
    ids = set()
    for _, cls in inspect.getmembers(p0_rules, inspect.isclass):
        rid = getattr(cls, "rule_id", None)
        if rid and rid != "base":
            ids.add(rid)
    return ids


def run_case(case: dict) -> str | None:
    """跑单个 fixture，返回命中的 rule_id 或 None。"""
    try:
        hx = Hexagram.from_ganzhi(
            case["yao_types"],
            month_zhi=case["month_zhi"],
            day_zhi=case["day_zhi"],
            day_gan=case.get("day_gan"),
            xun_kong=case.get("xun_kong"),
        )
        report = run_analysis(
            hx,
            question_type=case.get("question_type", "other"),
            yong_shen_override=case.get("yong_shen"),
        )
        return report.jixiong_result.get("rule_id")
    except Exception as e:
        cid = case.get("id") or case.get("case_id") or "?"
        print(f"  [跳过] {cid}: {e}")
        return None


def main():
    all_rule_ids = collect_all_rule_ids()
    hit_rule_ids: set[str] = set()

    all_cases = list(ZENGSHAN_CASES) + list(FEEDBACK_CASES) + SYNTHETIC_RULE_CASES
    print(f"总案例数：{len(all_cases)}")
    print(f"已知规则数：{len(all_rule_ids)}\n")

    for case in all_cases:
        rid = run_case(case)
        if rid:
            hit_rule_ids.add(rid)

    missed = sorted(all_rule_ids - hit_rule_ids)
    hit_count = len(hit_rule_ids & all_rule_ids)
    total = len(all_rule_ids)

    print(f"\n覆盖率：{hit_count}/{total} ({hit_count/total*100:.0f}%)\n")

    if missed:
        print("未被任何 fixture 触发的规则（补例优先目标）：")
        for rid in missed:
            # 附上对应的 theory_id 方便查书
            cls = next(
                (c for _, c in inspect.getmembers(p0_rules, inspect.isclass)
                 if getattr(c, "rule_id", None) == rid),
                None,
            )
            tid = getattr(cls, "theory_id", "") if cls else ""
            print(f"  {rid}  [{tid}]")
    else:
        print("[OK] 所有规则均有 fixture 覆盖，无需补例。")

    # ponytail: 加 --fail-under N 支持 CI 卡门槛，当前不做
    return len(missed)


if __name__ == "__main__":
    sys.exit(main())
