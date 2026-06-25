"""One-shot script: rewrite shim import paths in tests/ to canonical new paths."""
import pathlib

REPLACEMENTS = [
    ("from liuyao.hexagram import",       "from liuyao.domain.hexagram import"),
    ("from liuyao.data import",           "from liuyao.domain.data import"),
    ("from liuyao.analyzer import",       "from liuyao.application.use_cases.analysis import"),
    ("from liuyao.report import",         "from liuyao.interfaces.cli.reporting import"),
    ("from liuyao.wangshuai import",      "from liuyao.domain.wangshuai import"),
    ("from liuyao.jixiong import",        "from liuyao.domain.jixiong import"),
    ("from liuyao.patterns import",       "from liuyao.domain.patterns import"),
    ("from liuyao.dongbian import",       "from liuyao.domain.dongbian import"),
    ("from liuyao.yingqi import",         "from liuyao.domain.yingqi import"),
    ("from liuyao.calendar_utils import", "from liuyao.domain.calendar_utils import"),
    ("from liuyao.exceptions import",     "from liuyao.domain.exceptions import"),
]

root = pathlib.Path(__file__).resolve().parents[1]
changed = 0
for p in (root / "tests").glob("*.py"):
    text = p.read_text(encoding="utf-8")
    new = text
    for old, new_val in REPLACEMENTS:
        new = new.replace(old, new_val)
    if new != text:
        p.write_text(new, encoding="utf-8")
        changed += 1
        print(f"  updated: {p.name}")

print(f"Done. {changed} files updated.")
