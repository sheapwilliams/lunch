import stripe as stripe_module
from unittest.mock import patch, MagicMock

from app import app as flask_app
import app as app_module


def _inject_cart(client, cart, user_id):
    """Inject a cart into the server-side cachelib session.

    Flask-session stores data in a FileSystemCache keyed by the session cookie
    value.  session_transaction() only touches the signed cookie, not the
    server-side store, so we must write directly to the cache.
    """
    cookie = client.get_cookie("session")
    if cookie is None:
        return
    session_id = cookie.value
    cache = flask_app.config["SESSION_CACHELIB"]
    session_data = cache.get("session:" + session_id) or {}
    session_data["cart"] = cart
    # Set user_id to match current_user.id so before_request does not reset cart.
    session_data["user_id"] = user_id
    cache.set("session:" + session_id, session_data)


def test_checkout_includes_user_id_in_metadata(client, logged_in_user):
    """PaymentIntent metadata must include user_id so the webhook can create orders."""
    mock_intent = MagicMock()
    mock_intent.client_secret = "pi_test_secret_123"

    _inject_cart(client, {"2025-04-28": "Test Meal"}, logged_in_user.id)

    stripe_module.api_key = "sk_test_fake"

    with patch.object(app_module, "STRIPE_PUBLIC_KEY", "pk_test_fake"), \
         patch("app.stripe.PaymentIntent.create", return_value=mock_intent) as mock_create:
        client.get("/checkout")

        assert mock_create.called, "PaymentIntent.create was not called"
        call_kwargs = mock_create.call_args.kwargs
        metadata = call_kwargs.get("metadata", {})
        assert "user_id" in metadata, "user_id must be in PaymentIntent metadata"
        assert metadata["user_id"] == str(logged_in_user.id)
