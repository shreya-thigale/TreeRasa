from datetime import datetime, timezone
from sqlalchemy import DateTime, String, ForeignKey, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base

class LabReport(Base):
    __tablename__ = "lab_reports"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    file_path: Mapped[str] = mapped_column(String(500))
    original_filename: Mapped[str] = mapped_column(String(255))
    report_type: Mapped[str] = mapped_column(String(80), default="soil_or_crop_lab")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    interpretation_status: Mapped[str] = mapped_column(String(40), default="uploaded_for_review")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class DoctorProfile(Base):
    __tablename__ = "doctor_profiles"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True)
    specialty: Mapped[str] = mapped_column(String(160))
    qualifications: Mapped[str | None] = mapped_column(String(255), nullable=True)
    region: Mapped[str | None] = mapped_column(String(160), nullable=True)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)

class Appointment(Base):
    __tablename__ = "appointments"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    requester_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    doctor_id: Mapped[int] = mapped_column(ForeignKey("doctor_profiles.id", ondelete="CASCADE"), index=True)
    requested_time: Mapped[str] = mapped_column(String(100))
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(40), default="requested")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class LabInterpretation(Base):
    """Structured measurements entered by the user after a lab file is uploaded.

    The uploaded PDF/image is not automatically OCR-parsed by this starter version.
    These values and educational comments are saved separately so original files remain intact.
    """
    __tablename__ = "lab_interpretations"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    report_id: Mapped[int] = mapped_column(ForeignKey("lab_reports.id", ondelete="CASCADE"), index=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    crop_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    values: Mapped[dict] = mapped_column(JSON, default=dict)
    guidance: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
