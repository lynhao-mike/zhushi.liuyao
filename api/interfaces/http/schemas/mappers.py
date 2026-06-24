"""
HTTP schema mappers for reading use cases.

Keeping the conversion here avoids leaking FastAPI/Pydantic models deeper into
application service internals.
"""
from __future__ import annotations

from api.application.use_cases.dto import (
    ReadingCreateCommand,
    ReadingFeedbackCreateCommand,
    TemplateCreateCommand,
)
from api.interfaces.http.schemas.reading import (
    ReadingCreateRequest,
    ReadingFeedbackCreateRequest,
    TemplateCreateRequest,
)


def reading_create_command_from_request(req: ReadingCreateRequest) -> ReadingCreateCommand:
    return ReadingCreateCommand(
        yao_values=req.yao_values,
        question_type=req.question_type,
        question=req.question,
        querent_name=req.querent_name,
        is_dual=req.is_dual,
        year=req.year,
        month=req.month,
        day=req.day,
        hour=req.hour,
        ganzhi_override=req.ganzhi_override.model_dump() if req.ganzhi_override else None,
    )


def reading_feedback_create_command_from_request(req: ReadingFeedbackCreateRequest) -> ReadingFeedbackCreateCommand:
    return ReadingFeedbackCreateCommand(
        actual_outcome=req.actual_outcome,
        feedback_text=req.feedback_text,
    )


def template_create_command_from_request(req: TemplateCreateRequest) -> TemplateCreateCommand:
    return TemplateCreateCommand(
        name=req.name,
        description=req.description,
        yao_values=req.yao_values,
        ganzhi_override=req.ganzhi_override.model_dump() if req.ganzhi_override else None,
        cast_hour=req.cast_hour,
        default_question_type=req.default_question_type,
        source_text=req.source_text,
    )
