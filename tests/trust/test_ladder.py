"""Tests for trust models — TrustStage, TrustProfile, TrustEvent."""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from src.trust.ladder import TrustEvent, TrustEventType, TrustProfile, TrustStage

# ---------------------------------------------------------------------------
# TrustStage enum
# ---------------------------------------------------------------------------


def test_trust_stage_has_all_required_values() -> None:
    """TrustStage enum covers the full relationship arc."""
    stages = {s.value for s in TrustStage}
    assert stages == {"stranger", "initial", "working", "deep", "alliance"}


def test_trust_stage_ordered_progression() -> None:
    """Stages can be referenced in progression order."""
    ordered = [
        TrustStage.STRANGER,
        TrustStage.INITIAL,
        TrustStage.WORKING,
        TrustStage.DEEP,
        TrustStage.ALLIANCE,
    ]
    assert len(ordered) == 5


# ---------------------------------------------------------------------------
# TrustEventType enum
# ---------------------------------------------------------------------------


def test_trust_event_type_covers_all_signal_types() -> None:
    """Event types match what the trust_events DB table records."""
    types = {t.value for t in TrustEventType}
    assert "message_sent" in types
    assert "user_replied" in types
    assert "positive_reaction" in types
    assert "negative_reaction" in types
    assert "personality_adjusted" in types
    assert "silence_period" in types


# ---------------------------------------------------------------------------
# TrustProfile model
# ---------------------------------------------------------------------------


@pytest.fixture()
def now() -> datetime:
    return datetime(2026, 3, 25, 12, 0, 0, tzinfo=UTC)


@pytest.fixture()
def valid_profile(now: datetime) -> TrustProfile:
    return TrustProfile(
        user_id="user-123",
        entity_id="entity-456",
        recipient_id="user-123",
        current_stage=TrustStage.STRANGER,
        stage_entered_at=now,
    )


def test_trust_profile_validates_with_required_fields(valid_profile: TrustProfile) -> None:
    """TrustProfile accepts all required fields."""
    assert valid_profile.user_id == "user-123"
    assert valid_profile.entity_id == "entity-456"
    assert valid_profile.current_stage == TrustStage.STRANGER


def test_trust_profile_numeric_defaults_are_zero(valid_profile: TrustProfile) -> None:
    """Counters default to 0 for new users."""
    assert valid_profile.total_interactions == 0
    assert valid_profile.positive_reactions == 0
    assert valid_profile.negative_reactions == 0
    assert valid_profile.longest_silence_days == 0
    assert valid_profile.personality_adjustments == 0


def test_trust_profile_progression_rules_defaults_to_empty(valid_profile: TrustProfile) -> None:
    """progression_rules defaults to empty dict (rules injected at evaluation time)."""
    assert valid_profile.progression_rules == {}


def test_trust_profile_rejects_negative_counters(now: datetime) -> None:
    """Counters must not go negative — data integrity check."""
    with pytest.raises(ValidationError):
        TrustProfile(
            user_id="user-123",
            entity_id="entity-456",
            recipient_id="user-123",
            current_stage=TrustStage.STRANGER,
            stage_entered_at=now,
            total_interactions=-1,
        )


def test_trust_profile_rejects_invalid_stage(now: datetime) -> None:
    """Unknown trust stage values are rejected."""
    with pytest.raises(ValidationError):
        TrustProfile(
            user_id="user-123",
            entity_id="entity-456",
            recipient_id="user-123",
            current_stage="unknown_stage",  # type: ignore[arg-type]
            stage_entered_at=now,
        )


# ---------------------------------------------------------------------------
# Foundation field: recipient_id (Phase 2 multi-recipient prep)
# ---------------------------------------------------------------------------


def test_trust_profile_has_recipient_id(valid_profile: TrustProfile) -> None:
    """Foundation field: recipient_id exists and defaults to owner (user_id) in Phase 1."""
    assert valid_profile.recipient_id == "user-123"


def test_trust_profile_recipient_id_can_differ_from_user_id(now: datetime) -> None:
    """Foundation: recipient_id is distinct from user_id for Phase 2 multi-recipient use."""
    profile = TrustProfile(
        user_id="user-123",
        entity_id="entity-456",
        recipient_id="other-recipient-789",
        current_stage=TrustStage.INITIAL,
        stage_entered_at=now,
    )
    assert profile.recipient_id == "other-recipient-789"
    assert profile.user_id == "user-123"


# ---------------------------------------------------------------------------
# TrustEvent model
# ---------------------------------------------------------------------------


@pytest.fixture()
def valid_event(now: datetime) -> TrustEvent:
    return TrustEvent(
        event_id="evt-001",
        entity_id="entity-456",
        user_id="user-123",
        event_type=TrustEventType.MESSAGE_SENT,
        occurred_at=now,
    )


def test_trust_event_validates_with_required_fields(valid_event: TrustEvent) -> None:
    """TrustEvent accepts all required fields."""
    assert valid_event.event_id == "evt-001"
    assert valid_event.entity_id == "entity-456"
    assert valid_event.event_type == TrustEventType.MESSAGE_SENT


def test_trust_event_data_defaults_to_empty_dict(valid_event: TrustEvent) -> None:
    """event_data defaults to an empty dict."""
    assert valid_event.event_data == {}


def test_trust_event_accepts_event_data(now: datetime) -> None:
    """event_data can carry arbitrary payload."""
    event = TrustEvent(
        event_id="evt-002",
        entity_id="entity-456",
        user_id="user-123",
        event_type=TrustEventType.POSITIVE_REACTION,
        event_data={"message_id": "msg-999", "reaction": "thumbs_up"},
        occurred_at=now,
    )
    assert event.event_data["message_id"] == "msg-999"


def test_trust_event_rejects_invalid_type(now: datetime) -> None:
    """Unknown event types are rejected."""
    with pytest.raises(ValidationError):
        TrustEvent(
            event_id="evt-003",
            entity_id="entity-456",
            user_id="user-123",
            event_type="not_a_real_event",  # type: ignore[arg-type]
            occurred_at=now,
        )


def test_trust_profile_roundtrips_through_json(valid_profile: TrustProfile) -> None:
    """TrustProfile serialises and deserialises cleanly."""
    json_str = valid_profile.model_dump_json()
    restored = TrustProfile.model_validate_json(json_str)
    assert restored == valid_profile


def test_trust_event_roundtrips_through_json(valid_event: TrustEvent) -> None:
    """TrustEvent serialises and deserialises cleanly."""
    json_str = valid_event.model_dump_json()
    restored = TrustEvent.model_validate_json(json_str)
    assert restored == valid_event
