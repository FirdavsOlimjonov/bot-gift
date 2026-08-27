from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, Integer, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.models.user import Base


class Box(Base):
    __tablename__ = "boxes"
    __table_args__ = (
        UniqueConstraint("box_number"),
        CheckConstraint("box_number BETWEEN 1 AND 100"),
        CheckConstraint("gift_amount >= 0"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    box_number: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    gift_amount: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    is_winner: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
