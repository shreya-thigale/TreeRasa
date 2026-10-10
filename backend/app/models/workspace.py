"""Flexible records for the operational modules that share the same CRUD pattern.

Core entities such as users, plants, scans, products and appointments have dedicated
SQLAlchemy models. This model is reserved for structured workspace records whose
fields vary by module (for example farm observations, drone missions and soil tests).
"""
from datetime import datetime, timezone
from sqlalchemy import DateTime, ForeignKey, JSON, String, Text, Index
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class WorkspaceRecord(Base):
    __tablename__ = "workspace_records"
    __table_args__ = (Index("ix_workspace_owner_module", "owner_id", "module_key"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    module_key: Mapped[str] = mapped_column(String(60), index=True)
    title: Mapped[str] = mapped_column(String(180))
    data: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
