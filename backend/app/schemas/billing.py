from pydantic import BaseModel


class CheckoutSessionCreate(BaseModel):
    plan_id: int


class CheckoutSessionResponse(BaseModel):
    checkout_url: str
