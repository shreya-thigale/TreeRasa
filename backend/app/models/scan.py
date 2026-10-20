from datetime import datetime
from sqlalchemy import String, Text, ForeignKey, DateTime, LargeBinary, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base

class PlantScan(Base):
    __tablename__ = "plant_scans"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    crop_name: Mapped[str | None] = mapped_column(String(80), nullable=True)
    predicted_disease: Mapped[str] = mapped_column(String(160), default="Not analyzed")
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    recommendations: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(40), default="model_not_configured")
    image_data: Mapped[bytes] = mapped_column(LargeBinary)
    image_mime: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    user = relationship("User")
