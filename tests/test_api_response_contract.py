"""HTTP 响应模型契约回归测试。"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from api.interfaces.http.schemas.reading import (
    PaginatedReadings,
    ReadingFeedbackResponse,
    ReadingResponse,
    StatsResponse,
    TemplateResponse,
)


def _reading_payload() -> dict:
    return {
        "id": str(uuid.uuid4()),
        "question_type": "other",
        "question_type_label": "其他/综合",
        "question": None,
        "querent_name": None,
        "is_dual": False,
        "ben_gua_name": "雷火丰",
        "bian_gua_name": "风山渐",
        "palace_name": "震",
        "palace_wu_xing": "木",
        "xun_kong": ["辰", "巳"],
        "gan_zhi": {"year": "丙午", "month": "癸巳", "day": "己亥", "hour": "辛未"},
        "lines": [],
        "wangshuai": [],
        "dongbian": {},
        "patterns": {},
        "star_spirits": {},
        "jixiong": {"pattern": "用旺世兴局", "ji_xiong": "吉", "explanation": "测试解释"},
        "yingqi": [],
        "perspectives": None,
        "dual_consensus": None,
        "report_text": None,
        "report_readable": None,
        "report_files": [],
        "from_cache": False,
        "created_at": datetime.now(UTC).isoformat(),
    }


def test_reading_response_accepts_service_payload():
    """create/get reading 服务字典必须能通过 HTTP response_model 校验。"""
    response = ReadingResponse.model_validate(_reading_payload())

    assert response.question_type == "other"
    assert response.jixiong is not None
    assert response.jixiong.ji_xiong == "吉"


def test_paginated_readings_accepts_summary_payload():
    """list_readings 服务字典必须能通过分页响应模型校验。"""
    item = {
        "id": str(uuid.uuid4()),
        "question_type": "other",
        "question_type_label": "其他/综合",
        "question": "测试",
        "querent_name": None,
        "ben_gua_name": "雷火丰",
        "bian_gua_name": "风山渐",
        "ji_xiong": "吉",
        "gua_ju_pattern": "用旺世兴局",
        "is_dual": False,
        "created_at": datetime.now(UTC),
    }

    response = PaginatedReadings.model_validate(
        {"items": [item], "total": 1, "page": 1, "size": 20, "pages": 1}
    )

    assert response.items[0].ji_xiong == "吉"


def test_stats_template_and_feedback_responses_accept_service_payloads():
    """统计、模板、反馈服务字典必须保持 response_model 兼容。"""
    stats = StatsResponse.model_validate(
        {
            "total_readings": 1,
            "total_by_question_type": {"other": 1},
            "total_by_ji_xiong": {"吉": 1},
            "top_ben_gua": [{"gua": "雷火丰", "count": 1}],
            "cache_hit_rate": None,
        }
    )
    template = TemplateResponse.model_validate(
        {
            "id": str(uuid.uuid4()),
            "name": "模板",
            "description": None,
            "yao_values": [7, 7, 7, 7, 7, 7],
            "ganzhi_override": None,
            "cast_hour": 12,
            "default_question_type": "other",
            "source_text": None,
            "created_at": datetime.now(UTC),
        }
    )
    feedback = ReadingFeedbackResponse.model_validate(
        {
            "id": str(uuid.uuid4()),
            "reading_id": str(uuid.uuid4()),
            "actual_outcome": "已应验",
            "feedback_text": None,
            "status": "submitted",
            "original_judgement": {"ji_xiong": "吉"},
            "created_at": datetime.now(UTC),
        }
    )

    assert stats.total_readings == 1
    assert template.name == "模板"
    assert feedback.status == "submitted"
