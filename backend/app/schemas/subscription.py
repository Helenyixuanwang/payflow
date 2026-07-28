from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.subscription import SubscriptionStatus


class PlanRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    price_cents: int
    currency: str
    interval: str


class SubscriptionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: SubscriptionStatus
    current_period_start: datetime
    current_period_end: datetime
    cancel_at_period_end: bool
    plan: PlanRead | None
    created_at: datetime
