from unittest.mock import patch, MagicMock


def test_confirmation_redirects_on_failed_redirect_status(client):
    """redirect_status=failed must redirect to cart without calling Stripe API."""
    with patch("app.stripe.PaymentIntent.retrieve") as mock_retrieve:
        response = client.get(
            "/confirmation?payment_intent=pi_test_123&redirect_status=failed",
            follow_redirects=False,
        )
    assert response.status_code == 302
    assert "/cart" in response.headers["Location"]
    mock_retrieve.assert_not_called()


def test_confirmation_redirects_on_canceled_redirect_status(client):
    """redirect_status=canceled must redirect to cart without calling Stripe API."""
    with patch("app.stripe.PaymentIntent.retrieve") as mock_retrieve:
        response = client.get(
            "/confirmation?payment_intent=pi_test_123&redirect_status=canceled",
            follow_redirects=False,
        )
    assert response.status_code == 302
    assert "/cart" in response.headers["Location"]
    mock_retrieve.assert_not_called()


def test_confirmation_proceeds_when_no_redirect_status(client):
    """No redirect_status param (e.g. direct navigation) must proceed to retrieve the intent."""
    mock_intent = MagicMock()
    mock_intent.status = "requires_payment_method"
    with patch("app.stripe.PaymentIntent.retrieve", return_value=mock_intent) as mock_retrieve:
        response = client.get(
            "/confirmation?payment_intent=pi_test_123",
            follow_redirects=False,
        )
    mock_retrieve.assert_called_once()
