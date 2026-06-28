"""
Micro benchmark for the liuyao analysis pipeline.

The benchmark uses Hexagram.from_ganzhi so it does not require the optional sxtwl
Gregorian-calendar dependency. It is intended for quick local regression checks
after framework/performance changes.

Usage:
    python scripts/benchmark_analysis.py --iterations 2000
"""
from __future__ import annotations

import argparse
import statistics
import sys
from pathlib import Path
from time import perf_counter

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from liuyao.domain.hexagram import Hexagram
from liuyao.application.use_cases.analysis import run_analysis, run_dual_analysis
from liuyao.domain.wangshuai import analyze_hexagram_wangshuai
from liuyao.domain.dongbian import analyze_dongbian
from liuyao.domain.patterns import analyze_all_patterns
from liuyao.domain.yimao_imagery import analyze_yimao_imagery
from liuyao.domain.jixiong import (
    determine_yong_shen,
    find_shi_line,
    find_yong_shen_lines,
    JI_SHEN_TABLE,
    judge_jixiong,
)
from liuyao.domain.rules import P0_RULES, RuleContext, RuleEngine
from liuyao.domain.rules.dynamic_rules import evaluate_dynamic_classic_rules
from liuyao.domain.yingqi import analyze_yingqi


def build_hexagram() -> Hexagram:
    return Hexagram.from_ganzhi(
        [8, 7, 7, 9, 7, 8],
        month_zhi="丑",
        day_zhi="卯",
        day_gan="甲",
        xun_kong=["午", "未"],
    )


def bench(name: str, iterations: int, fn) -> dict[str, float | str | int]:
    samples: list[float] = []
    for _ in range(iterations):
        h = build_hexagram()
        started = perf_counter()
        fn(h)
        samples.append((perf_counter() - started) * 1000)

    return {
        "name": name,
        "iterations": iterations,
        "total_ms": round(sum(samples), 3),
        "avg_ms": round(statistics.fmean(samples), 6),
        "p50_ms": round(statistics.median(samples), 6),
        "p95_ms": round(sorted(samples)[int(iterations * 0.95) - 1], 6),
        "min_ms": round(min(samples), 6),
        "max_ms": round(max(samples), 6),
    }


def profile_single_analysis_stages(iterations: int, question_type: str = "shiwu") -> dict[str, float | str | int]:
    stage_samples = {
        "setup_ms": [],
        "wangshuai_ms": [],
        "dongbian_ms": [],
        "patterns_ms": [],
        "yimao_ms": [],
        "jixiong_ms": [],
        "yingqi_ms": [],
        "total_ms": [],
    }

    for _ in range(iterations):
        h = build_hexagram()
        total_started = perf_counter()

        started = perf_counter()
        yong_shen = determine_yong_shen(question_type)
        ji_shen = JI_SHEN_TABLE.get(yong_shen, "")
        yong_lines = find_yong_shen_lines(h, yong_shen)
        stage_samples["setup_ms"].append((perf_counter() - started) * 1000)

        started = perf_counter()
        wangshuai = analyze_hexagram_wangshuai(h)
        stage_samples["wangshuai_ms"].append((perf_counter() - started) * 1000)

        started = perf_counter()
        dongbian = analyze_dongbian(h, wangshuai)
        stage_samples["dongbian_ms"].append((perf_counter() - started) * 1000)

        started = perf_counter()
        patterns = analyze_all_patterns(
            h, wangshuai, dongbian,
            yong_shen, ji_shen,
            yong_lines, question_type,
        )
        stage_samples["patterns_ms"].append((perf_counter() - started) * 1000)

        started = perf_counter()
        yimao = analyze_yimao_imagery(
            h, yong_lines, wangshuai, dongbian,
            patterns_results=patterns,
            question_type=question_type,
        )
        stage_samples["yimao_ms"].append((perf_counter() - started) * 1000)

        started = perf_counter()
        jixiong = judge_jixiong(
            h, yong_shen,
            wangshuai, dongbian,
            question_type,
            patterns_results=patterns,
        )
        if yimao.get("sentences"):
            jixiong.setdefault("yimao_signals", yimao["sentences"])
        stage_samples["jixiong_ms"].append((perf_counter() - started) * 1000)

        started = perf_counter()
        analyze_yingqi(
            h, yong_lines,
            wangshuai, dongbian,
            patterns_results=patterns,
        )
        stage_samples["yingqi_ms"].append((perf_counter() - started) * 1000)

        stage_samples["total_ms"].append((perf_counter() - total_started) * 1000)

    result: dict[str, float | str | int] = {
        "name": f"profile_single_{question_type}",
        "iterations": iterations,
    }
    for key, values in stage_samples.items():
        result[f"{key}_avg"] = round(statistics.fmean(values), 6)
        result[f"{key}_p95"] = round(sorted(values)[int(iterations * 0.95) - 1], 6)
    return result


