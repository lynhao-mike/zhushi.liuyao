# -*- coding: utf-8 -*-
"""Classic Liuyao judgement loading and lightweight keyword retrieval."""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATA_PATH = ROOT / "data" / "classic_judgements.jsonl"


@dataclass(frozen=True)
class ClassicJudgement:
    id: str
    source: str
    source_file: str
    line_start: int
    line_end: int
    section: str
    raw_text: str
    explanation: str
    keywords: tuple[str, ...]
    conditions_text: str
    result_text: str
    polarity: str
    question_types: tuple[str, ...]
    review_status: str
    notes: str

    @classmethod
    def from_dict(cls, data: dict) -> "ClassicJudgement":
        return cls(
            id=data["id"],
            source=data["source"],
            source_file=data["source_file"],
            line_start=int(data["line_start"]),
            line_end=int(data["line_end"]),
            section=data.get("section", ""),
            raw_text=data["raw_text"],
            explanation=data.get("explanation", ""),
            keywords=tuple(data.get("keywords", ())),
            conditions_text=data.get("conditions_text", ""),
            result_text=data.get("result_text", ""),
            polarity=data.get("polarity", "待审"),
            question_types=tuple(data.get("question_types", ("other",))),
            review_status=data.get("review_status", "candidate"),
            notes=data.get("notes", ""),
        )


def load_classic_judgements(path: Path | None = None) -> list[ClassicJudgement]:
    data_path = path or DEFAULT_DATA_PATH
    records = []
    with data_path.open("r", encoding="utf-8") as file:
        for line in file:
            if line.strip():
                records.append(ClassicJudgement.from_dict(json.loads(line)))
    return records


@lru_cache(maxsize=1)
def get_classic_judgements() -> tuple[ClassicJudgement, ...]:
    return tuple(load_classic_judgements())


def search_classic_judgements(
    keywords: Iterable[str],
    *,
    question_type: str | None = None,
    limit: int = 5,
    include_candidate: bool = True,
) -> list[ClassicJudgement]:
    query_keywords = tuple(keyword for keyword in keywords if keyword)
    if not query_keywords:
        return []

    scored = []
    for judgement in get_classic_judgements():
        if judgement.review_status == "rejected":
            continue
        if judgement.review_status == "candidate" and not include_candidate:
            continue
        if question_type and "other" not in judgement.question_types and question_type not in judgement.question_types:
            continue

        text = judgement.raw_text + judgement.section + "".join(judgement.keywords)
        score = sum(1 for keyword in query_keywords if keyword in text)
        if score:
            scored.append((score, judgement.line_start, judgement))

    scored.sort(key=lambda item: (-item[0], item[1], item[2].id))
    return [judgement for _, _, judgement in scored[:limit]]
