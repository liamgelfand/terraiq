from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from api.database import Base


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    fleet_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    corridor_id: Mapped[str | None] = mapped_column(
        String, ForeignKey("saved_corridors.id"), nullable=True, index=True
    )
    batch_id: Mapped[str | None] = mapped_column(
        String, ForeignKey("job_batches.id"), nullable=True, index=True
    )
    simulation_engine_version: Mapped[str | None] = mapped_column(String(32), nullable=True)
    lineage: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    api_key_id: Mapped[str | None] = mapped_column(
        String, ForeignKey("api_keys.id"), nullable=True, index=True
    )
    idempotency_key: Mapped[str | None] = mapped_column(
        String(128), nullable=True, index=True
    )
    status: Mapped[str] = mapped_column(String, nullable=False, default="pending")
    config: Mapped[dict] = mapped_column(JSON, nullable=False)
    result: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
