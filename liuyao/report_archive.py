"""
Report archiving utilities.

Persist generated report texts into the repository so each completed reading can
be reviewed and compared with later feedback.
"""
from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPORTS_DIR = PROJECT_ROOT / "examples" / "reports"


def _safe_filename_part(value: Optional[str], fallback: str = "未命名") -> str:
    text = (value or "").strip() or fallback
    text = re.sub(r"[\\/:*?\"<>|\r\n\t]+", "_", text)
    text = re.sub(r"\s+", "", text)
    text = text.strip("._ ")
    return (text or fallback)[:48]


def _build_prefix(meta: Optional[Dict[str, Any]]) -> str:
    meta = meta or {}
    question = _safe_filename_part(meta.get("question"), "未命名占问")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{timestamp}_{question}"


def _iter_hexagram_input_lines(value: Any) -> Iterable[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [line.rstrip() for line in value.splitlines() if line.strip()]
    if isinstance(value, dict):
        labels = {
            "question": "占问事项",
            "querent": "求测人",
            "question_type": "占问类型",
            "date": "起卦日期",
            "hour": "起卦小时",
            "yao_values": "摇卦值",
            "ganzhi_override": "干支覆盖",
            "gan_zhi": "干支",
            "xun_kong": "旬空",
            "ben_gua_name": "本卦",
            "bian_gua_name": "变卦",
            "palace_name": "卦宫",
            "palace_wu_xing": "宫五行",
            "shi_pos": "世爻",
            "ying_pos": "应爻",
            "lines": "六爻明细",
        }
        lines: List[str] = []
        for key, label in labels.items():
            if key not in value or value[key] in (None, "", []):
                continue
            lines.append(f"- {label}：{value[key]}")
        for key, item in value.items():
            if key in labels or item in (None, "", []):
                continue
            lines.append(f"- {key}：{item}")
        return lines
    return [str(value)]


def _build_hexagram_input_section(meta: Optional[Dict[str, Any]]) -> str:
    meta = meta or {}
    lines = list(_iter_hexagram_input_lines(meta.get("hexagram_input")))
    if not lines:
        return ""
    return "\n".join(["# 输入卦象信息", "", *lines, ""])


def _with_hexagram_input(content: str, meta: Optional[Dict[str, Any]]) -> str:
    section = _build_hexagram_input_section(meta)
    if not section:
        return content
    return f"{section}\n---\n\n{content}"


def archive_reports(
    *,
    report_text: Optional[str] = None,
    report_readable: Optional[str] = None,
    meta: Optional[Dict[str, Any]] = None,
    reports_dir: Optional[str | Path] = None,
) -> List[str]:
    """Write generated reports to disk and return workspace-relative paths."""
    target_dir = Path(reports_dir) if reports_dir else DEFAULT_REPORTS_DIR
    if not target_dir.is_absolute():
        target_dir = PROJECT_ROOT / target_dir
    target_dir.mkdir(parents=True, exist_ok=True)

    prefix = _build_prefix(meta)
    written: List[str] = []

    outputs = [
        (report_text, "技术报告"),
        (report_readable, "可读性报告"),
    ]
    for content, suffix in outputs:
        if not content:
            continue
        path = target_dir / f"{prefix}_{suffix}.txt"
        path.write_text(_with_hexagram_input(content, meta), encoding="utf-8")
        written.append(path.relative_to(PROJECT_ROOT).as_posix())

    return written
