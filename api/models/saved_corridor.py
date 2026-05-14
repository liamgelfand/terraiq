from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from api.database import Base


class SavedCorridor(Base):
    __tablename__ = "saved_corridors"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    fleet_id: Mapped[str] = mapped_column(String, ForeignKey("fleets.id"), index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    origin: Mapped[str] = mapped_column(Text, nullable=False)
    destination: Mapped[str] = mapped_column(Text, nullable=False)
    vehicle_id: Mapped[str] = mapped_column(String(64), nullable=False, default="freightliner_2022")
    load_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    time_budget_fraction: Mapped[float] = mapped_column(Float, nullable=False, default=1.05)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
