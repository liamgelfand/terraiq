from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class ApiKeyCreate(BaseModel):
    name: str
    fleet_name: str | None = None


class ApiKeyCreatedResponse(BaseModel):
    id: str
    name: str
    fleet_name: str | None
    key_prefix: str
    raw_key: str  # shown exactly once — never stored in DB
    created_at: datetime

    model_config = {"from_attributes": True}


class ApiKeyResponse(BaseModel):
    id: str
    name: str
    fleet_name: str | None
    key_prefix: str
    is_active: bool
    usage_count: int
    created_at: datetime
    last_used_at: datetime | None

    model_config = {"from_attributes": True}
