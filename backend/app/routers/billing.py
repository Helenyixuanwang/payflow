import stripe
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from starlette.concurrency import run_in_threadpool

from app.core.config import settings
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.plan import Plan
from app.models.subscription import Subscription, SubscriptionStatus
from app.models.user import User
from app.schemas.billing import CheckoutSessionCreate, CheckoutSessionResponse
from app.schemas.subscription import SubscriptionRead
from app.services.stripe_service import cancel_subscription_at_period_end, create_checkout_session

router = APIRouter(prefix="/billing", tags=["billing"])


@router.post("/checkout-session", response_model=CheckoutSessionResponse)
async def create_checkout_session_endpoint(
    payload: CheckoutSessionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CheckoutSessionResponse:
    plan = await db.get(Plan, payload.plan_id)
    if plan is None or not plan.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")

    try:
        session = await run_in_threadpool(
            create_checkout_session,
            price_id=plan.stripe_price_id,
            customer_email=current_user.email,
            client_reference_id=str(current_user.id),
            success_url=f"{settings.FRONTEND_URL}/dashboard?checkout=success",
            cancel_url=f"{settings.FRONTEND_URL}/dashboard?checkout=cancel",
        )
    except stripe.error.StripeError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    return CheckoutSessionResponse(checkout_url=session.url)


@router.get("/subscription", response_model=SubscriptionRead | None)
async def get_current_subscription(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Subscription | None:
    return await db.scalar(
        select(Subscription)
        .where(Subscription.user_id == current_user.id)
        .order_by(Subscription.created_at.desc())
        .limit(1)
        .options(selectinload(Subscription.plan))
    )


@router.post("/subscription/cancel", response_model=SubscriptionRead)
async def cancel_current_subscription(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SubscriptionRead:
    subscription = await db.scalar(
        select(Subscription)
        .where(Subscription.user_id == current_user.id, Subscription.status == SubscriptionStatus.ACTIVE)
        .order_by(Subscription.created_at.desc())
        .limit(1)
        .options(selectinload(Subscription.plan))
    )
    if subscription is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No active subscription found")

    try:
        await run_in_threadpool(cancel_subscription_at_period_end, subscription.stripe_subscription_id)
    except stripe.error.StripeError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    # Stripe's response already reflects the change, but the DB row is only
    # updated by the webhook handler once customer.subscription.updated
    # arrives, so we overlay the field we know just changed rather than
    # writing to the row here ourselves.
    return SubscriptionRead.model_validate(subscription).model_copy(update={"cancel_at_period_end": True})
