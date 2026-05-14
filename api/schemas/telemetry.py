from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class TelemetryResponse(BaseModel):
    id: str
    fleet_id: str
    job_id: str | None
    corridor_id: str | None
    original_filename: str
    row_count: int
    status: str
    adherence: dict[str, Any] | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TelemetryListPage(BaseModel):
    items: list[TelemetryResponse]
    total: int
    page: int
    page_size: int


class TelemetryLinkBody(BaseModel):
    job_id: str = Field(..., min_length=8)
    corridor_id: str | None = None
