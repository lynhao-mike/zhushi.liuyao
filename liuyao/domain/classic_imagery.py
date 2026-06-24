# -*- coding: utf-8 -*-
"""Classic Liuyao imagery loading and lightweight keyword retrieval."""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATA_PATH = ROOT / "data" / "classic_imagery.jsonl"


@dataclass(frozen=True)
class ClassicImagery:
    id: str
    source: str
    source_file: str
    line_start: int
    line_end: int
    section: str
    raw_text: str
    imagery_type: str
    keywords: tuple[str, ...]
    question_types: tuple[str, ...]
    usage: str
    review_status: str
    notes: str

    @classmethod
    def from_dict(cls, data: dict) -> "ClassicImagery":
        return cls(
            id=data["id"],
            source=data["source"],
            source_file=data["source_file"],
            line_start=int(data["line_start"]),
            line_end=int(data["line_end"]),
            section=data.get("section", ""),
            raw_text=data["raw_text"],
            imagery_type=data.get("imagery_type", "general"),
            keywords=tuple(data.get("keywords", ())),
            question_types=tuple(data.get("question_types", ("other",))),
            usage=data.get("usage", "report_imagery_reference_only"),
            review_status=data.get("review_status", "candidate"),
            notes=data.get("notes", ""),
        )


def load_classic_imagery(path: Path | None = None) -> list[ClassicImagery]:
    data_path = path or DEFAULT_DATA_PATH
    records = []
    with data_path.open("r", encoding="utf-8") as file:
        for line in file:
            if line.strip():
                records.append(ClassicImagery.from_dict(json.loads(line)))
    return records


@lru_cache(maxsize=1)
def get_classic_imagery() -> tuple[ClassicImagery, ...]:
    return tuple(load_classic_imagery())


def search_classic_imagery(
    keywords: Iterable[str],
    *,
    question_type: str | None = None,
    limit: int = 5,
    include_candidate: bool = True,
) -> list[ClassicImagery]:
    query_keywords = tuple(keyword for keyword in keywords if keyword)
    if not query_keywords:
        return []

    scored = []
    for imagery in get_classic_imagery():
        if imagery.review_status == "rejected":
            continue
        if imagery.review_status == "candidate" and not include_candidate:
            continue
        if question_type and "other" not in imagery.question_types and question_type not in imagery.question_types:
            continue

        text = imagery.raw_text + imagery.section + imagery.imagery_type + "".join(imagery.keywords)
        score = sum(1 for keyword in query_keywords if keyword in text)
        if score:
            scored.append((score, imagery.line_start, imagery))

    scored.sort(key=lambda item: (-item[0], item[1], item[2].id))
    return [imagery for _, _, imagery in scored[:limit]]
