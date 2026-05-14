from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class CorridorCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    origin: str = Field(..., min_length=1)
    destination: str = Field(..., min_length=1)
    vehicle_id: str = Field(default="freightliner_2022")
    load_kg: float | None = Field(default=None, ge=0, le=17_000)
    time_budget_fraction: float = Field(default=1.05, ge=1.0, le=2.0)


class CorridorUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    origin: str | None = None
    destination: str | None = None
    vehicle_id: str | None = None
    load_kg: float | None = Field(default=None, ge=0, le=17_000)
    time_budget_fraction: float | None = Field(default=None, ge=1.0, le=2.0)


class CorridorResponse(BaseModel):
    id: str
    fleet_id: str
    name: str
    origin: str
    destination: str
    vehicle_id: str
    load_kg: float | None
    time_budget_fraction: float
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
