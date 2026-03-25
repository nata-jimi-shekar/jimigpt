"""Tests for Twilio webhook handler — TDD: tests written before implementation."""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from src.api.webhooks import (
    TERMINAL_FAILURE_STATUSES,
    TERMINAL_SUCCESS_STATUSES,
    get_delivery_channel,
    get_delivery_status,
    reset_status_store,
    verify_twilio_signature,
)
from src.main import app

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _clear_status_store() -> None:
    """Reset in-memory status store between tests."""
    reset_status_store()


@pytest.fixture()
def client_no_sig() -> TestClient:
    """TestClient with signature verification bypassed."""
    app.dependency_overrides[verify_twilio_signature] = lambda: None
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture()
def client_with_sig() -> TestClient:
    """TestClient with real (unoverridden) signature verification."""
    app.dependency_overrides.clear()
    return TestClient(app)


# ---------------------------------------------------------------------------
# Status constants
# ---------------------------------------------------------------------------


def test_terminal_success_statuses_includes_delivered() -> None:
    assert "delivered" in TERMINAL_SUCCESS_STATUSES


def test_terminal_failure_statuses_includes_failed_and_undelivered() -> None:
    assert "failed" in TERMINAL_FAILURE_STATUSES
    assert "undelivered" in TERMINAL_FAILURE_STATUSES


# ---------------------------------------------------------------------------
# Successful status updates
# ---------------------------------------------------------------------------


def test_webhook_delivered_status_updates_store(client_no_sig: TestClient) -> None:
    """Twilio 'delivered' callback records the status."""
    response = client_no_sig.post(
        "/api/v1/webhooks/twilio",
        data={
            "MessageSid": "SM_abc123",
            "MessageStatus": "delivered",
            "To": "+15551234567",
            "From": "+15550001111",
            "AccountSid": "ACtest",
        },
    )

    assert response.status_code == 200
    assert get_delivery_status("SM_abc123") == "delivered"


def test_webhook_failed_status_updates_store(client_no_sig: TestClient) -> None:
    response = client_no_sig.post(
        "/api/v1/webhooks/twilio",
        data={
            "MessageSid": "SM_fail001",
            "MessageStatus": "failed",
            "To": "+15551234567",
            "From": "+15550001111",
            "AccountSid": "ACtest",
        },
    )

    assert response.status_code == 200
    assert get_delivery_status("SM_fail001") == "failed"


def test_webhook_undelivered_status_updates_store(client_no_sig: TestClient) -> None:
    response = client_no_sig.post(
        "/api/v1/webhooks/twilio",
        data={
            "MessageSid": "SM_undel",
            "MessageStatus": "undelivered",
            "To": "+15551234567",
            "From": "+15550001111",
            "AccountSid": "ACtest",
        },
    )

    assert response.status_code == 200
    assert get_delivery_status("SM_undel") == "undelivered"


def test_webhook_returns_ok_on_success(client_no_sig: TestClient) -> None:
    response = client_no_sig.post(
        "/api/v1/webhooks/twilio",
        data={"MessageSid": "SM_ok", "MessageStatus": "delivered"},
    )
    assert response.json()["status"] == "ok"


def test_webhook_intermediate_status_acknowledged(client_no_sig: TestClient) -> None:
    """Non-terminal statuses (sent, queued) are acknowledged but not stored as final."""
    response = client_no_sig.post(
        "/api/v1/webhooks/twilio",
        data={"MessageSid": "SM_sent", "MessageStatus": "sent"},
    )
    assert response.status_code == 200
    # Status is recorded for traceability even if non-terminal
    assert get_delivery_status("SM_sent") == "sent"


# ---------------------------------------------------------------------------
# Unknown / missing message SID
# ---------------------------------------------------------------------------


def test_webhook_unknown_message_sid_handled_gracefully(
    client_no_sig: TestClient,
) -> None:
    """Unknown SID returns 200 — Twilio must always get a 2xx or it retries."""
    response = client_no_sig.post(
        "/api/v1/webhooks/twilio",
        data={"MessageSid": "SM_unknown_999", "MessageStatus": "delivered"},
    )
    assert response.status_code == 200


def test_get_delivery_status_returns_none_for_unknown_sid() -> None:
    assert get_delivery_status("SM_does_not_exist") is None


def test_webhook_status_overwritten_by_later_callback(
    client_no_sig: TestClient,
) -> None:
    """Twilio can send multiple callbacks; last one wins."""
    client_no_sig.post(
        "/api/v1/webhooks/twilio",
        data={"MessageSid": "SM_multi", "MessageStatus": "sent"},
    )
    client_no_sig.post(
        "/api/v1/webhooks/twilio",
        data={"MessageSid": "SM_multi", "MessageStatus": "delivered"},
    )
    assert get_delivery_status("SM_multi") == "delivered"


# ---------------------------------------------------------------------------
# Signature validation
# ---------------------------------------------------------------------------


