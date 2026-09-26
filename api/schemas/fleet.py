from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class InviteCreateRequest(BaseModel):
    email: EmailStr


class InviteResponse(BaseModel):
    id: str
    email: str
    fleet_id: str
    created_at: datetime
    expires_at: datetime


class AuditEventResponse(BaseModel):
    id: str
    actor_user_id: str
    action: str
    resource_type: str
    resource_id: str | None
    details: dict | None
    created_at: datetime

    model_config = {"from_attributes": True}


class WebhookDeliveryResponse(BaseModel):
    id: str
    job_id: str
    url: str
    event: str
    attempt: int
    http_status: int | None
    error_message: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class FleetUsageResponse(BaseModel):
    jobs_total: int
    jobs_completed: int
    jobs_failed: int
    jobs_this_month: int
    api_key_usage_total: int
    billing_plan: str
    plan_label: str
    jobs_limit_monthly: int | None
    jobs_remaining_this_month: int | None
    corridors_count: int
    corridors_limit: int | None
    stripe_configured: bool


class AuditLogPage(BaseModel):
    items: list[AuditEventResponse]
    total: int
    page: int
    page_size: int


class WebhookDeliveryPage(BaseModel):
    items: list[WebhookDeliveryResponse]
    total: int
    page: int
    page_size: int


class DataPurgeBody(BaseModel):
    include_jobs: bool = Field(
        default=False,
        description="If true, deletes all fleet jobs (and webhook deliveries). Otherwise clears corridor/batch links only.",
    )
