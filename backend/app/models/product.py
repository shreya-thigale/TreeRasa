from datetime import datetime
from sqlalchemy import String, Text, Integer, Float, ForeignKey, DateTime, LargeBinary, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base

class Product(Base):
    __tablename__ = "products"
    __table_args__ = (CheckConstraint("price >= 0"), CheckConstraint("stock >= 0"))
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    seller_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(160))
    description: Mapped[str] = mapped_column(Text, default="")
    listing_type: Mapped[str] = mapped_column(String(20), index=True)  # produce or supply
    category: Mapped[str] = mapped_column(String(60), index=True)  # fruit, vegetable, fertilizer, seeds, pesticide...
    price: Mapped[float] = mapped_column(Float)
    unit: Mapped[str] = mapped_column(String(30), default="kg")
    stock: Mapped[int] = mapped_column(Integer, default=0)
    image_data: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    image_mime: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    seller = relationship("User", back_populates="products")
