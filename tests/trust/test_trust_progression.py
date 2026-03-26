"""Tests for trust stage progression evaluation.

Covers:
- New user starts at STRANGER
- Progression after meeting all thresholds
- Partial threshold satisfaction (no advancement)
- No regression (trust never goes backward)
- Multiple simultaneous signals handled
- ALLIANCE is the terminal stage
- Custom rules override defaults
"""

from datetime import UTC, datetime, timedelta

from src.trust.ladder import TrustProfile, TrustStage
from src.trust.progression import DEFAULT_PROGRESSION_RULES, evaluate_trust_progression

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_BASE_TIME = datetime(2026, 3, 25, 0, 0, 0, tzinfo=UTC)


def _profile(
    stage: TrustStage,
    stage_entered_at: datetime,
    total_interactions: int = 0,
    positive_reactions: int = 0,
    progression_rules: dict | None = None,
) -> TrustProfile:
    return TrustProfile(
        user_id="user-123",
        entity_id="entity-456",
        recipient_id="user-123",
        current_stage=stage,
        stage_entered_at=stage_entered_at,
        total_interactions=total_interactions,
        positive_reactions=positive_reactions,
        progression_rules=progression_rules or {},
    )


# ---------------------------------------------------------------------------
# New user behaviour
# ---------------------------------------------------------------------------


def test_new_user_stays_at_stranger_within_24h() -> None:
    """A brand-new user with no interactions stays STRANGER inside 24 hours."""
    profile = _profile(
        stage=TrustStage.STRANGER,
        stage_entered_at=_BASE_TIME,
        total_interactions=0,
    )
    result = evaluate_trust_progression(profile, current_time=_BASE_TIME + timedelta(hours=12))
    assert result == TrustStage.STRANGER


def test_new_user_stays_at_stranger_without_enough_interactions() -> None:
    """Time threshold met but interactions below minimum — no advance."""
    profile = _profile(
        stage=TrustStage.STRANGER,
        stage_entered_at=_BASE_TIME,
        total_interactions=2,  # Need 3
    )
    result = evaluate_trust_progression(profile, current_time=_BASE_TIME + timedelta(hours=25))
    assert result == TrustStage.STRANGER


# ---------------------------------------------------------------------------
# STRANGER → INITIAL
# ---------------------------------------------------------------------------


def test_progresses_stranger_to_initial_when_thresholds_met() -> None:
    """Advances to INITIAL after 24h + 3 interactions."""
    profile = _profile(
        stage=TrustStage.STRANGER,
        stage_entered_at=_BASE_TIME,
        total_interactions=3,
    )
    result = evaluate_trust_progression(profile, current_time=_BASE_TIME + timedelta(hours=25))
    assert result == TrustStage.INITIAL


def test_stranger_stays_if_only_time_met() -> None:
    """24h elapsed but zero interactions — stays STRANGER."""
    profile = _profile(
        stage=TrustStage.STRANGER,
        stage_entered_at=_BASE_TIME,
        total_interactions=0,
    )
    result = evaluate_trust_progression(profile, current_time=_BASE_TIME + timedelta(hours=25))
    assert result == TrustStage.STRANGER


def test_stranger_stays_if_only_interactions_met() -> None:
    """3 interactions but only 1 hour elapsed — stays STRANGER."""
    profile = _profile(
        stage=TrustStage.STRANGER,
        stage_entered_at=_BASE_TIME,
        total_interactions=5,
    )
    result = evaluate_trust_progression(profile, current_time=_BASE_TIME + timedelta(hours=1))
    assert result == TrustStage.STRANGER


# ---------------------------------------------------------------------------
# INITIAL → WORKING
# ---------------------------------------------------------------------------


def test_progresses_initial_to_working_when_thresholds_met() -> None:
    """Advances to WORKING after 7 days + 10 interactions."""
    profile = _profile(
        stage=TrustStage.INITIAL,
        stage_entered_at=_BASE_TIME,
        total_interactions=10,
    )
    result = evaluate_trust_progression(profile, current_time=_BASE_TIME + timedelta(days=8))
    assert result == TrustStage.WORKING


def test_initial_stays_if_only_days_met() -> None:
    """7+ days but only 5 interactions — stays INITIAL."""
    profile = _profile(
        stage=TrustStage.INITIAL,
        stage_entered_at=_BASE_TIME,
        total_interactions=5,
    )
    result = evaluate_trust_progression(profile, current_time=_BASE_TIME + timedelta(days=8))
    assert result == TrustStage.INITIAL


# ---------------------------------------------------------------------------
# WORKING → DEEP
# ---------------------------------------------------------------------------


def test_progresses_working_to_deep_when_thresholds_met() -> None:
    """Advances to DEEP after 28 days + 30 interactions."""
    profile = _profile(
        stage=TrustStage.WORKING,
        stage_entered_at=_BASE_TIME,
        total_interactions=30,
    )
    result = evaluate_trust_progression(profile, current_time=_BASE_TIME + timedelta(days=29))
    assert result == TrustStage.DEEP


def test_working_stays_if_days_not_met() -> None:
    """30 interactions but only 10 days — stays WORKING."""
    profile = _profile(
        stage=TrustStage.WORKING,
        stage_entered_at=_BASE_TIME,
        total_interactions=30,
    )
    result = evaluate_trust_progression(profile, current_time=_BASE_TIME + timedelta(days=10))
    assert result == TrustStage.WORKING


# ---------------------------------------------------------------------------
# DEEP → ALLIANCE
# ---------------------------------------------------------------------------


