from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_db, require_founder
from api.models.lead import Lead

router = APIRouter(prefix="/api/leads", tags=["leads"])


class LeadOut(BaseModel):
    id: str
    name: str
    email: str
    company: str
    fleet_size: str | None
    message: str | None
    source: str
    status: str
    created_at: str

    model_config = {"from_attributes": True}


class LeadStatusBody(BaseModel):
    status: str = Field(..., pattern="^(new|contacted|won|lost)$")


def _out(row: Lead) -> LeadOut:
    return LeadOut(
        id=row.id,
        name=row.name,
        email=row.email,
        company=row.company,
        fleet_size=row.fleet_size,
        message=row.message,
        source=row.source,
        status=row.status,
        created_at=row.created_at.isoformat() if row.created_at else "",
    )


@router.get("", response_model=list[LeadOut])
async def list_leads(
    db: AsyncSession = Depends(get_db),
    _founder=Depends(require_founder),
):
    res = await db.execute(select(Lead).order_by(desc(Lead.created_at)).limit(200))
    return [_out(row) for row in res.scalars().all()]


@router.patch("/{lead_id}", response_model=LeadOut)
async def update_lead_status(
    lead_id: str,
    body: LeadStatusBody,
    db: AsyncSession = Depends(get_db),
    _founder=Depends(require_founder),
):
    row = await db.get(Lead, lead_id)
    if not row:
        raise HTTPException(status_code=404, detail="Lead not found")
    row.status = body.status
    await db.commit()
    await db.refresh(row)
    return _out(row)
