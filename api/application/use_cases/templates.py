"""
Template use cases.

ponytail: keep CRUD direct and local; no repository layer until template behavior becomes non-trivial.
"""
from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.application.use_cases.reading_support import template_to_dict
from api.core.exceptions import NotFoundError
from api.infrastructure.database.models import HexagramTemplate
from api.interfaces.http.schemas.reading import TemplateCreateRequest


async def create_template(req: TemplateCreateRequest, db: AsyncSession) -> dict[str, Any]:
    tmpl = HexagramTemplate(
        name=req.name,
        description=req.description,
        yao_values=req.yao_values,
        ganzhi_override=req.ganzhi_override,
        cast_hour=req.cast_hour,
        default_question_type=req.default_question_type,
        source_text=req.source_text,
    )
    db.add(tmpl)
    await db.flush()
    return template_to_dict(tmpl)


async def list_templates(db: AsyncSession) -> list[dict[str, Any]]:
    rows = (await db.execute(select(HexagramTemplate).order_by(HexagramTemplate.created_at))).scalars().all()
    return [template_to_dict(row) for row in rows]


async def get_template(template_id: uuid.UUID, db: AsyncSession) -> dict[str, Any]:
    row = await db.get(HexagramTemplate, template_id)
    if not row:
        raise NotFoundError(f"Template {template_id} not found")
    return template_to_dict(row)


async def delete_template(template_id: uuid.UUID, db: AsyncSession) -> None:
    row = await db.get(HexagramTemplate, template_id)
    if not row:
        raise NotFoundError(f"Template {template_id} not found")
    await db.delete(row)
