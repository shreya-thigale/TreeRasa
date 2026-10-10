"""Task-specific AI results linked to a saved plant image.

Separate rows allow TreeRasa to keep disease and pest model results distinct without
mixing their label spaces or requiring a destructive change to existing scan tables.
"""
from datetime import datetime, timezone
from sqlalchemy import DateTime, ForeignKey, Float, String
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class ScanAnalysis(Base):
    __tablename__ = "scan_analyses"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    scan_id: Mapped[int] = mapped_column(ForeignKey("plant_scans.id", ondelete="CASCADE"), index=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    analysis_type: Mapped[str] = mapped_column(String(30), default="disease", index=True)
    predicted_label: Mapped[str | None] = mapped_column(String(200), nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(40), default="model_not_trained")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
