import pathlib
import stripe


def test_stripe_api_version_is_pinned():
    import app  # noqa: F401 — importing app sets stripe.api_version as a side effect
    assert stripe.api_version == "2026-03-25.dahlia", (
        f"Expected Stripe API version '2026-03-25.dahlia', got '{stripe.api_version}'"
    )


def test_no_legacy_stripe_error_namespace():
    source = pathlib.Path("app.py").read_text()
    assert "stripe.error.StripeError" not in source, (
        "Found legacy stripe.error.StripeError — use stripe.StripeError instead"
    )
