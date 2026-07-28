import enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.subscription import Subscription


class BillingInterval(str, enum.Enum):
    MONTH = "month"
    YEAR = "year"


class Plan(Base):
    __tablename__ = "plans"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    stripe_price_id: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    price_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="usd", server_default="usd")
    interval: Mapped[BillingInterval] = mapped_column(Enum(BillingInterval, name="billing_interval"), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    subscriptions: Mapped[list["Subscription"]] = relationship(back_populates="plan")
