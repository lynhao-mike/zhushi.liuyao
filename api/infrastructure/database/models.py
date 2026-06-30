"""
SQLAlchemy ORM models.

Schema design principles:
  - ReadingSession  : core aggregate — one row per divination reading.
  - ReadingFeedback : user-submitted actual outcome/feedback for a reading.
  - HexagramTemplate: reusable named hexagram configurations (optional convenience).
  - AnalysisCache   : denormalized cache table for repeated identical readings
                      (supplements Redis; survives restarts).
  - All JSONB columns use native PostgreSQL JSONB for rich querying.
"""
from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func


def _utcnow() -> datetime:
    return datetime.now(UTC)


class Base(DeclarativeBase):
    pass


# ── ReadingSession ────────────────────────────────────────────────────────────

class ReadingSession(Base):
    """
    One divination reading end-to-end.

    Raw inputs are stored separately from computed results so we can
    re-run analysis without losing the original data.
    """
    __tablename__ = "reading_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # ── Question context ──────────────────────────────────────────────
    question: Mapped[str | None] = mapped_column(Text, nullable=True)
    question_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    querent_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    is_dual: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # ── Raw hexagram inputs ───────────────────────────────────────────
    yao_values: Mapped[list[int]] = mapped_column(
        ARRAY(SmallInteger), nullable=False
    )

    # Gregorian date (nullable when ganzhi_override is provided)
    cast_year: Mapped[int | None]  = mapped_column(Integer, nullable=True)
    cast_month: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cast_day: Mapped[int | None]   = mapped_column(Integer, nullable=True)
    cast_hour: Mapped[int] = mapped_column(SmallInteger, default=12)

    # Optional direct ganzhi override (for classical-text replay)
    ganzhi_override: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # ── Computed hexagram metadata ────────────────────────────────────
    ben_gua_name: Mapped[str | None]   = mapped_column(String(16), nullable=True, index=True)
    bian_gua_name: Mapped[str | None]  = mapped_column(String(16), nullable=True)
    palace_name: Mapped[str | None]    = mapped_column(String(8),  nullable=True)
    palace_wu_xing: Mapped[str | None] = mapped_column(String(4),  nullable=True)
    xun_kong: Mapped[list[str] | None] = mapped_column(ARRAY(String(2)), nullable=True)
    gan_zhi: Mapped[dict | None]       = mapped_column(JSONB, nullable=True)

    # ── Full analysis results (JSONB blobs) ───────────────────────────
    lines_json: Mapped[dict | None]         = mapped_column(JSONB, nullable=True)
    wangshuai_json: Mapped[dict | None]     = mapped_column(JSONB, nullable=True)
    dongbian_json: Mapped[dict | None]      = mapped_column(JSONB, nullable=True)
    patterns_json: Mapped[dict | None]      = mapped_column(JSONB, nullable=True)
    jixiong_json: Mapped[dict | None]       = mapped_column(JSONB, nullable=True)
    yingqi_json: Mapped[dict | None]        = mapped_column(JSONB, nullable=True)
    star_spirits_json: Mapped[dict | None]  = mapped_column(JSONB, nullable=True)

    # Full formatted reports
    report_text: Mapped[str | None]          = mapped_column(Text, nullable=True)
    report_readable: Mapped[str | None]      = mapped_column(Text, nullable=True)

    # Dual-perspective extras
    dual_perspectives_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    dual_consensus: Mapped[str | None] = mapped_column(String(256), nullable=True)

    # ── Summary (denormalised for quick listing) ──────────────────────
    ji_xiong: Mapped[str | None] = mapped_column(String(4), nullable=True, index=True)
    gua_ju_pattern: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # ── Audit ─────────────────────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow,
        onupdate=_utcnow, server_default=func.now()
    )

    # ── Relationships ─────────────────────────────────────────────────
    feedbacks: Mapped[list[ReadingFeedback]] = relationship(
        back_populates="reading", cascade="all, delete-orphan"
    )

    # ── Indexes ───────────────────────────────────────────────────────
    __table_args__ = (
        Index("ix_reading_sessions_created_at", "created_at"),
        Index("ix_reading_sessions_question_type_ji_xiong", "question_type", "ji_xiong"),
        Index("ix_reading_sessions_ben_gua_created", "ben_gua_name", "created_at"),
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<ReadingSession {self.id} {self.ben_gua_name} {self.ji_xiong}>"


# ── ReadingFeedback ───────────────────────────────────────────────────────────

class ReadingFeedback(Base):
    """User feedback for a completed reading."""

    __tablename__ = "reading_feedbacks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    reading_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("reading_sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    actual_outcome: Mapped[str] = mapped_column(Text, nullable=False)
    feedback_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="submitted", nullable=False, index=True)
    original_judgement: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, server_default=func.now()
    )

    reading: Mapped[ReadingSession] = relationship(back_populates="feedbacks")

    __table_args__ = (
        Index("ix_reading_feedbacks_status_created", "status", "created_at"),
    )


# ── AnalysisCache ─────────────────────────────────────────────────────────────

class AnalysisCache(Base):
    """
    Persistent deterministic cache keyed by the hexagram fingerprint.
    Supplements Redis; survives Redis restarts.

    Fingerprint = SHA-256 of (sorted yao_values | ganzhi_key | question_type | is_dual).
    """
    __tablename__ = "analysis_cache"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    fingerprint: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)

    question_type: Mapped[str] = mapped_column(String(32), nullable=False)
    is_dual: Mapped[bool] = mapped_column(Boolean, default=False)

    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)

    hit_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, server_default=func.now()
    )
    last_hit_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


# ── HexagramTemplate ──────────────────────────────────────────────────────────

class HexagramTemplate(Base):
    """
    Named, reusable hexagram configurations.
    Useful for saving classical text examples or frequently-used readings.
    """
    __tablename__ = "hexagram_templates"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    yao_values: Mapped[list[int]] = mapped_column(ARRAY(SmallInteger), nullable=False)
    ganzhi_override: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    cast_hour: Mapped[int] = mapped_column(SmallInteger, default=12)

    # Optional canonical question context
    default_question_type: Mapped[str] = mapped_column(
        String(32), default="other", nullable=False
    )
    source_text: Mapped[str | None] = mapped_column(
        String(256), nullable=True,
        comment="e.g. '增删卜易第42例'"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, server_default=func.now()
    )

    __table_args__ = (
        Index("ix_hexagram_templates_name", "name"),
    )
