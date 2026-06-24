# -*- coding: utf-8 -*-
"""Extract candidate classic Liuyao judgements from 《黄金策》 reference markdown files."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "data" / "classic_judgements.jsonl"
SOURCE_DIRS = {
    "huangjince": ROOT / "docs" / "reference" / "huangjince",
}

JUDGEMENT_KEYWORDS = (
    "世",
    "应",
    "用",
    "爻",
    "卦",
    "动",
    "变",
    "化",
    "冲",
    "合",
    "刑",
    "害",
    "克",
    "生",
    "扶",
    "空",
    "亡",
    "墓",
    "绝",
    "旺",
    "衰",
    "财",
    "官",
    "鬼",
    "父母",
    "兄弟",
    "子孙",
    "妻财",
    "福德",
    "日辰",
    "月建",
    "六神",
    "青龙",
    "朱雀",
    "勾陈",
    "螣蛇",
    "白虎",
    "玄武",
)

QUESTION_TYPE_KEYWORDS = {
    "hun_male": ("婚", "夫", "妻", "媒", "嫁", "娶", "夫妻"),
    "cai": ("求财", "经营", "买卖", "交易", "经商", "谋财", "财源", "利息", "贾", "商", "投资"),
    "shiwu": ("失", "寻", "物", "盗", "贼", "遗"),
    "bing": ("病", "疾", "医", "药", "痊", "死"),
    "kaoshi": ("功名", "试", "科", "文书", "学", "师"),
    "chuxing": ("行人", "出行", "归", "舟", "车", "路"),
    "other": (),
}

SECTION_PATTERNS = (
    re.compile(r"^\s*#{1,6}\s*(.+?)\s*$"),
    re.compile(r"^\s*[卷甲乙丙丁戊己庚辛壬癸子丑寅卯辰巳午未申酉戌亥].{0,20}[章卷篇第]\S*\s*$"),
)

SECTION_ALIASES = (
    "总断千金赋",
    "天时",
    "年时",
    "国朝",
    "征战",
    "身命",
    "婚姻",
    "胎孕",
    "产育",
    "求财",
    "买卖",
    "交易",
    "出行",
    "行人",
    "失物",
    "疾病",
    "词讼",
    "功名",
    "仕宦",
    "种作",
    "蚕桑",
    "家宅",
    "坟墓",
)

SKIP_PREFIXES = (
    "序",
    "凡例",
    "目录",
    "校注",
    "说明",
)

PUNCTUATION_RE = re.compile(r"[，。；：、！？,.!?;:\s（）()《》〈〉\[\]【】\"'“”‘’]")


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
            in_comment = False
            with path.open("r", encoding="utf-8") as file:
                for line_number, raw_line in enumerate(file, start=1):
                    text = raw_line.strip()
                    if not text:
                        continue
                    if in_comment:
                        if "）" in text:
                            in_comment = False
                        continue
                    if text.startswith("（"):
                        if "）" not in text:
                            in_comment = True
                        continue
                    matched_section = match_section(text)
                    if matched_section:
                        section = matched_section
                        if source == "huangjince" and re.match(r"^\s*\d+[、.]", text):
                            in_body = True
                        if source == "yimao" and ("卷" in text or "章" in text):
                            in_body = True
                        continue
                    if not in_body:
                        continue
                    yield SourceLine(source, path, line_number, text, section)


def match_section(text: str) -> str | None:
    numeric_match = re.match(r"^\s*\d+[、.]\s*(.+?)\s*$", text)
    if numeric_match:
        return shorten_section_title(numeric_match.group(1))
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


def split_explanation(text: str) -> tuple[str, str]:
    match = re.match(r"^(.*?)（(.+?)）\s*$", text)
    if match:
        return match.group(1).strip(), match.group(2).strip()
    return text.strip(), ""


def is_candidate(raw_text: str, source: str, section: str) -> bool:
    if not raw_text or len(raw_text) < 4:
        return False
    if raw_text.startswith("（"):
        return False
    if any(raw_text.startswith(prefix) for prefix in SKIP_PREFIXES):
        return False
    if source == "yimao" and not section:
        return False
    keyword_count = sum(1 for keyword in JUDGEMENT_KEYWORDS if keyword in raw_text)
    has_result_word = any(word in raw_text for word in ("吉", "凶", "利", "不利", "成", "败", "遂", "不遂", "喜", "恶", "宜", "忌", "怕", "难", "可", "不可"))
    return keyword_count >= 1 and has_result_word


def infer_polarity(text: str) -> str:
    negative_words = ("凶", "不利", "不遂", "难", "忌", "怕", "恶", "伤", "克", "破", "败", "死", "损")
    positive_words = ("吉", "利", "遂", "成", "喜", "宜", "旺", "生", "扶", "合", "痊")
    negative = any(word in text for word in negative_words)
    positive = any(word in text for word in positive_words)
    if negative and not positive:
        return "凶"
    if positive and not negative:
        return "吉"
    if positive or negative:
        return "中性"
    return "待审"


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
    return [keyword for keyword in JUDGEMENT_KEYWORDS if keyword in text]


def stable_id(source: str, source_file: Path, line_number: int, raw_text: str) -> str:
    digest = hashlib.sha1(f"{source}:{source_file.name}:{line_number}:{raw_text}".encode("utf-8")).hexdigest()[:12]
    return f"classic_{source}_{digest}"


def normalize_text(text: str) -> str:
    return PUNCTUATION_RE.sub("", text)


def build_records() -> list[dict]:
    records = []
    seen_normalized = set()
    for source_line in iter_source_lines():
        raw_text, explanation = split_explanation(source_line.text)
        if not is_candidate(raw_text, source_line.source, source_line.section):
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
                "explanation": explanation,
                "keywords": extract_keywords(raw_text),
                "conditions_text": raw_text,
                "result_text": "",
                "polarity": infer_polarity(raw_text),
                "question_types": infer_question_types(raw_text, source_line.section),
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
