# -*- coding: utf-8 -*-
"""Classic Liuyao judgement loading and lightweight keyword retrieval."""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from heapq import nsmallest
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
    search_text: str

    @classmethod
    def from_dict(cls, data: dict) -> "ClassicJudgement":
        keywords = tuple(data.get("keywords", ()))
        raw_text = data["raw_text"]
        section = data.get("section", "")
        return cls(
            id=data["id"],
            source=data["source"],
            source_file=data["source_file"],
            line_start=int(data["line_start"]),
            line_end=int(data["line_end"]),
            section=section,
            raw_text=raw_text,
            explanation=data.get("explanation", ""),
            keywords=keywords,
            conditions_text=data.get("conditions_text", ""),
            result_text=data.get("result_text", ""),
            polarity=data.get("polarity", "待审"),
            question_types=tuple(data.get("question_types", ("other",))),
            review_status=data.get("review_status", "candidate"),
            notes=data.get("notes", ""),
            search_text=raw_text + section + "".join(keywords),
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


def clear_classic_judgements_caches() -> None:
    get_classic_judgements.cache_clear()
    _classic_judgement_keyword_matches.cache_clear()
    _search_classic_judgements_cached.cache_clear()


@lru_cache(maxsize=256)
def _classic_judgement_keyword_matches(keyword: str) -> tuple[int, ...]:
    return tuple(
        index
        for index, judgement in enumerate(get_classic_judgements())
        if keyword in judgement.search_text
    )


def _classic_judgement_candidate_indexes(query_keywords: tuple[str, ...]) -> set[int]:
    candidate_indexes: set[int] = set()
    for keyword in query_keywords:
        candidate_indexes.update(_classic_judgement_keyword_matches(keyword))
    return candidate_indexes


def search_classic_judgements(
    keywords: Iterable[str],
    *,
    question_type: str | None = None,
    limit: int = 5,
    include_candidate: bool = True,
) -> list[ClassicJudgement]:
    query_keywords = tuple(keyword for keyword in keywords if keyword)
    return list(_search_classic_judgements_cached(
        query_keywords,
        question_type,
        limit,
        include_candidate,
    ))


@lru_cache(maxsize=128)
def _search_classic_judgements_cached(
    query_keywords: tuple[str, ...],
    question_type: str | None,
    limit: int,
    include_candidate: bool,
) -> tuple[ClassicJudgement, ...]:
    if not query_keywords or limit <= 0:
        return ()

    judgements = get_classic_judgements()
    candidate_indexes = _classic_judgement_candidate_indexes(query_keywords)

    scored = []
    for index in candidate_indexes:
        judgement = judgements[index]
        if judgement.review_status == "rejected":
            continue
        if judgement.review_status == "candidate" and not include_candidate:
            continue
        if question_type and "other" not in judgement.question_types and question_type not in judgement.question_types:
            continue

        score = sum(1 for keyword in query_keywords if keyword in judgement.search_text)
        if score:
            scored.append((-score, judgement.line_start, judgement.id, judgement))

    top_matches = nsmallest(limit, scored)
    return tuple(judgement for _, _, _, judgement in top_matches)
