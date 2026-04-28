import json
import pytest
from unittest.mock import patch
from app import app as flask_app, db, User, Order
from werkzeug.security import generate_password_hash


@pytest.fixture
def app_ctx():
    """Return the Flask app for use as an app context manager."""
    return flask_app


def _make_event(user_id, cart, payment_intent_id="pi_test_webhook_123"):
    return {
        "id": "evt_test_123",
        "type": "payment_intent.succeeded",
        "data": {
            "object": {
                "id": payment_intent_id,
                "object": "payment_intent",
                "status": "succeeded",
                "metadata": {
                    "user_id": str(user_id),
                    "cart": json.dumps(cart),
                },
            }
        },
    }


def _post_webhook(client, event_dict):
    payload = json.dumps(event_dict).encode()
    with patch("app.stripe.Webhook.construct_event", return_value=event_dict):
        return client.post(
            "/webhook",
            data=payload,
            content_type="application/json",
            headers={"Stripe-Signature": "t=1,v1=test"},
        )


def _create_user(app_ctx, username="webhook@example.com"):
    with app_ctx.app_context():
        user = User(
            username=username,
            password_hash=generate_password_hash("pw"),
        )
        db.session.add(user)
        db.session.commit()
        return user.id


def test_webhook_creates_orders_on_payment_succeeded(client, app_ctx):
    user_id = _create_user(app_ctx)
    cart = {"2026-05-19": "Chimichurri Carne Asada Burrito"}
    event = _make_event(user_id, cart)

    response = _post_webhook(client, event)

    assert response.status_code == 200
    with app_ctx.app_context():
        orders = Order.query.filter_by(payment_intent_id="pi_test_webhook_123").all()
        assert len(orders) == 1
        assert orders[0].user_id == user_id
        assert orders[0].meal_name == "Chimichurri Carne Asada Burrito"


def test_webhook_is_idempotent(client, app_ctx):
    user_id = _create_user(app_ctx, username="idempotent@example.com")
    cart = {"2026-05-19": "Test Meal"}
    event = _make_event(user_id, cart, payment_intent_id="pi_idempotent_456")

    _post_webhook(client, event)
    _post_webhook(client, event)

    with app_ctx.app_context():
        orders = Order.query.filter_by(payment_intent_id="pi_idempotent_456").all()
        assert len(orders) == 1, f"Expected 1 order, got {len(orders)}"


def test_webhook_rejects_invalid_signature(client, app_ctx):
    import stripe
    with patch(
        "app.stripe.Webhook.construct_event",
        side_effect=stripe.SignatureVerificationError("bad sig", "sig_header"),
    ):
        response = client.post(
            "/webhook",
            data=b'{"type": "payment_intent.succeeded"}',
            content_type="application/json",
            headers={"Stripe-Signature": "invalid"},
        )
    assert response.status_code == 400
