"""
Tests covering the order creation bugs identified in production.

Bug summary:
- /confirmation was not idempotent: reloading the page created duplicate orders.
- Order model lacked a UniqueConstraint on (user_id, date).
- /order route's concurrent check-then-insert could race.
- Login after a pending payment intent redirected to /confirmation without
  the payment_intent query parameter, silently discarding the order.
"""

import json
from datetime import date
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.exc import IntegrityError

from app import app as flask_app
from models import Order, db
from tests.conftest import MOCK_LUNCH_OPTIONS, login

# ---------------------------------------------------------------------------
# Shared test helpers
# ---------------------------------------------------------------------------

TEST_CART = {"2025-04-28": "Test Meal"}


def make_mock_intent(cart=None, status="succeeded"):
    if cart is None:
        cart = TEST_CART
    intent = MagicMock()
    intent.status = status
    intent.metadata = {"cart": json.dumps(cart)}
    return intent


# ---------------------------------------------------------------------------
# 1. /confirmation must be idempotent
# ---------------------------------------------------------------------------


class TestIdempotentConfirmation:
    def test_reload_does_not_create_duplicate_orders(self, client, test_user):
        """Reloading the confirmation URL must not insert a second set of orders."""
        mock_intent = make_mock_intent()

        with client:
            login(client)

            with patch("app.stripe.PaymentIntent.retrieve", return_value=mock_intent):
                resp1 = client.get("/confirmation?payment_intent=pi_test_reload")
                assert resp1.status_code == 200

                # Simulate a page reload with the same URL.
                resp2 = client.get("/confirmation?payment_intent=pi_test_reload")
                assert resp2.status_code == 200

        with flask_app.app_context():
            orders = Order.query.all()
            assert len(orders) == 1, (
                f"Expected 1 order after two confirmation loads, got {len(orders)}"
            )


# ---------------------------------------------------------------------------
# 2. UniqueConstraint on (user_id, date)
# ---------------------------------------------------------------------------


class TestUniqueConstraint:
    def test_inserting_duplicate_user_date_raises_integrity_error(self, test_user):
        """The database must reject a second order for the same user+date."""
        test_date = date(2025, 4, 28)

        with flask_app.app_context():
            order1 = Order(user_id=test_user, date=test_date, meal_name="Meal A")
            db.session.add(order1)
            db.session.commit()

            order2 = Order(user_id=test_user, date=test_date, meal_name="Meal B")
            db.session.add(order2)

            with pytest.raises(IntegrityError):
                db.session.commit()

            db.session.rollback()


# ---------------------------------------------------------------------------
# 3. Direct /order route deduplication
# ---------------------------------------------------------------------------


class TestDirectOrderRoute:
    def test_submitting_same_date_twice_does_not_duplicate(self, client, test_user):
        """Two POSTs to /order for the same date must produce exactly one row."""
        form_data = {"meal_2025-04-28": "Test Meal"}

        with client:
            login(client)
            client.post("/order", data=form_data)
            client.post("/order", data=form_data)

        with flask_app.app_context():
            orders = Order.query.all()
            assert len(orders) == 1, (
                f"Expected 1 order after two /order POSTs, got {len(orders)}"
            )


# ---------------------------------------------------------------------------
# 4. Pending payment intent redirect after login
# ---------------------------------------------------------------------------


class TestPendingPaymentRedirect:
    def test_login_redirects_to_confirmation_with_payment_intent(
        self, client, test_user
    ):
        """After storing a pending payment intent, logging in must redirect to
        /confirmation with the payment_intent query parameter included."""
        mock_intent = make_mock_intent()

        with client:
            # Visit /confirmation while not logged in — stores pending intent in session.
            with patch("app.stripe.PaymentIntent.retrieve", return_value=mock_intent):
                resp = client.get(
                    "/confirmation?payment_intent=pi_test_pending",
                    follow_redirects=False,
                )
            assert resp.status_code == 302
            assert "/login" in resp.headers["Location"]

            # Log in — the handler should redirect to /confirmation?payment_intent=...
            resp = login(client)

            assert resp.status_code == 302
            location = resp.headers["Location"]
            assert "payment_intent=pi_test_pending" in location, (
                f"Expected payment_intent in redirect URL, got: {location}"
            )
