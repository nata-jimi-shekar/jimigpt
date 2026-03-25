"""Tests for deliver_with_retry — TDD: tests written before implementation."""

from datetime import UTC, datetime

import pytest

from src.delivery.models import DeliveryChannel, DeliveryRequest, DeliveryResult
from src.delivery.sms import MAX_ATTEMPTS, RETRY_DELAYS, deliver_with_retry
from src.messaging.generator import GeneratedMessage
from src.messaging.models import MessageIntent
from src.personality.models import ToneSpectrum

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _tone() -> ToneSpectrum:
    return ToneSpectrum(
        warmth=0.7, humor=0.4, directness=0.5,
        gravity=0.2, energy=0.6, vulnerability=0.3,
    )


def _msg() -> GeneratedMessage:
    return GeneratedMessage(
        message_id="msg-001",
        entity_id="entity-abc",
        content="Hey! Thinking of you 🐾",
        generated_at=datetime.now(tz=UTC),
        model_used="claude-sonnet-4-6",
        prompt_tokens=50,
        completion_tokens=20,
        message_category="greeting",
        intended_intent=MessageIntent.AFFIRM,
        intended_tone=_tone(),
        character_count=22,
    )


def _request() -> DeliveryRequest:
    return DeliveryRequest(
        message=_msg(),
        channel=DeliveryChannel.SMS,
        recipient_phone="+15551234567",
        scheduled_at=datetime.now(tz=UTC),
        timezone="UTC",
        recipient_id="user-001",
    )


def _success(sid: str = "SM123") -> DeliveryResult:
    return DeliveryResult(
        success=True,
        channel=DeliveryChannel.SMS,
        delivered_at=datetime.now(tz=UTC),
        external_id=sid,
    )


def _failure(error: str = "Twilio error") -> DeliveryResult:
    return DeliveryResult(
        success=False,
        channel=DeliveryChannel.SMS,
        error=error,
    )


# No-op sleep so tests don't actually wait
_NO_SLEEP = lambda _: None  # noqa: E731


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------


def test_max_attempts_is_three() -> None:
    assert MAX_ATTEMPTS == 3


def test_retry_delays_has_three_values() -> None:
    """Three backoff durations defined (1min, 5min, 15min)."""
    assert len(RETRY_DELAYS) == 3
    assert RETRY_DELAYS[0] == 60
    assert RETRY_DELAYS[1] == 300
    assert RETRY_DELAYS[2] == 900


# ---------------------------------------------------------------------------
# First attempt succeeds — no retry
# ---------------------------------------------------------------------------


def test_first_attempt_success_no_retry() -> None:
    """When first attempt succeeds, send_fn called exactly once."""
    send_fn = lambda to, body: _success("SM_first")  # noqa: E731

    result = deliver_with_retry(_request(), _send_fn=send_fn, _sleep_fn=_NO_SLEEP)

    assert result.success is True
    assert result.external_id == "SM_first"
    assert result.attempts == 1
    assert result.last_attempt_at is not None


def test_first_attempt_success_returns_delivery_result() -> None:
    result = deliver_with_retry(
        _request(),
        _send_fn=lambda to, body: _success(),
        _sleep_fn=_NO_SLEEP,
    )
    assert isinstance(result, DeliveryResult)


# ---------------------------------------------------------------------------
# First attempt fails, second succeeds — 1 retry
# ---------------------------------------------------------------------------


def test_first_fail_second_success_two_attempts() -> None:
    """send_fn called twice; second attempt succeeds."""
    call_count = 0

    def send_fn(to: str, body: str) -> DeliveryResult:
        nonlocal call_count
        call_count += 1
        return _success("SM_second") if call_count == 2 else _failure()

    result = deliver_with_retry(_request(), _send_fn=send_fn, _sleep_fn=_NO_SLEEP)

    assert result.success is True
    assert result.external_id == "SM_second"
    assert result.attempts == 2
    assert call_count == 2


def test_first_fail_second_success_sleeps_once() -> None:
    """One sleep between attempt 1 and attempt 2."""
    sleep_calls: list[float] = []
    call_count = 0

    def send_fn(to: str, body: str) -> DeliveryResult:
        nonlocal call_count
        call_count += 1
        return _success() if call_count == 2 else _failure()

    deliver_with_retry(
        _request(),
        _send_fn=send_fn,
        _sleep_fn=lambda s: sleep_calls.append(s),
    )

    assert len(sleep_calls) == 1
    assert sleep_calls[0] == RETRY_DELAYS[0]


