from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from api.database import Base


class TelemetryUpload(Base):
    __tablename__ = "telemetry_uploads"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    fleet_id: Mapped[str] = mapped_column(String, ForeignKey("fleets.id"), index=True)
    job_id: Mapped[str | None] = mapped_column(
        String, ForeignKey("jobs.id"), nullable=True, index=True
    )
    corridor_id: Mapped[str | None] = mapped_column(
        String, ForeignKey("saved_corridors.id"), nullable=True, index=True
    )
    original_filename: Mapped[str] = mapped_column(String(512), nullable=False)
    row_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    points: Mapped[list | None] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    adherence: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
