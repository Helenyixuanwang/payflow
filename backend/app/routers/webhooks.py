import logging
from datetime import datetime, timezone
from typing import Any

import stripe
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from app.core.config import settings
from app.core.database import get_db
from app.models.plan import Plan
from app.models.subscription import Subscription, SubscriptionStatus
from app.services import stripe_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/stripe")
async def stripe_webhook(request: Request, db: AsyncSession = Depends(get_db)) -> dict[str, str]:
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    try:
        event = await run_in_threadpool(
            stripe_service.construct_webhook_event, payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except (ValueError, stripe.error.SignatureVerificationError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid webhook signature") from exc

    event_type = event["type"]
    data_object = event["data"]["object"]

    if event_type == "checkout.session.completed":
        await _handle_checkout_completed(db, data_object)
    elif event_type in ("customer.subscription.updated", "customer.subscription.deleted"):
        await _sync_subscription(db, data_object, user_id=None)
    else:
        logger.info("Unhandled Stripe event type: %s", event_type)

    return {"status": "ok"}


async def _handle_checkout_completed(db: AsyncSession, session: dict[str, Any]) -> None:
    subscription_id = session.get("subscription")
    client_reference_id = session.get("client_reference_id")

    if not subscription_id or not client_reference_id:
        logger.warning(
            "checkout.session.completed missing subscription or client_reference_id (session=%s); skipping",
            session.get("id"),
        )
        return

    subscription = await run_in_threadpool(stripe_service.retrieve_subscription, subscription_id)
    await _sync_subscription(db, subscription, user_id=int(client_reference_id))


async def _sync_subscription(db: AsyncSession, subscription: Any, user_id: int | None) -> None:
    stripe_subscription_id = subscription["id"]
    stripe_customer_id = subscription["customer"]
    status_value = SubscriptionStatus(subscription["status"])
    current_period_start = datetime.fromtimestamp(subscription["current_period_start"], tz=timezone.utc)
    current_period_end = datetime.fromtimestamp(subscription["current_period_end"], tz=timezone.utc)
    cancel_at_period_end = bool(subscription["cancel_at_period_end"])

    price_id = subscription["items"]["data"][0]["price"]["id"]
    plan = await db.scalar(select(Plan).where(Plan.stripe_price_id == price_id))
    if plan is None:
        logger.warning("No Plan found for stripe price %s (subscription=%s)", price_id, stripe_subscription_id)

    existing = await db.scalar(
        select(Subscription).where(Subscription.stripe_subscription_id == stripe_subscription_id)
    )

    if existing is not None:
        existing.stripe_customer_id = stripe_customer_id
        existing.plan_id = plan.id if plan else existing.plan_id
        existing.status = status_value
        existing.current_period_start = current_period_start
        existing.current_period_end = current_period_end
        existing.cancel_at_period_end = cancel_at_period_end
        await db.commit()
        logger.info("Updated subscription %s -> %s", stripe_subscription_id, status_value.value)
        return

    if user_id is None:
        logger.warning(
            "Received event for unknown subscription %s with no user context; skipping", stripe_subscription_id
        )
        return

    db.add(
        Subscription(
            user_id=user_id,
            plan_id=plan.id if plan else None,
            stripe_customer_id=stripe_customer_id,
            stripe_subscription_id=stripe_subscription_id,
            status=status_value,
            current_period_start=current_period_start,
            current_period_end=current_period_end,
            cancel_at_period_end=cancel_at_period_end,
        )
    )
    await db.commit()
    logger.info("Created subscription %s for user %s", stripe_subscription_id, user_id)
