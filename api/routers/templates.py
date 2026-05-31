"""
Templates Router — /api/v1/templates

Reusable named hexagram configurations (classical text examples, etc.).
"""
from __future__ import annotations

import uuid
from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.db.session import get_db
from api.schemas.reading import TemplateCreateRequest, TemplateResponse
from api.services import reading as reading_svc

router = APIRouter(prefix="/templates", tags=["templates"])


@router.post(
    "",
    response_model=TemplateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Save a hexagram template",
)
async def create_template(
    req: TemplateCreateRequest,
    db: AsyncSession = Depends(get_db),
) -> TemplateResponse:
    return await reading_svc.create_template(req, db)


@router.get(
    "",
    response_model=List[TemplateResponse],
    summary="List all templates",
)
async def list_templates(db: AsyncSession = Depends(get_db)) -> List[TemplateResponse]:
    return await reading_svc.list_templates(db)


@router.get(
    "/{template_id}",
    response_model=TemplateResponse,
    summary="Get a template by ID",
)
async def get_template(
    template_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> TemplateResponse:
    return await reading_svc.get_template(template_id, db)


@router.delete(
    "/{template_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a template by ID",
)
async def delete_template(
    template_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    await reading_svc.delete_template(template_id, db)
