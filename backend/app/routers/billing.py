import stripe
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from app.core.config import settings
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.plan import Plan
from app.models.user import User
from app.schemas.billing import CheckoutSessionCreate, CheckoutSessionResponse
from app.services.stripe_service import create_checkout_session

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
