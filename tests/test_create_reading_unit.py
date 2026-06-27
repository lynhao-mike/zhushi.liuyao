# -*- coding: utf-8 -*-
"""
create_reading() 最小单元安全网。

不依赖真实 DB / Redis / liuyao engine：全部用 stub 替换。
目的：在重构 reading.py 时，如果核心编排逻辑被破坏，这里会最先报错。
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from api.application.use_cases.dto import ReadingCreateCommand
from api.application.use_cases.readings import create_reading
from api.application.use_cases.reading_support import orm_to_response as _orm_to_response


# ── Fake DB ───────────────────────────────────────────────────────────────────

class _FakeSession:
    def __init__(self):
        self._store: Dict[str, Any] = {}
        self.added: List[Any] = []
        self.flushed = False

    async def get(self, model, key):
        return None  # 无缓存行

    async def execute(self, stmt):
        result = MagicMock()
        result.scalar_one_or_none.return_value = None
        result.scalars.return_value.all.return_value = []
        result.scalar_one.return_value = 0
        return result

    def add(self, obj):
        # 注入一个假 id，模拟 DB flush 后 id 已存在
        if not getattr(obj, "id", None):
            obj.id = uuid.uuid4()
        self.added.append(obj)

    async def flush(self):
        self.flushed = True


# ── Stub engine result ────────────────────────────────────────────────────────

_STUB_ENGINE_RESULT: Dict[str, Any] = {
    "hexagram_meta": {
        "ben_gua_name": "雷火丰",
        "bian_gua_name": "风山渐",
        "palace_name": "震",
        "palace_wu_xing": "木",
        "xun_kong": ["辰", "巳"],
        "gan_zhi": {"year": "丙午", "month": "癸巳", "day": "己亥", "hour": "辛未"},
        "lines": [],
        "shi_pos": 5,
        "ying_pos": 2,
    },
    "analysis": {
        "wangshuai": [],
        "dongbian": {},
        "patterns": {},
        "star_spirits": {},
        "jixiong": {"ji_xiong": "吉", "rule_id": "TEST"},
        "yingqi": [],
    },
    "report_text": "技术报告内容",
    "report_readable": "可读报告内容",
    "report_files": [],
    "ji_xiong": "吉",
    "gua_ju_pattern": None,
}

_STUB_REQ = ReadingCreateCommand(
    yao_values=[9, 8, 7, 9, 6, 6],
    year=2026,
    month=5,
    day=25,
    hour=14,
    question_type="shiwu",
    question="金首饰丢失能否找回",
    querent_name="张女士",
)


@pytest.mark.asyncio
async def test_create_reading_returns_response_with_id():
    db = _FakeSession()

    with (
        patch("api.application.use_cases.readings.get_cache", AsyncMock(return_value=None)),
        patch("api.application.use_cases.readings.set_cache", AsyncMock()),
        patch("api.application.use_cases.readings.invalidate_prefix", AsyncMock(return_value=0)),
        patch("api.application.use_cases.readings.analyze", AsyncMock(return_value=_STUB_ENGINE_RESULT)),
        patch("api.application.use_cases.reading_support.archive_reports", MagicMock(return_value=[])),
    ):
        result = await create_reading(_STUB_REQ, db)

    assert result["ben_gua_name"] == "雷火丰"
    assert result["question_type"] == "shiwu"
    assert "id" in result
    assert db.flushed is True


@pytest.mark.asyncio
async def test_cache_hit_with_missing_report_files_is_rewarmed_after_recovery():
    """旧 Redis payload 缺少 report_files 时，只补一次并把补全结果写回缓存。"""
    db = _FakeSession()
    cached_payload = {
        **_STUB_ENGINE_RESULT["hexagram_meta"],
        "id": str(uuid.uuid4()),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "question_type": "shiwu",
        "question_type_label": "失物",
        "question": "测试",
        "querent_name": "",
        "is_dual": False,
        "wangshuai": [],
        "dongbian": {},
        "patterns": {},
        "star_spirits": {},
        "jixiong": None,
        "yingqi": [],
        "perspectives": None,
        "dual_consensus": None,
        "report_text": "技术报告内容",
        "report_readable": None,
    }
    set_cache = AsyncMock()

    with (
        patch("api.application.use_cases.readings.get_cache", AsyncMock(return_value=cached_payload)),
        patch("api.application.use_cases.readings.set_cache", set_cache),
        patch("api.application.use_cases.reading_support.archive_reports", MagicMock(return_value=["examples/reports/recovered.txt"])),
        patch("api.application.use_cases.readings.analyze", AsyncMock(side_effect=AssertionError("engine should not run on cache hit"))),
    ):
        result = await create_reading(_STUB_REQ, db)

    assert result["from_cache"] is True
    assert result["report_files"] == ["examples/reports/recovered.txt"]
    assert set_cache.await_count == 1
    warmed_payload = set_cache.await_args.args[1]
    assert warmed_payload["report_files"] == ["examples/reports/recovered.txt"]


@pytest.mark.asyncio
async def test_create_reading_returns_cache_hit_without_db_write():
    """Redis 命中时不应该触发 DB write 或 engine。"""
    db = _FakeSession()
    cached_payload = {
        **_STUB_ENGINE_RESULT["hexagram_meta"],
        "id": str(uuid.uuid4()),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "question_type": "shiwu",
        "question_type_label": "失物",
        "question": "测试",
        "querent_name": "",
        "is_dual": False,
        "wangshuai": [],
        "dongbian": {},
        "patterns": {},
        "star_spirits": {},
        "jixiong": None,
        "yingqi": [],
        "perspectives": None,
        "dual_consensus": None,
        "report_text": None,
        "report_readable": None,
        "report_files": ["examples/reports/test.txt"],  # 已有文件，不再写盘
    }

    with (
        patch("api.application.use_cases.readings.get_cache", AsyncMock(return_value=cached_payload)),
        patch("api.application.use_cases.readings.analyze", AsyncMock(side_effect=AssertionError("engine should not run on cache hit"))),
    ):
        result = await create_reading(_STUB_REQ, db)

    assert result["from_cache"] is True
    assert db.flushed is False  # 无 DB write
    assert result["question"] == "测试"
    assert result["querent_name"] == ""


@pytest.mark.asyncio
async def test_create_reading_cache_key_includes_question_context():
    """不同占问文本/求测人不能复用同一个 create 响应缓存。"""
    db = _FakeSession()
    get_cache = AsyncMock(return_value=None)

    with (
        patch("api.application.use_cases.readings.get_cache", get_cache),
        patch("api.application.use_cases.readings.set_cache", AsyncMock()),
        patch("api.application.use_cases.readings.invalidate_prefix", AsyncMock(return_value=0)),
        patch("api.application.use_cases.readings.analyze", AsyncMock(return_value=_STUB_ENGINE_RESULT)),
        patch("api.application.use_cases.reading_support.archive_reports", MagicMock(return_value=[])),
    ):
        await create_reading(_STUB_REQ, db)
        await create_reading(
            ReadingCreateCommand(
                yao_values=_STUB_REQ.yao_values,
                year=_STUB_REQ.year,
                month=_STUB_REQ.month,
                day=_STUB_REQ.day,
                hour=_STUB_REQ.hour,
                question_type=_STUB_REQ.question_type,
                question="同一卦但另一个问题",
                querent_name="李先生",
            ),
            db,
        )

    first_key = get_cache.await_args_list[0].args[0]
    second_key = get_cache.await_args_list[1].args[0]
    assert first_key != second_key


def test_orm_to_response_is_read_only_for_archived_report_text():
    """GET 详情不能因为存在报告正文而重复写归档文件。"""
    reading = __import__("api.infrastructure.database.models", fromlist=["ReadingSession"]).ReadingSession(
        id=uuid.uuid4(),
        question="测试重复读取",
        question_type="other",
        is_dual=False,
        yao_values=[8, 7, 7, 6, 7, 8],
        cast_hour=12,
        lines_json=[],
        xun_kong=[],
        gan_zhi={},
        report_text="技术报告内容",
        report_readable="可读报告内容",
        created_at=datetime.now(timezone.utc),
    )

    with patch(
        "api.application.use_cases.reading_support.archive_reports",
        MagicMock(side_effect=AssertionError("GET should not archive reports")),
    ):
        result = _orm_to_response(reading)

    assert result["report_text"] == "技术报告内容"
    assert result["report_readable"] == "可读报告内容"
    assert result["report_files"] == []
