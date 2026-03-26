"""Escalation detection for JimiGPT.

Evaluates whether a user message requires escalation beyond normal AI
companion messaging. JimiGPT primarily operates at Levels 0-1.
Level 3+ is rare and pauses pet messaging in favour of crisis resources.

Safety principle: No entity speaks without primary owner consent.
This module enforces that boundary when user distress is detected —
the entity steps aside and real support is surfaced instead.

Detection strategy: keyword-based scanning against product_rules.
Rules are product-configurable; DEFAULT_JIMIGPT_ESCALATION_RULES
provides the JimiGPT baseline. Highest-priority match wins.

Foundation field: life_contexts (list[str] | None) is accepted on
assess_escalation() for Phase 2 life-event-aware sensitivity tuning
(e.g. pet_sick + distress language = higher urgency). In Phase 1
this parameter is accepted but has no effect on output.
"""

from enum import IntEnum
from typing import Any

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class EscalationLevel(IntEnum):
    NORMAL = 0
    ATTENTION = 1
    CONCERN = 2
    URGENT = 3
    EMERGENCY = 4


class EscalationSignal(BaseModel):
    """Result of escalation assessment for a single user interaction."""

    level: EscalationLevel
    signals_detected: list[str]
    recommended_action: str
    resources: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Default JimiGPT escalation rules
# ---------------------------------------------------------------------------

DEFAULT_JIMIGPT_ESCALATION_RULES: dict[str, Any] = {
    # Level 1 — pet health questions: deflect to vet, stay in character.
    # "{name} tilts head. I don't know about that stuff.
    #  Maybe ask the person in the white coat?"
    "vet_deflection": {
        "keywords": [
            "vet",
            "veterinarian",
            "sick",
            "symptoms",
            "diagnosis",
            "medication",
            "medicine",
            "treatment",
            "lethargic",
            "not eating",
            "vomit",
            "diarrhea",
            "limp",
            "infection",
        ],
        "level": EscalationLevel.ATTENTION,
        "recommended_action": "deflect_to_vet",
        "resources": [],
    },
    # Level 2 — personal distress: gentle support nudge, no crisis resources.
    "distress": {
        "keywords": [
            "depressed",
            "depression",
            "anxious",
            "anxiety",
            "struggling",
            "overwhelmed",
            "can't cope",
            "cant cope",
            "falling apart",
            "so stressed",
            "so sad",
            "hopeless",
            "worthless",
        ],
        "level": EscalationLevel.CONCERN,
        "recommended_action": "suggest_human_support",
        "resources": [],
    },
    # Level 3 — crisis language: pause pet messaging, surface crisis resources.
    "crisis": {
        "keywords": [
            "kill myself",
            "suicide",
            "suicidal",
            "end it all",
            "ending it all",
            "don't want to be here",
            "dont want to be here",
            "hurt myself",
            "harm myself",
            "want to die",
            "no reason to live",
        ],
        "level": EscalationLevel.URGENT,
        "recommended_action": "provide_crisis_resources",
        "resources": [
            "988 Suicide & Crisis Lifeline: call or text 988 (US)",
            "Crisis Text Line: text HOME to 741741",
        ],
    },
}

# Rule evaluation order: highest severity first so the first match is the
# highest applicable level.
_RULE_PRIORITY: list[str] = ["crisis", "distress", "vet_deflection"]

_NORMAL_SIGNAL = EscalationSignal(
    level=EscalationLevel.NORMAL,
    signals_detected=[],
    recommended_action="none",
    resources=[],
)

# ---------------------------------------------------------------------------
# Assessment
# ---------------------------------------------------------------------------


def assess_escalation(
    user_message: str | None,
    interaction_history: list[dict[str, Any]],
    product_rules: dict[str, Any],
    life_contexts: list[str] | None = None,  # Foundation: Phase 2 life-event sensitivity
) -> EscalationSignal:
    """Evaluate whether a user message requires escalation.

    Scans user_message against product_rules keywords. Returns the
    highest-priority match, or Level 0 (NORMAL) if no match is found.

    Rules are evaluated in severity order (crisis → distress → vet_deflection)
    so that the most important signal is always surfaced.

    Args:
        user_message: The user's reply or inbound message. None/empty → NORMAL.
        interaction_history: Recent interaction records (reserved for future
            pattern-based detection; not used in Phase 1 keyword scan).
        product_rules: Dict of escalation rule definitions. Each rule has:
            keywords (list[str]), level (EscalationLevel), recommended_action
            (str), resources (list[str]).
        life_contexts: Foundation field — Phase 2 life-event aware sensitivity.
            Accepted and ignored in Phase 1. Pass None (default) in production.

    Returns:
        EscalationSignal with the highest matched level, or NORMAL.
    """
    if not user_message:
        return _NORMAL_SIGNAL

    lower_message = user_message.lower()

    # Evaluate rules in priority order; return on first (highest-level) match.
    for rule_key in _RULE_PRIORITY:
        rule = product_rules.get(rule_key)
        if rule is None:
            continue

        matched = [kw for kw in rule["keywords"] if kw.lower() in lower_message]
        if matched:
            return EscalationSignal(
                level=EscalationLevel(rule["level"]),
                signals_detected=matched,
                recommended_action=rule["recommended_action"],
                resources=list(rule.get("resources", [])),
            )

    return _NORMAL_SIGNAL
