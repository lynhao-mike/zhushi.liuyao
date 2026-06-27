# -*- coding: utf-8 -*-
"""最小阅读反馈用例测试。"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest

from api.application.use_cases.dto import ReadingFeedbackCreateCommand
from api.application.use_cases.feedback import create_reading_feedback
from api.infrastructure.database.models import ReadingSession


class FakeResult:
    def __init__(self, row):
        self._row = row

    def scalar_one_or_none(self):
        return self._row


class FakeDB:
    def __init__(self, row):
        self._row = row
        self.added = None
        self.flushed = False

    async def get(self, model, key):
        return self._row if key == self._row.id else None

    async def execute(self, stmt):
        return FakeResult(self._row)

    def add(self, obj):
        self.added = obj

    async def flush(self):
        self.flushed = True


@pytest.mark.asyncio
async def test_create_reading_feedback_persists_snapshot_and_links_reading():
    reading_id = uuid.uuid4()
    reading = ReadingSession(
        id=reading_id,
        question="test",
        question_type="other",
        is_dual=False,
        yao_values=[8, 7, 7, 6, 7, 8],
        cast_hour=12,
        jixiong_json={"rule_id": "P1_TEST", "ji_xiong": "吉"},
        created_at=datetime.now(timezone.utc),
    )
    db = FakeDB(reading)
    req = ReadingFeedbackCreateCommand(
        actual_outcome="事情已解决",
        feedback_text="用户实际结果反馈",
    )

    result = await create_reading_feedback(reading_id, req, db)

    assert db.added is not None
    assert db.flushed is True
    assert result["reading_id"] == reading_id
    assert result["actual_outcome"] == "事情已解决"
    assert result["feedback_text"] == "用户实际结果反馈"
    assert result["status"] == "submitted"
    assert result["original_judgement"] == {"rule_id": "P1_TEST", "ji_xiong": "吉"}
    assert db.added.reading_id == reading_id
    assert db.added.original_judgement == {"rule_id": "P1_TEST", "ji_xiong": "吉"}
