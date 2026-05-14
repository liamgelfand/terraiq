from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from api.config import settings
from api.deps import get_db, require_fleet_admin
from api.models.fleet import Fleet

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/billing", tags=["billing"])


@router.post("/checkout-session")
async def create_checkout_session(
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_fleet_admin),
):
    """Create a Stripe Checkout session for the pilot subscription price (if configured)."""
    if not settings.stripe_secret_key or not settings.stripe_price_pilot_monthly:
        raise HTTPException(
            status_code=503,
            detail="Stripe billing is not configured (STRIPE_SECRET_KEY / STRIPE_PRICE_PILOT_MONTHLY).",
        )
    try:
        import stripe
    except ImportError as e:
        raise HTTPException(status_code=503, detail="stripe package not installed") from e

    user, fleet = admin
    stripe.api_key = settings.stripe_secret_key
    session = stripe.checkout.Session.create(
        mode="subscription",
        success_url=f"{settings.public_app_url}/?billing=success",
        cancel_url=f"{settings.public_app_url}/?billing=cancel",
        line_items=[{"price": settings.stripe_price_pilot_monthly, "quantity": 1}],
        customer_email=user.email,
        metadata={"fleet_id": fleet.id},
    )
    return {"url": session.url, "id": session.id}


@router.post("/webhook")
async def stripe_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    if not settings.stripe_webhook_secret:
        raise HTTPException(status_code=503, detail="Stripe webhook secret not configured")
    try:
        import stripe
    except ImportError as e:
        raise HTTPException(status_code=503, detail="stripe package not installed") from e

    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    if not sig_header:
        raise HTTPException(status_code=400, detail="Missing stripe-signature")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.stripe_webhook_secret
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Invalid payload") from e
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid signature") from e

    if event["type"] == "checkout.session.completed":
        obj = event["data"]["object"]
        fleet_id = (obj.get("metadata") or {}).get("fleet_id")
        if fleet_id:
            fleet = await db.get(Fleet, fleet_id)
            if fleet:
                fleet.stripe_customer_id = obj.get("customer")
                fleet.stripe_subscription_id = obj.get("subscription")
                fleet.billing_plan = "pilot"
                await db.commit()
                logger.info("Stripe checkout completed for fleet %s", fleet_id)
    return {"received": True}
