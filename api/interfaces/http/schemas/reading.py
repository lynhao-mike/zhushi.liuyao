"""
Pydantic v2 schemas for reading sessions (request / response).
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from liuyao import QUESTION_TYPE_LABELS


# ── Shared validators ────────────────────────────────────────────────────────

VALID_QUESTION_TYPES = {
    "cai", "guan", "hun_male", "hun_female",
    "bing", "kaoshi", "zinv", "xingRen",
    "youHuan", "shiwu", "other",
}


# ── Ganzhi override sub-schema ────────────────────────────────────────────────

class GanzhiOverride(BaseModel):
    """Direct stem-branch injection (classical text replay)."""
    month_zhi: str = Field(..., description="月支，如 '巳'")
    day_zhi: str   = Field(..., description="日支，如 '申'")
    day_gan: Optional[str] = Field(None, description="日干（可缺省，由旬空反推）")
    xun_kong: Optional[List[str]] = Field(None, description="旬空两地支，如 ['寅','卯']")
    year_gan: str = Field("甲", description="年干（仅展示用）")
    year_zhi: str = Field("子", description="年支（仅展示用）")
    month_gan: str = Field("甲", description="月干（仅展示用）")

    @field_validator("xun_kong")
    @classmethod
    def validate_xun_kong(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        if v is not None and len(v) != 2:
            raise ValueError("xun_kong must contain exactly 2 earthly branches")
        return v


# ── Request ───────────────────────────────────────────────────────────────────

class ReadingCreateRequest(BaseModel):
    """
    POST /readings

    Two casting modes:
      1. Gregorian date (year/month/day) + optional hour
      2. Ganzhi override (for classical-text replay, no Gregorian date needed)
    """
    # Core yao values — always required
    yao_values: List[int] = Field(
        ...,
        min_length=6,
        max_length=6,
        description="六次摇卦结果 [初爻..上爻]，每值为 6/7/8/9",
        examples=[[8, 7, 7, 6, 7, 8]],
    )

    # Question context
    question_type: str = Field(
        "other",
        description=f"问事类型: {', '.join(VALID_QUESTION_TYPES)}",
    )
    question: Optional[str] = Field(None, max_length=500, description="自由文本占问")
    querent_name: Optional[str] = Field(None, max_length=128)
    is_dual: Optional[bool] = Field(
        None,
        description="双视角模式（失物/疾病默认开启，可覆盖）",
    )

    # Gregorian date (mode 1)
    year: Optional[int]  = Field(None, ge=1900, le=2100)
    month: Optional[int] = Field(None, ge=1,    le=12)
    day: Optional[int]   = Field(None, ge=1,    le=31)
    hour: int            = Field(12,  ge=0,    le=23)

    # Ganzhi override (mode 2)
    ganzhi_override: Optional[GanzhiOverride] = None

    @field_validator("yao_values")
    @classmethod
    def validate_yao_values(cls, v: List[int]) -> List[int]:
        for val in v:
            if val not in (6, 7, 8, 9):
                raise ValueError(f"Each yao value must be 6, 7, 8, or 9 — got {val}")
        return v

    @field_validator("question_type")
    @classmethod
    def validate_question_type(cls, v: str) -> str:
        if v not in VALID_QUESTION_TYPES:
            raise ValueError(f"question_type must be one of: {', '.join(sorted(VALID_QUESTION_TYPES))}")
        return v

    @model_validator(mode="after")
    def validate_date_or_ganzhi(self) -> "ReadingCreateRequest":
        has_date = self.year is not None and self.month is not None and self.day is not None
        has_override = self.ganzhi_override is not None
        if not has_date and not has_override:
            raise ValueError(
                "Provide either (year + month + day) or ganzhi_override"
            )
        if has_date and has_override:
            raise ValueError(
                "Provide either (year + month + day) or ganzhi_override, not both"
            )
        return self


# ── Response sub-objects ──────────────────────────────────────────────────────

class YaoLineResponse(BaseModel):
    position: int
    yao_type: int
    yin_yang: int
    is_moving: bool
    tian_gan: str
    di_zhi: str
    wu_xing: str
    liu_qin: str
    liu_shen: str
    is_shi: bool
    is_ying: bool
    is_xun_kong: bool
    bian_tian_gan: Optional[str] = None
    bian_di_zhi: Optional[str] = None
    bian_wu_xing: Optional[str] = None
    bian_liu_qin: Optional[str] = None


class JixiongResponse(BaseModel):
    pattern: str
    ji_xiong: str
    explanation: str
    kuayi_supplements: Optional[List[Dict[str, Any]]] = None


class YingqiResponse(BaseModel):
    position: int
    di_zhi: str
    liu_qin: str
    candidates: List[str]


class PerspectiveResponse(BaseModel):
    perspective_label: str
    yong_shen_liu_qin: str
    jixiong: JixiongResponse
    yingqi: List[YingqiResponse]


class ReadingResponse(BaseModel):
    id: uuid.UUID
    question_type: str
    question_type_label: str
    question: Optional[str]
    querent_name: Optional[str]
    is_dual: bool

    # Hexagram metadata
    ben_gua_name: str
    bian_gua_name: str
    palace_name: str
    palace_wu_xing: str
    xun_kong: List[str]
    gan_zhi: Dict[str, str]

    # Lines
    lines: List[YaoLineResponse]

    # Core analysis
    wangshuai: List[Dict[str, Any]]
    dongbian: Dict[str, Any]
    patterns: Dict[str, Any]
    star_spirits: Dict[str, Any]
    jixiong: Optional[JixiongResponse] = None         # single-perspective
    yingqi: Optional[List[YingqiResponse]] = None     # single-perspective

    # Dual perspective
    perspectives: Optional[List[PerspectiveResponse]] = None
    dual_consensus: Optional[str] = None

    # Formatted reports
    report_text: Optional[str] = None
    report_readable: Optional[str] = None
    report_files: List[str] = Field(default_factory=list)

    # Meta
    from_cache: bool = False
    created_at: datetime

    model_config = {"from_attributes": True}


class ReadingFeedbackCreateRequest(BaseModel):
    actual_outcome: str = Field(..., min_length=1, max_length=2000)
    feedback_text: Optional[str] = Field(None, max_length=4000)


class ReadingFeedbackResponse(BaseModel):
    id: uuid.UUID
    reading_id: uuid.UUID
    actual_outcome: str
    feedback_text: Optional[str]
    status: str
    original_judgement: Optional[Dict[str, Any]]
    created_at: datetime

    model_config = {"from_attributes": True}


class ReadingSummary(BaseModel):
    """Lightweight row for list endpoints."""
    id: uuid.UUID
    question_type: str
    question_type_label: str
    question: Optional[str]
    querent_name: Optional[str]
    ben_gua_name: Optional[str]
    bian_gua_name: Optional[str]
    ji_xiong: Optional[str]
    gua_ju_pattern: Optional[str]
    is_dual: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Pagination ────────────────────────────────────────────────────────────────

class PaginatedReadings(BaseModel):
    items: List[ReadingSummary]
    total: int
    page: int
    size: int
    pages: int


# ── Template schemas ──────────────────────────────────────────────────────────

class TemplateCreateRequest(BaseModel):
    name: str = Field(..., max_length=128)
    description: Optional[str] = Field(None, max_length=1000)
    yao_values: List[int] = Field(..., min_length=6, max_length=6)
    ganzhi_override: Optional[GanzhiOverride] = None
    cast_hour: int = Field(12, ge=0, le=23)
    default_question_type: str = Field("other")
    source_text: Optional[str] = Field(None, max_length=256)

    @field_validator("yao_values")
    @classmethod
    def validate_yao_values(cls, v: List[int]) -> List[int]:
        for val in v:
            if val not in (6, 7, 8, 9):
                raise ValueError(f"Each yao value must be 6, 7, 8, or 9 — got {val}")
        return v


class TemplateResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: Optional[str]
    yao_values: List[int]
    ganzhi_override: Optional[Dict[str, Any]]
    cast_hour: int
    default_question_type: str
    source_text: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Stats ─────────────────────────────────────────────────────────────────────

class StatsResponse(BaseModel):
    total_readings: int
    total_by_question_type: Dict[str, int]
    total_by_ji_xiong: Dict[str, int]
    top_ben_gua: List[Dict[str, Any]]
    cache_hit_rate: Optional[float] = None
