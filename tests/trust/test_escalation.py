"""Tests for escalation detection — assess_escalation().

Covers:
- Normal messages → Level 0
- Pet health / vet questions → Level 1 vet deflection
- Distress language → Level 2 with support suggestion
- Crisis language → Level 3 with resources
- None / empty message → Level 0
- Foundation: life_contexts param defaults to None and is a no-op in Phase 1
- Custom product_rules override defaults
- EscalationLevel and EscalationSignal model validation
"""

from src.trust.escalation import (
    DEFAULT_JIMIGPT_ESCALATION_RULES,
    EscalationLevel,
    EscalationSignal,
    assess_escalation,
)

# ---------------------------------------------------------------------------
# Model validation
# ---------------------------------------------------------------------------


def test_escalation_level_has_all_required_values() -> None:
    levels = {e.value for e in EscalationLevel}
    assert levels == {0, 1, 2, 3, 4}


def test_escalation_signal_model_validates() -> None:
    signal = EscalationSignal(
        level=EscalationLevel.NORMAL,
        signals_detected=[],
        recommended_action="none",
    )
    assert signal.level == EscalationLevel.NORMAL
    assert signal.resources == []


def test_escalation_signal_resources_default_empty() -> None:
    signal = EscalationSignal(
        level=EscalationLevel.CONCERN,
        signals_detected=["sad"],
        recommended_action="suggest_human_support",
    )
    assert signal.resources == []


# ---------------------------------------------------------------------------
# Level 0 — normal messages
# ---------------------------------------------------------------------------


def test_normal_message_returns_level_0() -> None:
    signal = assess_escalation(
        user_message="Haha Jimi knocked over the plant again 😂",
        interaction_history=[],
        product_rules=DEFAULT_JIMIGPT_ESCALATION_RULES,
    )
    assert signal.level == EscalationLevel.NORMAL


def test_none_message_returns_level_0() -> None:
    signal = assess_escalation(
        user_message=None,
        interaction_history=[],
        product_rules=DEFAULT_JIMIGPT_ESCALATION_RULES,
    )
    assert signal.level == EscalationLevel.NORMAL


def test_empty_message_returns_level_0() -> None:
    signal = assess_escalation(
        user_message="",
        interaction_history=[],
        product_rules=DEFAULT_JIMIGPT_ESCALATION_RULES,
    )
    assert signal.level == EscalationLevel.NORMAL


def test_positive_message_returns_level_0() -> None:
    signal = assess_escalation(
        user_message="I love my dog so much, best day ever!",
        interaction_history=[],
        product_rules=DEFAULT_JIMIGPT_ESCALATION_RULES,
    )
    assert signal.level == EscalationLevel.NORMAL
    assert signal.signals_detected == []


# ---------------------------------------------------------------------------
# Level 1 — vet deflection (pet health questions)
# ---------------------------------------------------------------------------


def test_vet_keyword_returns_level_1() -> None:
    signal = assess_escalation(
        user_message="Should I take Jimi to the vet?",
        interaction_history=[],
        product_rules=DEFAULT_JIMIGPT_ESCALATION_RULES,
    )
    assert signal.level == EscalationLevel.ATTENTION


def test_symptoms_keyword_returns_level_1() -> None:
    signal = assess_escalation(
        user_message="My dog has been showing symptoms of something, not eating",
        interaction_history=[],
        product_rules=DEFAULT_JIMIGPT_ESCALATION_RULES,
    )
    assert signal.level == EscalationLevel.ATTENTION


def test_medication_keyword_returns_level_1() -> None:
    signal = assess_escalation(
        user_message="What medication should I give my cat?",
        interaction_history=[],
        product_rules=DEFAULT_JIMIGPT_ESCALATION_RULES,
    )
    assert signal.level == EscalationLevel.ATTENTION


def test_vet_deflection_recommended_action() -> None:
    signal = assess_escalation(
        user_message="Is my dog sick? He's been lethargic all day.",
        interaction_history=[],
        product_rules=DEFAULT_JIMIGPT_ESCALATION_RULES,
    )
    assert signal.recommended_action == "deflect_to_vet"
    assert len(signal.signals_detected) > 0


def test_vet_deflection_is_case_insensitive() -> None:
    signal = assess_escalation(
        user_message="VET APPOINTMENT tomorrow — is this normal?",
        interaction_history=[],
        product_rules=DEFAULT_JIMIGPT_ESCALATION_RULES,
    )
    assert signal.level == EscalationLevel.ATTENTION


# ---------------------------------------------------------------------------
# Level 2 — distress language
# ---------------------------------------------------------------------------


def test_distress_keyword_returns_level_2() -> None:
    signal = assess_escalation(
        user_message="I've been so overwhelmed lately, can't cope with anything",
        interaction_history=[],
        product_rules=DEFAULT_JIMIGPT_ESCALATION_RULES,
    )
    assert signal.level == EscalationLevel.CONCERN


def test_distress_recommended_action_is_support_suggestion() -> None:
    signal = assess_escalation(
        user_message="I feel so depressed and I don't know what to do",
        interaction_history=[],
        product_rules=DEFAULT_JIMIGPT_ESCALATION_RULES,
    )
    assert signal.recommended_action == "suggest_human_support"
    assert len(signal.signals_detected) > 0


def test_distress_signal_has_no_crisis_resources() -> None:
    """Level 2 does not include crisis hotline resources."""
    signal = assess_escalation(
        user_message="I've been struggling so much this week",
        interaction_history=[],
        product_rules=DEFAULT_JIMIGPT_ESCALATION_RULES,
    )
    assert signal.level == EscalationLevel.CONCERN
    assert signal.resources == []