# ---------------------------------------------------------------------------
# Second attempt fails, third succeeds — 2 retries
# ---------------------------------------------------------------------------


def test_first_two_fail_third_success() -> None:
    """Three total attempts; third succeeds."""
    call_count = 0

    def send_fn(to: str, body: str) -> DeliveryResult:
        nonlocal call_count
        call_count += 1
        return _success("SM_third") if call_count == 3 else _failure()

    result = deliver_with_retry(_request(), _send_fn=send_fn, _sleep_fn=_NO_SLEEP)

    assert result.success is True
    assert result.external_id == "SM_third"
    assert result.attempts == 3
    assert call_count == 3


def test_two_failures_sleeps_twice_with_correct_delays() -> None:
    """Two sleeps with delay[0] then delay[1] between the three attempts."""
    sleep_calls: list[float] = []
    call_count = 0

    def send_fn(to: str, body: str) -> DeliveryResult:
        nonlocal call_count
        call_count += 1
        return _success() if call_count == 3 else _failure()

    deliver_with_retry(
        _request(),
        _send_fn=send_fn,
        _sleep_fn=lambda s: sleep_calls.append(s),
    )

    assert sleep_calls == [RETRY_DELAYS[0], RETRY_DELAYS[1]]


# ---------------------------------------------------------------------------
# All 3 attempts fail — permanently failed
# ---------------------------------------------------------------------------


def test_all_attempts_fail_returns_failure() -> None:
    """After 3 failed attempts, result is success=False."""
    result = deliver_with_retry(
        _request(),
        _send_fn=lambda to, body: _failure("network down"),
        _sleep_fn=_NO_SLEEP,
    )

    assert result.success is False
    assert result.error is not None
    assert result.attempts == 3


def test_all_attempts_fail_send_called_three_times() -> None:
    call_count = 0

    def send_fn(to: str, body: str) -> DeliveryResult:
        nonlocal call_count
        call_count += 1
        return _failure()

    deliver_with_retry(_request(), _send_fn=send_fn, _sleep_fn=_NO_SLEEP)

    assert call_count == MAX_ATTEMPTS


def test_all_attempts_fail_error_from_last_attempt() -> None:
    """The error message on the final result comes from the last attempt."""
    attempt_num = 0

    def send_fn(to: str, body: str) -> DeliveryResult:
        nonlocal attempt_num
        attempt_num += 1
        return _failure(f"error on attempt {attempt_num}")

    result = deliver_with_retry(_request(), _send_fn=send_fn, _sleep_fn=_NO_SLEEP)

    assert "attempt 3" in (result.error or "")


def test_all_attempts_fail_no_sleep_after_last() -> None:
    """No sleep after the final (failed) attempt — don't wait for nothing."""
    sleep_count = 0

    deliver_with_retry(
        _request(),
        _send_fn=lambda to, body: _failure(),
        _sleep_fn=lambda s: sleep_count.__class__,  # counts via side effect
    )

    sleep_calls: list[float] = []
    deliver_with_retry(
        _request(),
        _send_fn=lambda to, body: _failure(),
        _sleep_fn=lambda s: sleep_calls.append(s),
    )
    # 3 attempts → 2 sleeps (between 1→2 and 2→3); none after attempt 3
    assert len(sleep_calls) == 2


# ---------------------------------------------------------------------------
# last_attempt_at tracking
# ---------------------------------------------------------------------------


def test_last_attempt_at_is_set_on_success() -> None:
    result = deliver_with_retry(
        _request(),
        _send_fn=lambda to, body: _success(),
        _sleep_fn=_NO_SLEEP,
    )
    assert result.last_attempt_at is not None
    assert result.last_attempt_at.tzinfo is not None


def test_last_attempt_at_is_set_on_failure() -> None:
    result = deliver_with_retry(
        _request(),
        _send_fn=lambda to, body: _failure(),
        _sleep_fn=_NO_SLEEP,
    )
    assert result.last_attempt_at is not None


# ---------------------------------------------------------------------------
# Request without phone number raises immediately (no retry)
# ---------------------------------------------------------------------------


def test_missing_phone_raises_before_retry() -> None:
    """DeliveryRequest without recipient_phone raises ValueError immediately."""
    req = DeliveryRequest(
        message=_msg(),
        channel=DeliveryChannel.SMS,
        recipient_phone=None,
        scheduled_at=datetime.now(tz=UTC),
        timezone="UTC",
        recipient_id="user-001",
    )
    with pytest.raises(ValueError, match="phone"):
        deliver_with_retry(req, _sleep_fn=_NO_SLEEP)
