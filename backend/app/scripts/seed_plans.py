"""One-time seed for the Basic/Pro Plan rows. Run from backend/ with:

    python -m app.scripts.seed_plans
"""

import asyncio

import stripe
from sqlalchemy import select

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.models import BillingInterval, Plan

stripe.api_key = settings.STRIPE_SECRET_KEY

PLANS = [
    ("Basic", settings.STRIPE_PRICE_BASIC),
    ("Pro", settings.STRIPE_PRICE_PRO),
]


def resolve_price(configured_id: str) -> stripe.Price:
    """STRIPE_PRICE_* may hold either a Price id or a Product id (Stripe's
    dashboard often surfaces the product id first); resolve either to the
    product's default Price."""
    if configured_id.startswith("prod_"):
        product = stripe.Product.retrieve(configured_id, expand=["default_price"])
        if product.default_price is None:
            raise RuntimeError(f"Product {configured_id} has no default price set")
        return product.default_price
    return stripe.Price.retrieve(configured_id)


async def seed_plans() -> None:
    async with AsyncSessionLocal() as db:
        for name, configured_id in PLANS:
            price = resolve_price(configured_id)

            existing = await db.scalar(select(Plan).where(Plan.stripe_price_id == price.id))
            if existing is not None:
                print(f"Skipping {name}: already seeded (plan id={existing.id}, price={price.id})")
                continue

            plan = Plan(
                name=name,
                stripe_price_id=price.id,
                price_cents=price.unit_amount,
                currency=price.currency,
                interval=BillingInterval(price.recurring.interval),
            )
            db.add(plan)
            await db.commit()
            print(
                f"Created plan {name} (id={plan.id}, price={price.id}, "
                f"{plan.price_cents / 100:.2f} {plan.currency.upper()}/{plan.interval.value})"
            )


if __name__ == "__main__":
    asyncio.run(seed_plans())