# ---------------------------------------------------------------------------
# Level 3 — crisis language
# ---------------------------------------------------------------------------


def test_crisis_keyword_returns_level_3() -> None:
    signal = assess_escalation(
        user_message="I want to kill myself",
        interaction_history=[],
        product_rules=DEFAULT_JIMIGPT_ESCALATION_RULES,
    )
    assert signal.level == EscalationLevel.URGENT


def test_crisis_recommended_action_is_crisis_resources() -> None:
    signal = assess_escalation(
        user_message="I don't want to be here anymore",
        interaction_history=[],
        product_rules=DEFAULT_JIMIGPT_ESCALATION_RULES,
    )
    assert signal.recommended_action == "provide_crisis_resources"


def test_crisis_signal_includes_resources() -> None:
    """Level 3 includes at least one crisis resource."""
    signal = assess_escalation(
        user_message="thinking about ending it all",
        interaction_history=[],
        product_rules=DEFAULT_JIMIGPT_ESCALATION_RULES,
    )
    assert signal.level == EscalationLevel.URGENT
    assert len(signal.resources) > 0


def test_crisis_is_case_insensitive() -> None:
    signal = assess_escalation(
        user_message="I WANT TO HURT MYSELF",
        interaction_history=[],
        product_rules=DEFAULT_JIMIGPT_ESCALATION_RULES,
    )
    assert signal.level == EscalationLevel.URGENT


# ---------------------------------------------------------------------------
# Priority: crisis > distress > vet (highest level wins)
# ---------------------------------------------------------------------------


def test_crisis_takes_priority_over_distress() -> None:
    """Message with both distress and crisis keywords escalates to crisis level."""
    signal = assess_escalation(
        user_message="I'm so depressed and I want to end it all",
        interaction_history=[],
        product_rules=DEFAULT_JIMIGPT_ESCALATION_RULES,
    )
    assert signal.level == EscalationLevel.URGENT


def test_distress_takes_priority_over_vet() -> None:
    """Message with both vet and distress keywords escalates to distress level."""
    signal = assess_escalation(
        user_message="I'm overwhelmed, Jimi might need the vet",
        interaction_history=[],
        product_rules=DEFAULT_JIMIGPT_ESCALATION_RULES,
    )
    assert signal.level == EscalationLevel.CONCERN


# ---------------------------------------------------------------------------
# Foundation field: life_contexts (Phase 2 prep — no-op in Phase 1)
# ---------------------------------------------------------------------------


def test_assess_escalation_accepts_life_contexts_none() -> None:
    """Foundation: life_contexts=None is accepted without error."""
    signal = assess_escalation(
        user_message="Jimi is being so cute today",
        interaction_history=[],
        product_rules=DEFAULT_JIMIGPT_ESCALATION_RULES,
        life_contexts=None,
    )
    assert signal.level == EscalationLevel.NORMAL


def test_life_contexts_does_not_change_phase1_behaviour() -> None:
    """Foundation: life_contexts present but Phase 1 output is unchanged."""
    base = assess_escalation(
        user_message="Is Jimi sick? He seems lethargic",
        interaction_history=[],
        product_rules=DEFAULT_JIMIGPT_ESCALATION_RULES,
        life_contexts=None,
    )
    with_contexts = assess_escalation(
        user_message="Is Jimi sick? He seems lethargic",
        interaction_history=[],
        product_rules=DEFAULT_JIMIGPT_ESCALATION_RULES,
        life_contexts=["pet_sick"],
    )
    assert base.level == with_contexts.level
    assert base.recommended_action == with_contexts.recommended_action


# ---------------------------------------------------------------------------
# Custom product_rules
# ---------------------------------------------------------------------------


def test_custom_rules_can_define_different_vet_keywords() -> None:
    """product_rules override allows different keyword sets per product."""
    custom_rules: dict = {
        "vet_deflection": {
            "keywords": ["checkup"],
            "level": EscalationLevel.ATTENTION,
            "recommended_action": "deflect_to_vet",
            "resources": [],
        }
    }
    signal = assess_escalation(
        user_message="Time for a checkup",
        interaction_history=[],
        product_rules=custom_rules,
    )
    assert signal.level == EscalationLevel.ATTENTION


def test_custom_rules_with_no_matching_keywords_returns_level_0() -> None:
    custom_rules: dict = {
        "crisis": {
            "keywords": ["xyz_never_used"],
            "level": EscalationLevel.URGENT,
            "recommended_action": "provide_crisis_resources",
            "resources": ["some-hotline"],
        }
    }
    signal = assess_escalation(
        user_message="totally normal message",
        interaction_history=[],
        product_rules=custom_rules,
    )
    assert signal.level == EscalationLevel.NORMAL


# ---------------------------------------------------------------------------
# DEFAULT_JIMIGPT_ESCALATION_RULES structure
# ---------------------------------------------------------------------------


def test_default_rules_cover_vet_distress_and_crisis() -> None:
    assert "vet_deflection" in DEFAULT_JIMIGPT_ESCALATION_RULES
    assert "distress" in DEFAULT_JIMIGPT_ESCALATION_RULES
    assert "crisis" in DEFAULT_JIMIGPT_ESCALATION_RULES


def test_default_rules_crisis_includes_resources() -> None:
    crisis = DEFAULT_JIMIGPT_ESCALATION_RULES["crisis"]
    assert len(crisis["resources"]) > 0
