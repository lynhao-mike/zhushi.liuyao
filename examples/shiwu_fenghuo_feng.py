"""
示例：失物占 —— 雷火丰之风山渐（双视角 + 可读性报告）

占问事宜：金首饰丢失能否找回
起卦时间：2026-05-25 14:28（农历丙午年 癸巳月 己亥日 辛未时）
干支四柱：丙午年 癸巳月 己亥日 辛未时
旬    空：辰巳

摇卦结果（从初爻到上爻）：
  初爻 9（老阳·动）  → 子孙卯木
  二爻 8（少阴·静）  → 官鬼丑土  [应]
  三爻 7（少阳·静）  → 兄弟亥水
  四爻 9（老阳·动）  → 妻财午火
  五爻 6（老阴·动）  → 父母申金  [世]
  上爻 6（老阴·动）  → 官鬼戌土

运行方式（命令行）：
  python3 -m liuyao.main \\
      --date 2026-05-25 --yao 9 8 7 9 6 6 --hour 14 \\
      --question-type shiwu

运行方式（Python API）：
  python3 examples/shiwu_fenghuo_feng.py
"""

import sys
import os

# 确保在仓库根目录下可直接运行
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from liuyao import (
    Hexagram,
    run_dual_analysis,
    format_dual_report,
    format_readable_report,
)

REPORTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)

# ── 排卦 ──────────────────────────────────────────────────────────────────
#   yao_values: 从初爻(第1爻)到上爻(第6爻)
#   6=老阴(动变阳)  7=少阳(静)  8=少阴(静)  9=老阳(动变阴)
h = Hexagram(
    yao_values=[9, 8, 7, 9, 6, 6],
    year=2026, month=5, day=25,
    hour=14,
)
h.display()

# ── 双视角分析 ────────────────────────────────────────────────────────────
#   失物(shiwu)自动启用双视角：
#     视角1 — 父母爻（物件本相，物之载体）
#     视角2 — 妻财爻（贵重财物，物之价值）
dual = run_dual_analysis(h, question_type="shiwu")

# ── 技术报告（双视角，供研习/存档） ─────────────────────────────────────
tech_text = format_dual_report(dual)
print()
print("━" * 60)
print("  【技术报告】双视角分析")
print("━" * 60)
print(tech_text)

tech_path = os.path.join(REPORTS_DIR, "shiwu_fenghuo_feng.txt")
with open(tech_path, "w", encoding="utf-8") as f:
    f.write("占问：金首饰丢失能否找回\n")
    f.write("起卦：2026-05-25 14:28  丙午年 癸巳月 己亥日  旬空：辰巳\n")
    f.write("本卦：雷火丰 → 变卦：风山渐\n")
    f.write("=" * 60 + "\n\n")
    f.write(tech_text)
print(f"[技术报告已保存至 {tech_path}]")

# ── 可读性断卦报告（面向客户，供易师直接解读） ───────────────────────
META = {
    "question": "金首饰丢失，能否找回？",
    "querent":  "（卦主自占）",
    "datetime": "2026年5月25日 14时28分",
    "note":     "失物为金首饰，疑于外出途中遗落；起卦后第一时间测算。",
}

readable_text = format_readable_report(dual, meta=META)
print()
print("━" * 60)
print("  【可读性断卦报告】面向客户版")
print("━" * 60)
print(readable_text)

readable_path = os.path.join(REPORTS_DIR, "shiwu_fenghuo_feng_readable.txt")
with open(readable_path, "w", encoding="utf-8") as f:
    f.write(readable_text)
print(f"[可读性报告已保存至 {readable_path}]")