def test_progresses_deep_to_alliance_when_thresholds_met() -> None:
    """Advances to ALLIANCE after 90 days + 60 interactions."""
    profile = _profile(
        stage=TrustStage.DEEP,
        stage_entered_at=_BASE_TIME,
        total_interactions=60,
    )
    result = evaluate_trust_progression(profile, current_time=_BASE_TIME + timedelta(days=91))
    assert result == TrustStage.ALLIANCE


# ---------------------------------------------------------------------------
# No regression
# ---------------------------------------------------------------------------


def test_trust_never_regresses_from_alliance() -> None:
    """ALLIANCE is the terminal stage — stays there regardless of counters."""
    profile = _profile(
        stage=TrustStage.ALLIANCE,
        stage_entered_at=_BASE_TIME,
        total_interactions=0,  # Even with no interactions, stays at ALLIANCE
    )
    result = evaluate_trust_progression(profile, current_time=_BASE_TIME)
    assert result == TrustStage.ALLIANCE


def test_trust_never_regresses_existing_stage() -> None:
    """A WORKING profile never returns INITIAL or STRANGER."""
    profile = _profile(
        stage=TrustStage.WORKING,
        stage_entered_at=_BASE_TIME,
        total_interactions=1,  # Not enough to advance — but must not regress
    )
    result = evaluate_trust_progression(profile, current_time=_BASE_TIME + timedelta(days=1))
    assert result == TrustStage.WORKING


def test_trust_only_advances_one_stage_at_a_time() -> None:
    """Even with extreme interaction counts, only advances one stage per call."""
    profile = _profile(
        stage=TrustStage.STRANGER,
        stage_entered_at=_BASE_TIME,
        total_interactions=999,  # Way beyond any threshold
    )
    result = evaluate_trust_progression(profile, current_time=_BASE_TIME + timedelta(hours=25))
    assert result == TrustStage.INITIAL  # Not WORKING or DEEP


# ---------------------------------------------------------------------------
# Multiple simultaneous signals handled
# ---------------------------------------------------------------------------


def test_many_interactions_dont_break_evaluation() -> None:
    """High interaction counts are handled cleanly without errors."""
    profile = _profile(
        stage=TrustStage.INITIAL,
        stage_entered_at=_BASE_TIME,
        total_interactions=500,
        positive_reactions=200,
    )
    result = evaluate_trust_progression(profile, current_time=_BASE_TIME + timedelta(days=8))
    assert result == TrustStage.WORKING


def test_evaluation_with_all_counters_populated() -> None:
    """All TrustProfile counters present — evaluation is stable."""
    profile = TrustProfile(
        user_id="user-123",
        entity_id="entity-456",
        recipient_id="user-123",
        current_stage=TrustStage.INITIAL,
        stage_entered_at=_BASE_TIME,
        total_interactions=15,
        positive_reactions=10,
        negative_reactions=2,
        longest_silence_days=3,
        personality_adjustments=1,
    )
    result = evaluate_trust_progression(profile, current_time=_BASE_TIME + timedelta(days=8))
    assert result == TrustStage.WORKING


# ---------------------------------------------------------------------------
# Custom rules override defaults
# ---------------------------------------------------------------------------


def test_custom_progression_rules_override_defaults() -> None:
    """Custom rules injected via profile.progression_rules take precedence."""
    strict_rules = {
        "stranger_to_initial": {
            "min_hours_in_stage": 48,  # stricter than default 24h
            "min_interactions": 10,    # stricter than default 3
        },
    }
    profile = _profile(
        stage=TrustStage.STRANGER,
        stage_entered_at=_BASE_TIME,
        total_interactions=3,  # meets default but not custom
        progression_rules=strict_rules,
    )
    result = evaluate_trust_progression(profile, current_time=_BASE_TIME + timedelta(hours=25))
    assert result == TrustStage.STRANGER  # custom rule not yet met


def test_custom_relaxed_rules_can_accelerate_progression() -> None:
    """Relaxed custom rules allow faster progression."""
    relaxed_rules = {
        "stranger_to_initial": {
            "min_hours_in_stage": 1,
            "min_interactions": 1,
        },
    }
    profile = _profile(
        stage=TrustStage.STRANGER,
        stage_entered_at=_BASE_TIME,
        total_interactions=1,
        progression_rules=relaxed_rules,
    )
    result = evaluate_trust_progression(profile, current_time=_BASE_TIME + timedelta(hours=2))
    assert result == TrustStage.INITIAL


# ---------------------------------------------------------------------------
# Default time (no explicit current_time)
# ---------------------------------------------------------------------------


def test_evaluate_uses_current_time_when_not_provided() -> None:
    """evaluate_trust_progression() works without explicit current_time."""
    # Stage entered far in the past — should have progressed long ago
    profile = _profile(
        stage=TrustStage.STRANGER,
        stage_entered_at=datetime(2020, 1, 1, tzinfo=UTC),
        total_interactions=100,
    )
    result = evaluate_trust_progression(profile)
    assert result == TrustStage.INITIAL


# ---------------------------------------------------------------------------
# DEFAULT_PROGRESSION_RULES structure
# ---------------------------------------------------------------------------


def test_default_rules_cover_all_transitions() -> None:
    """Default rules define thresholds for all four stage transitions."""
    assert "stranger_to_initial" in DEFAULT_PROGRESSION_RULES
    assert "initial_to_working" in DEFAULT_PROGRESSION_RULES
    assert "working_to_deep" in DEFAULT_PROGRESSION_RULES
    assert "deep_to_alliance" in DEFAULT_PROGRESSION_RULES
