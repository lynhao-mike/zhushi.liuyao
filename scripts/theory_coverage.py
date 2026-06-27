#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
理论覆盖率检查

从5个theory文档中提取知识点关键词，与代码中的
theory_id / class名 / docstring / 函数注释做模糊匹配，
输出三类清单：已覆盖、部分覆盖、零覆盖。

用法：
    python scripts/theory_coverage.py

ponytail: 关键词匹配，不做语义理解，误报自行判断。
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent

# ── 1. 理论文档清单 ──────────────────────────────────────────────────────────

THEORY_DOCS = [
    ROOT / "docs/reference/zengshan_230_theory.md",
    ROOT / "docs/reference/zengshan_230_theory_101_160.md",
    ROOT / "docs/reference/zengshan_230_theory_part2.md",
    ROOT / "docs/reference/zhishidianzongjie.md",
    ROOT / "docs/reference/theory_audit_report.md",
]

# ── 2. 代码扫描目录 ──────────────────────────────────────────────────────────

CODE_DIRS = [
    ROOT / "liuyao/domain",
    ROOT / "liuyao/application",
]

# ── 3. 知识点提取（Markdown 标题 + 规则描述 + 关键词提取）────────────────────

HEADING_PATTERN = re.compile(r"^#{1,4}\s+(.+)", re.MULTILINE)
RULE_KEYWORDS = re.compile(
    r"(废爻型|金刚型|月令时效|时效卦|三合局|内重外轻|真绊|假绊|化绊|动绊"
    r"|子鬼互化|父子互化|财鬼互化|用忌互化|六冲六合|变爻用神|回头克|回头生"
    r"|化进|化退|化绝|化空|暗动|伏吟|反吟|三墓|旬空|月破|日克|日墓"
    r"|持世|用神克世|用神生世|元神.*变废|元神独发|灾卦|心态卦|暗心态卦"
    r"|再占卦|独静|就重避轻|串卦|太过卦|终身时效|寿元|克中带冲|动爻扶旺"
    r"|间爻|世化用忌|藏爻确认|对位法|拱扶|应期.*根|有根|无根)",
    re.VERBOSE,
)


def extract_theory_points(doc_path: Path) -> list[dict]:
    """从文档提取知识点（标题 + 关键词）。"""
    text = doc_path.read_text(encoding="utf-8", errors="ignore")
    points = []
    for m in HEADING_PATTERN.finditer(text):
        title = m.group(1).strip()
        # 只取包含实质内容的标题
        if len(title) < 4 or title.startswith("来源") or title.startswith("总结"):
            continue
        keywords = set(RULE_KEYWORDS.findall(title))
        # 也扫标题后面 200 字的描述
        start = m.end()
        context = text[start:start + 200]
        keywords |= set(RULE_KEYWORDS.findall(context))
        points.append({
            "title": title,
            "keywords": sorted(keywords),
            "source": doc_path.name,
        })
    return points


# ── 4. 代码扫描 ──────────────────────────────────────────────────────────────

def collect_code_tokens() -> set[str]:
    """从代码中收集所有 theory_id / docstring / 注释中的关键词。"""
    tokens: set[str] = set()
    for code_dir in CODE_DIRS:
        for py_file in code_dir.rglob("*.py"):
            text = py_file.read_text(encoding="utf-8", errors="ignore")
            tokens |= set(RULE_KEYWORDS.findall(text))
            # 也收集 theory_id 字符串值
            for tid in re.findall(r'theory_id\s*=\s*["\']([^"\']+)["\']', text):
                tokens |= set(RULE_KEYWORDS.findall(tid))
    return tokens


# ── 5. 覆盖率比对 ─────────────────────────────────────────────────────────────

def classify(points: list[dict], code_tokens: set[str]) -> tuple[list, list, list]:
    """返回 (已覆盖, 部分覆盖, 零覆盖) 三个列表。"""
    covered, partial, missing = [], [], []
    for p in points:
        if not p["keywords"]:
            partial.append(p)  # 无法提取关键词 = 无法判断
            continue
        hit = [kw for kw in p["keywords"] if kw in code_tokens]
        if len(hit) == len(p["keywords"]):
            covered.append({**p, "hit": hit})
        elif hit:
            partial.append({**p, "hit": hit, "miss": [k for k in p["keywords"] if k not in hit]})
        else:
            missing.append({**p, "hit": [], "miss": p["keywords"]})
    return covered, partial, missing


# ── 6. 主程序 ─────────────────────────────────────────────────────────────────

def main():
    print("扫描代码关键词...")
    code_tokens = collect_code_tokens()
    print(f"  代码中发现关键词: {sorted(code_tokens)}\n")

    all_points: list[dict] = []
    for doc in THEORY_DOCS:
        if not doc.exists():
            print(f"  [跳过] 不存在: {doc.name}")
            continue
        pts = extract_theory_points(doc)
        print(f"  {doc.name}: {len(pts)} 个知识点标题")
        all_points.extend(pts)

    print(f"\n总知识点标题: {len(all_points)}")

    covered, partial, missing = classify(all_points, code_tokens)

    total = len(all_points)
    print(f"\n覆盖率概览:")
    print(f"  已覆盖 (全部关键词命中): {len(covered)}/{total} ({len(covered)/total*100:.0f}%)")
    print(f"  部分覆盖 (部分命中):     {len(partial)}/{total}")
    print(f"  零覆盖 (无关键词命中):   {len(missing)}/{total}\n")

    if missing:
        print("=" * 60)
        print("零覆盖知识点（代码中完全未体现的理论）：")
        for p in missing:
            print(f"  [{p['source']}] {p['title']}")
            if p.get("miss"):
                print(f"    缺失关键词: {', '.join(p['miss'])}")
        print()

    if partial:
        print("=" * 60)
        print("部分覆盖知识点（关键词仅部分命中）：")
        for p in partial:
            hit = p.get("hit", [])
            miss = p.get("miss", [])
            if not hit and not miss:
                print(f"  [{p['source']}] {p['title']}  (无可提取关键词，需人工确认)")
            else:
                print(f"  [{p['source']}] {p['title']}")
                if miss:
                    print(f"    未覆盖: {', '.join(miss)}  | 已覆盖: {', '.join(hit)}")

    # ponytail: 不做 sys.exit(1) 卡CI，结果由人工判断
    return 0


if __name__ == "__main__":
    sys.exit(main())