def profile_jixiong_stages(iterations: int, question_type: str = "shiwu") -> dict[str, float | str | int]:
    stage_samples = {
        "prepare_context_ms": [],
        "p0_rules_ms": [],
        "dynamic_rules_ms": [],
        "full_jixiong_ms": [],
    }

    for _ in range(iterations):
        h = build_hexagram()
        yong_shen = determine_yong_shen(question_type)
        ji_shen = JI_SHEN_TABLE.get(yong_shen, "")
        yong_lines = find_yong_shen_lines(h, yong_shen)
        wangshuai = analyze_hexagram_wangshuai(h)
        dongbian = analyze_dongbian(h, wangshuai)
        patterns = analyze_all_patterns(
            h, wangshuai, dongbian,
            yong_shen, ji_shen,
            yong_lines, question_type,
        )

        started = perf_counter()
        shi_line = find_shi_line(h)
        primary_yong = yong_lines[0]
        primary_yong_ws = wangshuai[primary_yong.position - 1]
        for index, line in enumerate(yong_lines):
            line_ws = wangshuai[line.position - 1]
            if line.is_moving:
                primary_yong = line
                primary_yong_ws = line_ws
                break
            if line_ws["overall"] == "旺":
                primary_yong = line
                primary_yong_ws = line_ws
        context = RuleContext(
            hexagram=h,
            yong_shen_liu_qin=yong_shen,
            wangshuai_results=wangshuai,
            dongbian_results=dongbian,
            question_type=question_type,
            patterns_results=patterns,
            shi_line=shi_line,
            primary_yong=primary_yong,
            yong_lines=yong_lines,
            month_zhi=h.gan_zhi["month_zhi"],
            day_zhi=h.gan_zhi["day_zhi"],
        )
        if primary_yong_ws is None:
            raise AssertionError("primary_yong_ws must be set")
        stage_samples["prepare_context_ms"].append((perf_counter() - started) * 1000)

        started = perf_counter()
        RuleEngine(P0_RULES).evaluate(context)
        stage_samples["p0_rules_ms"].append((perf_counter() - started) * 1000)

        started = perf_counter()
        evaluate_dynamic_classic_rules(context)
        stage_samples["dynamic_rules_ms"].append((perf_counter() - started) * 1000)

        started = perf_counter()
        judge_jixiong(
            h, yong_shen,
            wangshuai, dongbian,
            question_type,
            patterns_results=patterns,
        )
        stage_samples["full_jixiong_ms"].append((perf_counter() - started) * 1000)

    result: dict[str, float | str | int] = {
        "name": f"profile_jixiong_{question_type}",
        "iterations": iterations,
    }
    for key, values in stage_samples.items():
        result[f"{key}_avg"] = round(statistics.fmean(values), 6)
        result[f"{key}_p95"] = round(sorted(values)[int(iterations * 0.95) - 1], 6)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark liuyao analysis pipeline")
    parser.add_argument("--iterations", type=int, default=1000)
    parser.add_argument("--profile-stages", action="store_true")
    args = parser.parse_args()

    if args.iterations <= 0:
        raise SystemExit("--iterations must be positive")

    scenarios = [
        ("single_shiwu", lambda h: run_analysis(h, "shiwu")),
        ("dual_shiwu", lambda h: run_dual_analysis(h, "shiwu")),
        ("dual_bing", lambda h: run_dual_analysis(h, "bing")),
    ]

    print(f"benchmark_iterations={args.iterations}")
    for name, fn in scenarios:
        result = bench(name, args.iterations, fn)
        print(
            " ".join(
                f"{key}={value}"
                for key, value in result.items()
            )
        )

    if args.profile_stages:
        profile = profile_single_analysis_stages(args.iterations, "shiwu")
        print(
            " ".join(
                f"{key}={value}"
                for key, value in profile.items()
            )
        )
        jixiong_profile = profile_jixiong_stages(args.iterations, "shiwu")
        print(
            " ".join(
                f"{key}={value}"
                for key, value in jixiong_profile.items()
            )
        )


if __name__ == "__main__":
    main()
