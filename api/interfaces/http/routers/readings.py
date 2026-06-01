"""
Readings Router — /api/v1/readings
"""
from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.infrastructure.database.session import get_db
from api.interfaces.http.schemas.reading import (
    PaginatedReadings,
    ReadingCreateRequest,
    ReadingResponse,
    StatsResponse,
)
from api.application.use_cases import reading as reading_svc
from api.core.config import get_settings
from api.interfaces.http.schemas.mappers import reading_create_command_from_request

settings = get_settings()
router = APIRouter(prefix="/readings", tags=["readings"])


@router.post(
    "",
    response_model=ReadingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new divination reading",
    description="""
Perform a complete 六爻 (Six-Line) analysis.

**Two input modes:**
1. **Gregorian date** — provide `year`, `month`, `day` (and optional `hour`)
2. **Ganzhi override** — provide `ganzhi_override` for classical-text replay
   (no Gregorian date required)

The response includes the full analysis: hexagram metadata, line-by-line
旺衰 (prosperity/decline), 动变 (moving-line changes), 卦象结构模式 (structural
patterns), 吉凶判断 (auspicious/inauspicious judgment), and 应期 (timing forecast).

**Caching:** identical inputs return a cached result in ~1 ms.
""",
)
async def create_reading(
    req: ReadingCreateRequest,
    db: AsyncSession = Depends(get_db),
) -> ReadingResponse:
    command = reading_create_command_from_request(req)
    return await reading_svc.create_reading(command, db)


@router.get(
    "",
    response_model=PaginatedReadings,
    summary="List reading sessions",
)
async def list_readings(
    question_type: Optional[str] = Query(None, description="Filter by question type"),
    ji_xiong: Optional[str] = Query(None, description="Filter by 吉/凶/平"),
    page: int = Query(1, ge=1),
    size: int = Query(
        settings.DEFAULT_PAGE_SIZE,
        ge=1,
        le=settings.MAX_PAGE_SIZE,
    ),
    db: AsyncSession = Depends(get_db),
) -> PaginatedReadings:
    return await reading_svc.list_readings(db, question_type, ji_xiong, page, size)


@router.get(
    "/stats",
    response_model=StatsResponse,
    summary="Aggregated reading statistics",
)
async def get_stats(db: AsyncSession = Depends(get_db)) -> StatsResponse:
    return await reading_svc.get_stats(db)


@router.get(
    "/{reading_id}",
    response_model=ReadingResponse,
    summary="Get a single reading by ID",
)
async def get_reading(
    reading_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> ReadingResponse:
    return await reading_svc.get_reading(reading_id, db)


@router.delete(
    "/{reading_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a reading",
)
async def delete_reading(
    reading_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    await reading_svc.delete_reading(reading_id, db)
