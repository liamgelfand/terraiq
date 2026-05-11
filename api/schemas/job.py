from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class JobConfig(BaseModel):
    origin: str = Field(..., description="Origin place name, e.g. 'Denver, CO'")
    destination: str = Field(..., description="Destination place name")
    vehicle_id: str = Field(default="freightliner_2022")
    job_type: str = Field(default="optimize", description="'optimize' or 'sweep'")
    load_kg: float | None = Field(
        default=None,
        ge=0,
        le=17_000,
        description="Payload weight in kg (0–17,000). Defaults to full GVW if omitted.",
    )
    time_budget_fraction: float = Field(
        default=1.05,
        ge=1.0,
        le=2.0,
        description="Max travel time as a fraction of baseline (1.05 = 5% longer allowed)",
    )


class JobCreate(BaseModel):
    config: JobConfig


class JobResponse(BaseModel):
    id: str
    status: str
    config: dict[str, Any]
    result: dict[str, Any] | None = None
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None = None

    model_config = {"from_attributes": True}
