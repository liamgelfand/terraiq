from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class BatchCreate(BaseModel):
    corridor_ids: list[str] = Field(..., min_length=1, max_length=100)
    name: str | None = Field(default=None, max_length=200)


class BatchResponse(BaseModel):
    id: str
    fleet_id: str
    name: str | None
    status: str
    config: dict[str, Any]
    summary: dict[str, Any] | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None

    model_config = {"from_attributes": True}


class BatchListPage(BaseModel):
    items: list[BatchResponse]
    total: int
    page: int
    page_size: int
