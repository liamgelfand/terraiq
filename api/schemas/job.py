from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, computed_field

from api.error_codes import describe_error_code


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
    corridor_id: str | None = Field(
        default=None,
        description="Optional saved corridor id — sets job.corridor_id for ops reporting.",
    )


class JobResponse(BaseModel):
    id: str
    status: str
    config: dict[str, Any]
    result: dict[str, Any] | None = None
    error_message: str | None = None
    error_code: str | None = None
    corridor_id: str | None = None
    batch_id: str | None = None
    simulation_engine_version: str | None = None
    lineage: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None = None

    model_config = {"from_attributes": True}

    @computed_field
    def error_hint(self) -> str | None:
        return describe_error_code(self.error_code)


class JobListPage(BaseModel):
    items: list[JobResponse]
    total: int
    page: int
    page_size: int
