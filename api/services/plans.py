"""Billing-plan limits for the paid-pilot product.

Free fleets can evaluate the product; paid `pilot` / `enterprise` plans raise the ceiling.
Limits are enforced when creating jobs, batches, and corridors, not on reads.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.config import settings
from api.models.fleet import Fleet
from api.models.job import Job
from api.models.saved_corridor import SavedCorridor


@dataclass(frozen=True)
class PlanLimits:
    key: str
    label: str
    jobs_per_month: int | None
    max_corridors: int | None
    max_batch_size: int


def _unlimited(label: str) -> PlanLimits:
    return PlanLimits(
        key="enterprise",
        label=label,
        jobs_per_month=None,
        max_corridors=None,
        max_batch_size=50,
    )


def plan_for_account(fleet: Fleet, *, actor_email: str | None = None) -> PlanLimits:
    """Local DEBUG and founder emails have no monthly job or corridor cap."""
    from api.deps import is_founder_email  # noqa: PLC0415

    if settings.debug:
        return _unlimited("Dev")
    if actor_email and is_founder_email(actor_email):
        return _unlimited("Founder")
    return resolve_plan(getattr(fleet, "billing_plan", "free"))


def apply_founder_plan(fleet: Fleet, email: str) -> None:
    """Persist unlimited plan for the founder so API keys inherit it too."""
    from api.deps import is_founder_email  # noqa: PLC0415

    if is_founder_email(email) and getattr(fleet, "billing_plan", "free") != "enterprise":
        fleet.billing_plan = "enterprise"


def resolve_plan(billing_plan: str | None) -> PlanLimits:
    key = (billing_plan or "free").strip().lower()
    if key in ("enterprise", "unlimited"):
        return _unlimited("Enterprise")
    if key == "pilot":
        return PlanLimits(
            key="pilot",
            label="Pilot",
            jobs_per_month=settings.pilot_jobs_per_month,
            max_corridors=settings.pilot_max_corridors,
            max_batch_size=25,
        )
    return PlanLimits(
        key="free",
        label="Trial",
        jobs_per_month=settings.free_jobs_per_month,
        max_corridors=settings.free_max_corridors,
        max_batch_size=5,
    )


def month_start_utc(now: datetime | None = None) -> datetime:
    current = now or datetime.now(timezone.utc)
    return datetime(current.year, current.month, 1, tzinfo=timezone.utc)


async def count_jobs_this_month(db: AsyncSession, fleet_id: str) -> int:
    start = month_start_utc()
    result = await db.execute(
        select(func.count())
        .select_from(Job)
        .where(and_(Job.fleet_id == fleet_id, Job.created_at >= start))
    )
    return int(result.scalar_one() or 0)


async def count_corridors(db: AsyncSession, fleet_id: str) -> int:
    result = await db.execute(
        select(func.count()).select_from(SavedCorridor).where(SavedCorridor.fleet_id == fleet_id)
    )
    return int(result.scalar_one() or 0)


def _quota_error(*, code: str, message: str, plan: PlanLimits, extra: dict | None = None) -> HTTPException:
    detail: dict = {
        "error_code": code,
        "message": message,
        "plan": plan.key,
        "plan_label": plan.label,
    }
    if extra:
        detail.update(extra)
    return HTTPException(status_code=402, detail=detail)


async def assert_can_create_jobs(
    db: AsyncSession, fleet: Fleet, n: int = 1, *, actor_email: str | None = None
) -> None:
    """Raise 402 if this fleet cannot enqueue `n` additional jobs this month."""
    if n < 1:
        return
    plan = plan_for_account(fleet, actor_email=actor_email)
    if plan.max_batch_size is not None and n > plan.max_batch_size:
        raise _quota_error(
            code="BATCH_TOO_LARGE",
            message=(
                f"{plan.label} plans can submit at most {plan.max_batch_size} jobs in one batch. "
                "Upgrade to raise this limit."
            ),
            plan=plan,
            extra={"requested": n, "max_batch_size": plan.max_batch_size},
        )
    if plan.jobs_per_month is None:
        return
    used = await count_jobs_this_month(db, fleet.id)
    if used + n > plan.jobs_per_month:
        remaining = max(0, plan.jobs_per_month - used)
        raise _quota_error(
            code="QUOTA_EXCEEDED",
            message=(
                f"{plan.label} plan allows {plan.jobs_per_month} optimization jobs per month "
                f"({used} used, {remaining} remaining). Start a paid pilot to continue."
            ),
            plan=plan,
            extra={
                "jobs_this_month": used,
                "jobs_limit": plan.jobs_per_month,
                "jobs_remaining": remaining,
                "requested": n,
            },
        )


async def assert_can_create_corridor(
    db: AsyncSession, fleet: Fleet, *, actor_email: str | None = None
) -> None:
    plan = plan_for_account(fleet, actor_email=actor_email)
    if plan.max_corridors is None:
        return
    used = await count_corridors(db, fleet.id)
    if used >= plan.max_corridors:
        raise _quota_error(
            code="CORRIDOR_LIMIT",
            message=(
                f"{plan.label} plan allows {plan.max_corridors} saved corridors "
                f"({used} in use). Delete unused lanes or upgrade."
            ),
            plan=plan,
            extra={"corridors_count": used, "corridors_limit": plan.max_corridors},
        )


def remaining_jobs(used: int, plan: PlanLimits) -> int | None:
    if plan.jobs_per_month is None:
        return None
    return max(0, plan.jobs_per_month - used)
