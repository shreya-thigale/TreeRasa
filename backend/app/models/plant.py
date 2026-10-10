from datetime import datetime, timezone
from sqlalchemy import DateTime, String, Float, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

class Plant(Base):
    __tablename__ = "plants"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(120))
    species: Mapped[str | None] = mapped_column(String(160), nullable=True)
    crop_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    location: Mapped[str | None] = mapped_column(String(200), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    owner = relationship("User", back_populates="plants")

class PlantScan(Base):
    __tablename__ = "plant_scans"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    plant_id: Mapped[int | None] = mapped_column(ForeignKey("plants.id", ondelete="SET NULL"), nullable=True)
    image_path: Mapped[str] = mapped_column(String(500))
    plant_part: Mapped[str] = mapped_column(String(30), default="leaf")
    predicted_label: Mapped[str | None] = mapped_column(String(200), nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="model_not_trained")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    owner = relationship("User", back_populates="scans")
