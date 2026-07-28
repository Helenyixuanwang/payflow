import stripe

from app.core.config import settings

stripe.api_key = settings.STRIPE_SECRET_KEY


def create_checkout_session(
    *,
    price_id: str,
    customer_email: str,
    client_reference_id: str,
    success_url: str,
    cancel_url: str,
) -> stripe.checkout.Session:
    return stripe.checkout.Session.create(
        mode="subscription",
        line_items=[{"price": price_id, "quantity": 1}],
        customer_email=customer_email,
        client_reference_id=client_reference_id,
        success_url=success_url,
        cancel_url=cancel_url,
    )


def retrieve_subscription(subscription_id: str) -> stripe.Subscription:
    return stripe.Subscription.retrieve(subscription_id)


def cancel_subscription_at_period_end(subscription_id: str) -> stripe.Subscription:
    return stripe.Subscription.modify(subscription_id, cancel_at_period_end=True)


def construct_webhook_event(payload: bytes, sig_header: str, webhook_secret: str) -> stripe.Event:
    return stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