def test_invalid_signature_returns_403(client_with_sig: TestClient) -> None:
    """Requests with an invalid X-Twilio-Signature are rejected with 403."""
    with patch(
        "src.api.webhooks.RequestValidator.validate", return_value=False
    ):
        response = client_with_sig.post(
            "/api/v1/webhooks/twilio",
            data={"MessageSid": "SM_bad", "MessageStatus": "delivered"},
            headers={"X-Twilio-Signature": "bad-signature"},
        )

    assert response.status_code == 403


def test_missing_signature_header_returns_422(client_with_sig: TestClient) -> None:
    """Requests missing X-Twilio-Signature header return 422 (validation error)."""
    with patch(
        "src.api.webhooks.RequestValidator.validate", return_value=False
    ):
        response = client_with_sig.post(
            "/api/v1/webhooks/twilio",
            data={"MessageSid": "SM_nosig", "MessageStatus": "delivered"},
            # No X-Twilio-Signature header
        )

    assert response.status_code in (422, 403)


def test_valid_signature_allows_request(client_with_sig: TestClient) -> None:
    """Requests with a valid signature are processed normally."""
    with patch(
        "src.api.webhooks.RequestValidator.validate", return_value=True
    ):
        response = client_with_sig.post(
            "/api/v1/webhooks/twilio",
            data={"MessageSid": "SM_valid", "MessageStatus": "delivered"},
            headers={"X-Twilio-Signature": "valid-sig"},
        )

    assert response.status_code == 200
    assert get_delivery_status("SM_valid") == "delivered"


# ---------------------------------------------------------------------------
# Channel detection from From field
# ---------------------------------------------------------------------------


def test_webhook_plain_from_field_detects_sms_channel(
    client_no_sig: TestClient,
) -> None:
    """Plain phone number in From field → channel recorded as 'sms'."""
    client_no_sig.post(
        "/api/v1/webhooks/twilio",
        data={
            "MessageSid": "SM_sms_ch",
            "MessageStatus": "delivered",
            "From": "+15550001111",
        },
    )
    assert get_delivery_channel("SM_sms_ch") == "sms"


def test_webhook_whatsapp_from_field_detects_whatsapp_channel(
    client_no_sig: TestClient,
) -> None:
    """'whatsapp:' prefix in From field → channel recorded as 'whatsapp'."""
    client_no_sig.post(
        "/api/v1/webhooks/twilio",
        data={
            "MessageSid": "WA_ch_001",
            "MessageStatus": "delivered",
            "From": "whatsapp:+14155238886",
        },
    )
    assert get_delivery_channel("WA_ch_001") == "whatsapp"


def test_webhook_no_from_field_defaults_to_sms(client_no_sig: TestClient) -> None:
    """Missing From field defaults channel to 'sms'."""
    client_no_sig.post(
        "/api/v1/webhooks/twilio",
        data={"MessageSid": "SM_nofrom", "MessageStatus": "delivered"},
    )
    assert get_delivery_channel("SM_nofrom") == "sms"


def test_get_delivery_channel_returns_none_for_unknown_sid() -> None:
    assert get_delivery_channel("SM_does_not_exist") is None


# ---------------------------------------------------------------------------
# WhatsApp status updates
# ---------------------------------------------------------------------------


def test_webhook_whatsapp_delivered_updates_status(
    client_no_sig: TestClient,
) -> None:
    """WhatsApp 'delivered' callback records status correctly."""
    response = client_no_sig.post(
        "/api/v1/webhooks/twilio",
        data={
            "MessageSid": "WA_del_001",
            "MessageStatus": "delivered",
            "To": "whatsapp:+573001234567",
            "From": "whatsapp:+14155238886",
            "AccountSid": "ACtest",
        },
    )
    assert response.status_code == 200
    assert get_delivery_status("WA_del_001") == "delivered"
    assert get_delivery_channel("WA_del_001") == "whatsapp"


def test_webhook_whatsapp_failed_updates_status(client_no_sig: TestClient) -> None:
    """WhatsApp 'failed' callback records status and channel correctly."""
    response = client_no_sig.post(
        "/api/v1/webhooks/twilio",
        data={
            "MessageSid": "WA_fail_001",
            "MessageStatus": "failed",
            "From": "whatsapp:+14155238886",
        },
    )
    assert response.status_code == 200
    assert get_delivery_status("WA_fail_001") == "failed"
    assert get_delivery_channel("WA_fail_001") == "whatsapp"


def test_webhook_response_includes_channel(client_no_sig: TestClient) -> None:
    """Response body includes the detected channel."""
    response = client_no_sig.post(
        "/api/v1/webhooks/twilio",
        data={
            "MessageSid": "WA_resp",
            "MessageStatus": "delivered",
            "From": "whatsapp:+14155238886",
        },
    )
    body = response.json()
    assert body["channel"] == "whatsapp"


def test_webhook_sms_response_includes_sms_channel(
    client_no_sig: TestClient,
) -> None:
    response = client_no_sig.post(
        "/api/v1/webhooks/twilio",
        data={
            "MessageSid": "SM_resp",
            "MessageStatus": "delivered",
            "From": "+15550001111",
        },
    )
    assert response.json()["channel"] == "sms"
