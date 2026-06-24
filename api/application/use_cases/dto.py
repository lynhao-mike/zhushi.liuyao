"""
Application-level DTOs for reading use cases.

These dataclasses decouple application services from FastAPI/Pydantic request
models while preserving the existing HTTP schema contract at the router edge.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class ReadingCreateCommand:
    yao_values: List[int]
    question_type: str = "other"
    question: Optional[str] = None
    querent_name: Optional[str] = None
    is_dual: Optional[bool] = None
    year: Optional[int] = None
    month: Optional[int] = None
    day: Optional[int] = None
    hour: int = 12
    ganzhi_override: Optional[Dict[str, Any]] = None


@dataclass(frozen=True)
class ReadingFeedbackCreateCommand:
    actual_outcome: str
    feedback_text: Optional[str] = None


@dataclass(frozen=True)
class TemplateCreateCommand:
    name: str
    description: Optional[str]
    yao_values: List[int]
    ganzhi_override: Optional[Dict[str, Any]]
    cast_hour: int
    default_question_type: str
    source_text: Optional[str]
