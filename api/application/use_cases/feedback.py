"""
Feedback use cases.

ponytail: only move the feedback flow out of `reading.py`; keep the DB access concrete until a second real caller forces more structure.
"""
from __future__ import annotations

import uuid
from typing import Any, Dict

from sqlalchemy.ext.asyncio import AsyncSession

from api.application.use_cases.dto import ReadingFeedbackCreateCommand
from api.application.use_cases.reading_support import feedback_to_dict
from api.core.exceptions import NotFoundError
from api.infrastructure.database.models import ReadingFeedback, ReadingSession


async def create_reading_feedback(
    reading_id: uuid.UUID,
    req: ReadingFeedbackCreateCommand,
    db: AsyncSession,
) -> Dict[str, Any]:
    row = await db.get(ReadingSession, reading_id)
    if not row:
        raise NotFoundError(f"Reading {reading_id} not found")

    feedback = ReadingFeedback(
        reading_id=reading_id,
        actual_outcome=req.actual_outcome,
        feedback_text=req.feedback_text,
        status="submitted",
        original_judgement=row.jixiong_json,
    )
    db.add(feedback)
    await db.flush()
    return feedback_to_dict(feedback)
