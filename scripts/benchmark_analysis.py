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


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark liuyao analysis pipeline")
    parser.add_argument("--iterations", type=int, default=1000)
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


if __name__ == "__main__":
    main()
