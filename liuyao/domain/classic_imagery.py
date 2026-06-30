"""Classic Liuyao imagery loading and lightweight keyword retrieval."""

from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import dataclass
from functools import lru_cache
from heapq import nsmallest
from pathlib import Path

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
    search_text: str

    @classmethod
    def from_dict(cls, data: dict) -> ClassicImagery:
        keywords = tuple(data.get("keywords", ()))
        raw_text = data["raw_text"]
        section = data.get("section", "")
        imagery_type = data.get("imagery_type", "general")
        return cls(
            id=data["id"],
            source=data["source"],
            source_file=data["source_file"],
            line_start=int(data["line_start"]),
            line_end=int(data["line_end"]),
            section=section,
            raw_text=raw_text,
            imagery_type=imagery_type,
            keywords=keywords,
            question_types=tuple(data.get("question_types", ("other",))),
            usage=data.get("usage", "report_imagery_reference_only"),
            review_status=data.get("review_status", "candidate"),
            notes=data.get("notes", ""),
            search_text=raw_text + section + imagery_type + "".join(keywords),
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


def clear_classic_imagery_caches() -> None:
    get_classic_imagery.cache_clear()
    _classic_imagery_keyword_matches.cache_clear()
    _search_classic_imagery_cached.cache_clear()


@lru_cache(maxsize=256)
def _classic_imagery_keyword_matches(keyword: str) -> tuple[int, ...]:
    return tuple(
        index
        for index, imagery in enumerate(get_classic_imagery())
        if keyword in imagery.search_text
    )


def _classic_imagery_candidate_indexes(query_keywords: tuple[str, ...]) -> set[int]:
    candidate_indexes: set[int] = set()
    for keyword in query_keywords:
        candidate_indexes.update(_classic_imagery_keyword_matches(keyword))
    return candidate_indexes


def search_classic_imagery(
    keywords: Iterable[str],
    *,
    question_type: str | None = None,
    limit: int = 5,
    include_candidate: bool = True,
) -> list[ClassicImagery]:
    query_keywords = tuple(keyword for keyword in keywords if keyword)
    return list(_search_classic_imagery_cached(
        query_keywords,
        question_type,
        limit,
        include_candidate,
    ))


@lru_cache(maxsize=128)
def _search_classic_imagery_cached(
    query_keywords: tuple[str, ...],
    question_type: str | None,
    limit: int,
    include_candidate: bool,
) -> tuple[ClassicImagery, ...]:
    if not query_keywords or limit <= 0:
        return ()

    imagery_records = get_classic_imagery()
    candidate_indexes = _classic_imagery_candidate_indexes(query_keywords)

    scored = []
    for index in candidate_indexes:
        imagery = imagery_records[index]
        if imagery.review_status == "rejected":
            continue
        if imagery.review_status == "candidate" and not include_candidate:
            continue
        if question_type and "other" not in imagery.question_types and question_type not in imagery.question_types:
            continue

        score = sum(1 for keyword in query_keywords if keyword in imagery.search_text)
        if score:
            scored.append((-score, imagery.line_start, imagery.id, imagery))

    top_matches = nsmallest(limit, scored)
    return tuple(imagery for _, _, _, imagery in top_matches)
