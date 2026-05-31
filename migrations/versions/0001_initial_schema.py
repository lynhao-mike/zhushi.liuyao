"""Initial schema: reading_sessions, analysis_cache, hexagram_templates

Revision ID: 0001
Revises:
Create Date: 2025-01-01 00:00:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── reading_sessions ──────────────────────────────────────────────
    op.create_table(
        "reading_sessions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("question", sa.Text, nullable=True),
        sa.Column("question_type", sa.String(32), nullable=False),
        sa.Column("querent_name", sa.String(128), nullable=True),
        sa.Column("is_dual", sa.Boolean, default=False, nullable=False),
        # Raw inputs
        sa.Column("yao_values", ARRAY(sa.SmallInteger), nullable=False),
        sa.Column("cast_year",  sa.Integer, nullable=True),
        sa.Column("cast_month", sa.Integer, nullable=True),
        sa.Column("cast_day",   sa.Integer, nullable=True),
        sa.Column("cast_hour",  sa.SmallInteger, default=12),
        sa.Column("ganzhi_override", JSONB, nullable=True),
        # Computed hexagram metadata
        sa.Column("ben_gua_name",   sa.String(16), nullable=True),
        sa.Column("bian_gua_name",  sa.String(16), nullable=True),
        sa.Column("palace_name",    sa.String(8),  nullable=True),
        sa.Column("palace_wu_xing", sa.String(4),  nullable=True),
        sa.Column("xun_kong", ARRAY(sa.String(2)), nullable=True),
        sa.Column("gan_zhi", JSONB, nullable=True),
        # Analysis blobs
        sa.Column("lines_json",        JSONB, nullable=True),
        sa.Column("wangshuai_json",    JSONB, nullable=True),
        sa.Column("dongbian_json",     JSONB, nullable=True),
        sa.Column("patterns_json",     JSONB, nullable=True),
        sa.Column("jixiong_json",      JSONB, nullable=True),
        sa.Column("yingqi_json",       JSONB, nullable=True),
        sa.Column("star_spirits_json", JSONB, nullable=True),
        # Reports
        sa.Column("report_text",     sa.Text, nullable=True),
        sa.Column("report_readable", sa.Text, nullable=True),
        # Dual
        sa.Column("dual_perspectives_json", JSONB, nullable=True),
        sa.Column("dual_consensus", sa.String(256), nullable=True),
        # Summary
        sa.Column("ji_xiong",       sa.String(4),  nullable=True),
        sa.Column("gua_ju_pattern", sa.String(64), nullable=True),
        # Audit
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_reading_sessions_created_at",     "reading_sessions", ["created_at"])
    op.create_index("ix_reading_sessions_question_type",  "reading_sessions", ["question_type"])
    op.create_index("ix_reading_sessions_ben_gua_name",   "reading_sessions", ["ben_gua_name"])
    op.create_index("ix_reading_sessions_ji_xiong",       "reading_sessions", ["ji_xiong"])
    op.create_index(
        "ix_reading_sessions_question_type_ji_xiong",
        "reading_sessions", ["question_type", "ji_xiong"]
    )
    op.create_index(
        "ix_reading_sessions_ben_gua_created",
        "reading_sessions", ["ben_gua_name", "created_at"]
    )

    # ── analysis_cache ────────────────────────────────────────────────
    op.create_table(
        "analysis_cache",
        sa.Column("id",            sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("fingerprint",   sa.String(64), nullable=False, unique=True),
        sa.Column("question_type", sa.String(32), nullable=False),
        sa.Column("is_dual",       sa.Boolean, default=False),
        sa.Column("payload",       JSONB, nullable=False),
        sa.Column("hit_count",     sa.Integer, default=0),
        sa.Column("created_at",    sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("last_hit_at",   sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_analysis_cache_fingerprint", "analysis_cache", ["fingerprint"], unique=True)

    # ── hexagram_templates ────────────────────────────────────────────
    op.create_table(
        "hexagram_templates",
        sa.Column("id",                   UUID(as_uuid=True), primary_key=True),
        sa.Column("name",                 sa.String(128), nullable=False),
        sa.Column("description",          sa.Text, nullable=True),
        sa.Column("yao_values",           ARRAY(sa.SmallInteger), nullable=False),
        sa.Column("ganzhi_override",      JSONB, nullable=True),
        sa.Column("cast_hour",            sa.SmallInteger, default=12),
        sa.Column("default_question_type", sa.String(32), default="other"),
        sa.Column("source_text",          sa.String(256), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_hexagram_templates_name", "hexagram_templates", ["name"])


def downgrade() -> None:
    op.drop_table("hexagram_templates")
    op.drop_table("analysis_cache")
    op.drop_table("reading_sessions")
