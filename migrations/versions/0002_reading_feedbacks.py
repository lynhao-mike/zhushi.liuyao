"""Add reading feedbacks

Revision ID: 0002_reading_feedbacks
Revises: 0001
Create Date: 2026-06-24 00:00:00.000000

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "0002_reading_feedbacks"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "reading_feedbacks",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "reading_id",
            UUID(as_uuid=True),
            sa.ForeignKey("reading_sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("actual_outcome", sa.Text, nullable=False),
        sa.Column("feedback_text", sa.Text, nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="submitted"),
        sa.Column("original_judgement", JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_reading_feedbacks_reading_id", "reading_feedbacks", ["reading_id"])
    op.create_index("ix_reading_feedbacks_status", "reading_feedbacks", ["status"])
    op.create_index(
        "ix_reading_feedbacks_status_created",
        "reading_feedbacks",
        ["status", "created_at"],
    )


def downgrade() -> None:
    op.drop_table("reading_feedbacks")
