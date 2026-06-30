"""Extract candidate classic Liuyao imagery records from 《易冒》 reference markdown files."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "data" / "classic_imagery.jsonl"
SOURCE_DIRS = {
    "yimao": ROOT / "docs" / "reference" / "yimao",
}

IMAGERY_KEYWORDS = (
    "象",
    "像",
    "形",
    "色",
    "位",
    "方",
    "方位",
    "类",
    "属",
    "用",
    "爻",
    "卦",
    "世",
    "应",
    "飞",
    "伏",
    "互",
    "变",
    "反",
    "空",
    "破",
    "墓",
    "绝",
    "散",
    "旺",
    "衰",
    "进",
    "退",
    "生",
    "克",
    "冲",
    "合",
    "刑",
    "害",
    "父母",
    "官鬼",
    "兄弟",
    "子孙",
    "妻财",
    "青龙",
    "朱雀",
    "勾陈",
    "腾蛇",
    "螣蛇",
    "白虎",
    "元武",
    "玄武",
)

QUESTION_TYPE_KEYWORDS = {
    "hun_male": ("婚", "夫", "妻", "媒", "嫁", "娶", "夫妻"),
    "cai": ("求财", "经营", "买卖", "交易", "经商", "谋财", "财源", "利", "财"),
    "shiwu": ("失", "寻", "物", "盗", "贼", "遗"),
    "bing": ("病", "疾", "医", "药", "痊", "死"),
    "kaoshi": ("功名", "试", "科", "文书", "学", "师"),
    "chuxing": ("行人", "出行", "归", "舟", "车", "路"),
    "other": (),
}

SECTION_PATTERNS = (
    re.compile(r"^\s*#{1,6}\s*(.+?)\s*$"),
    re.compile(r"^\s*(.+?章第\S*)\s*$"),
    re.compile(r"^\s*易冒卷之\S+\s*$"),
)

SECTION_ALIASES = (
    "甲子",
    "成爻",
    "成卦",
    "纳甲",
    "五行",
    "六亲",
    "六神",
    "世应",
    "飞伏",
    "互卦",
    "变卦",
    "反伏",
    "空亡",
    "月破",
    "墓绝",
    "进退",
    "用神",
    "取象",
    "方位",
    "疾病",
    "失物",
    "婚姻",
    "求财",
)

SKIP_PREFIXES = (
    "易冒王序",
    "易冒顾序",
    "易冒陆序",
    "易冒自序",
    "康熙",
    "新安",
)

PUNCTUATION_RE = re.compile(r"[，。；：、！？,.!?;:\s（）()《》〈〉\[\]【】\"'“”‘’]")
PAREN_RE = re.compile(r"^（(.+?)）\s*$")


@dataclass(frozen=True)
class SourceLine:
    source: str
    source_file: Path
    line_number: int
    text: str
    section: str


def iter_source_lines() -> Iterable[SourceLine]:
    for source, source_dir in SOURCE_DIRS.items():
        for path in sorted(source_dir.glob("*.md")):
            section = ""
            in_body = False
            with path.open("r", encoding="utf-8") as file:
                for line_number, raw_line in enumerate(file, start=1):
                    text = raw_line.strip()
                    if not text:
                        continue
                    matched_section = match_section(text)
                    if matched_section:
                        section = matched_section
                        if "卷" in text or "章" in text:
                            in_body = True
                        continue
                    if not in_body:
                        continue
                    yield SourceLine(source, path, line_number, text, section)


def match_section(text: str) -> str | None:
    for pattern in SECTION_PATTERNS:
        match = pattern.match(text)
        if match:
            return shorten_section_title(match.group(1) if match.groups() else text)
    return None


def shorten_section_title(text: str) -> str:
    title = re.sub(r"（.*?）", "", text).strip()
    title = re.split(r"[，。；：,.!?！？]", title, maxsplit=1)[0].strip()
    for alias in SECTION_ALIASES:
        if alias in title:
            return alias
    if len(title) > 18:
        return title[:18]
    return title


def strip_parenthetical(text: str) -> str:
    match = PAREN_RE.match(text)
    if match:
        return match.group(1).strip()
    return text.strip()


def split_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[。；])", text)
    return [part.strip() for part in parts if part.strip()]


def imagery_type(text: str, section: str) -> str:
    haystack = text + section
    if any(word in haystack for word in ("父母", "官鬼", "兄弟", "子孙", "妻财", "六亲")):
        return "liu_qin_imagery"
    if any(word in haystack for word in ("青龙", "朱雀", "勾陈", "腾蛇", "螣蛇", "白虎", "元武", "玄武", "六神")):
        return "liu_shen_imagery"
    if any(word in haystack for word in ("方", "位", "东", "西", "南", "北", "中")):
        return "position_imagery"
    if any(word in haystack for word in ("色", "形", "性", "象", "像", "类")):
        return "object_imagery"
    if any(word in haystack for word in ("飞", "伏", "互", "变", "反", "空", "破", "墓", "绝")):
        return "structure_imagery"
    return "general_imagery"


def is_candidate(raw_text: str, section: str) -> bool:
    if not raw_text or len(raw_text) < 8:
        return False
    if any(raw_text.startswith(prefix) for prefix in SKIP_PREFIXES):
        return False
    keyword_count = sum(1 for keyword in IMAGERY_KEYWORDS if keyword in raw_text)
    has_imagery_signal = any(word in raw_text for word in ("象", "像", "形", "色", "位", "方", "属", "主", "谓", "为", "取", "类"))
    has_section_signal = section in SECTION_ALIASES
    return keyword_count >= 1 and (has_imagery_signal or has_section_signal)


def infer_question_types(text: str, section: str) -> list[str]:
    haystack = text + section
    matched = []
    for question_type, keywords in QUESTION_TYPE_KEYWORDS.items():
        if question_type == "other":
            continue
        if any(keyword in haystack for keyword in keywords):
            matched.append(question_type)
    return matched or ["other"]


def extract_keywords(text: str) -> list[str]:
    return [keyword for keyword in IMAGERY_KEYWORDS if keyword in text]


def stable_id(source: str, source_file: Path, line_number: int, raw_text: str) -> str:
    digest = hashlib.sha1(f"{source}:{source_file.name}:{line_number}:{raw_text}".encode()).hexdigest()[:12]
    return f"imagery_{source}_{digest}"


def normalize_text(text: str) -> str:
    return PUNCTUATION_RE.sub("", text)


def build_records() -> list[dict]:
    records = []
    seen_normalized = set()
    for source_line in iter_source_lines():
        for raw_text in split_sentences(strip_parenthetical(source_line.text)):
            if not is_candidate(raw_text, source_line.section):
                continue
            normalized = normalize_text(raw_text)
            if normalized in seen_normalized:
                continue
            seen_normalized.add(normalized)
            records.append(
                {
                    "id": stable_id(source_line.source, source_line.source_file, source_line.line_number, raw_text),
                    "source": source_line.source,
                    "source_file": str(source_line.source_file.relative_to(ROOT)).replace("\\", "/"),
                    "line_start": source_line.line_number,
                    "line_end": source_line.line_number,
                    "section": source_line.section,
                    "raw_text": raw_text,
                    "imagery_type": imagery_type(raw_text, source_line.section),
                    "keywords": extract_keywords(raw_text),
                    "question_types": infer_question_types(raw_text, source_line.section),
                    "usage": "report_imagery_reference_only",
                    "review_status": "candidate",
                    "notes": "",
                }
            )
    return records


def write_jsonl(records: list[dict], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="\n") as file:
        for record in records:
            file.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    records = build_records()
    write_jsonl(records, args.output)
    print(f"wrote {len(records)} records to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
