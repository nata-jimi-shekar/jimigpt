"""Trust stage progression evaluation.

Evaluates whether a trust relationship should advance to the next stage
based on time elapsed and interaction counts.

The engine is entity-agnostic: progression rules are injected via
TrustProfile.progression_rules. DEFAULT_PROGRESSION_RULES provides
the JimiGPT baseline; other products supply their own rule dicts.

Rules:
  STRANGER  → INITIAL  : 24 hours  + 3 interactions
  INITIAL   → WORKING  : 7 days    + 10 interactions
  WORKING   → DEEP     : 28 days   + 30 interactions
  DEEP      → ALLIANCE : 90 days   + 60 interactions

Trust never regresses. Only one stage advance per call.
"""

from datetime import UTC, datetime
from typing import Any

from src.trust.ladder import TrustProfile, TrustStage

# ---------------------------------------------------------------------------
# Default progression rules (JimiGPT baseline)
# ---------------------------------------------------------------------------

DEFAULT_PROGRESSION_RULES: dict[str, dict[str, int]] = {
    "stranger_to_initial": {
        "min_hours_in_stage": 24,
        "min_interactions": 3,
    },
    "initial_to_working": {
        "min_days_in_stage": 7,
        "min_interactions": 10,
    },
    "working_to_deep": {
        "min_days_in_stage": 28,
        "min_interactions": 30,
    },
    "deep_to_alliance": {
        "min_days_in_stage": 90,
        "min_interactions": 60,
    },
}

# Ordered list of stages — defines legal advancement direction.
_STAGE_ORDER: list[TrustStage] = [
    TrustStage.STRANGER,
    TrustStage.INITIAL,
    TrustStage.WORKING,
    TrustStage.DEEP,
    TrustStage.ALLIANCE,
]

# Maps each stage to the rule key that governs its outgoing transition.
_TRANSITION_KEY: dict[TrustStage, str] = {
    TrustStage.STRANGER: "stranger_to_initial",
    TrustStage.INITIAL: "initial_to_working",
    TrustStage.WORKING: "working_to_deep",
    TrustStage.DEEP: "deep_to_alliance",
}


def _time_threshold_met(
    rule: dict[str, Any],
    seconds_in_stage: float,
) -> bool:
    if "min_hours_in_stage" in rule:
        return seconds_in_stage >= float(rule["min_hours_in_stage"]) * 3600
    if "min_days_in_stage" in rule:
        return seconds_in_stage >= float(rule["min_days_in_stage"]) * 86400
    return True


def evaluate_trust_progression(
    profile: TrustProfile,
    current_time: datetime | None = None,
) -> TrustStage:
    """Return the trust stage the profile should be in after applying progression rules.

    Returns the current stage if advancement conditions are not met.
    Trust never regresses — the return value is always >= profile.current_stage.
    Advances at most one stage per call.

    Args:
        profile: Current trust profile including interaction counters.
        current_time: Evaluation timestamp. Defaults to now (UTC).
    """
    if current_time is None:
        current_time = datetime.now(UTC)

    current_stage = profile.current_stage

    if current_stage == TrustStage.ALLIANCE:
        return TrustStage.ALLIANCE

    transition_key = _TRANSITION_KEY.get(current_stage)
    if transition_key is None:
        return current_stage

    rules = profile.progression_rules if profile.progression_rules else DEFAULT_PROGRESSION_RULES
    rule = rules.get(transition_key)
    if rule is None:
        return current_stage

    seconds_in_stage = (current_time - profile.stage_entered_at).total_seconds()

    if not _time_threshold_met(rule, seconds_in_stage):
        return current_stage

    if profile.total_interactions < rule.get("min_interactions", 0):
        return current_stage

    # All conditions met — advance exactly one stage.
    next_idx = _STAGE_ORDER.index(current_stage) + 1
    return _STAGE_ORDER[next_idx]
