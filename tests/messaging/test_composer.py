"""Tests for the message composer — composition model, compose(), and to_prompt()."""

from datetime import datetime, timezone

import pytest

from src.messaging.intent import IntentProfile, TrustStage
from src.messaging.models import MessageIntent
from src.messaging.recipient import RecipientState, TrustProfile
from src.messaging.signals import (
    ContextSignal,
    ContextSignalBundle,
    ContextSignalSource,
)
from src.messaging.tone import ToneCalibrationResult, ToneRule
from src.messaging.triggers import TriggerRule, TriggerType
from src.personality.models import (
    CommunicationStyle,
    EmotionalDisposition,
    EntityProfile,
    KnowledgeAwareness,
    RelationalStance,
    ToneSpectrum,
)
from src.personality.enums import EnergyLevel
from src.messaging.composer import ComposedPrompt, MessageComposition, MessageComposer

UTC = timezone.utc


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------


def _ts() -> datetime:
    return datetime(2026, 3, 23, 10, 0, tzinfo=UTC)


def _sig(
    key: str,
    value: str,
    source: ContextSignalSource = ContextSignalSource.TIME,
) -> ContextSignal:
    return ContextSignal(source=source, signal_key=key, signal_value=value, timestamp=_ts())


def _bundle(signals: list[ContextSignal] | None = None) -> ContextSignalBundle:
    return ContextSignalBundle(
        signals=signals or [
            _sig("time_of_day", "morning"),
            _sig("day_type", "workday"),
        ],
        user_id="u1",
        entity_id="e1",
        generated_at=_ts(),
    )


def _entity(
    name: str = "Sparky",
    forbidden_phrases: list[str] | None = None,
) -> EntityProfile:
    return EntityProfile(
        entity_id="e1",
        entity_name=name,
        entity_type="pet",
        product="jimigpt",
        communication=CommunicationStyle(
            sentence_length="short",
            energy_level=EnergyLevel.HIGH,
            emoji_usage="moderate",
            punctuation_style="excited_exclamations",
            vocabulary_level="simple",
        ),
        emotional=EmotionalDisposition(
            baseline_mood="cheerful",
            emotional_range="wide",
            need_expression="dramatic",
            humor_style="silly",
        ),
        relational=RelationalStance(
            attachment_style="clingy",
            initiative_style="proactive",
            boundary_respect="moderate",
            warmth_level="intense",
        ),
        knowledge=KnowledgeAwareness(
            domain_knowledge=["daily routines", "treats"],
            user_context_fields=["name", "schedule"],
            temporal_awareness=True,
            memory_references=True,
        ),
        primary_archetype="chaos_gremlin",
        archetype_weights={i.value: 1.0 / 14 for i in MessageIntent},
        forbidden_phrases=forbidden_phrases or ["I'm just an AI", "as an AI"],
        forbidden_topics=[],
    )


def _trust(stage: TrustStage = TrustStage.WORKING) -> TrustProfile:
    return TrustProfile(
        user_id="u1",
        entity_id="e1",
        current_stage=stage,
        stage_entered_at=datetime(2026, 1, 1, tzinfo=UTC),
    )


def _trigger(category: str = "greeting") -> TriggerRule:
    return TriggerRule(
        rule_id="t1",
        trigger_type=TriggerType.TIME_BASED,
        product="jimigpt",
        entity_id="e1",
        message_category=category,
        schedule_cron="0 8 * * *",
    )


def _tone_defaults() -> ToneSpectrum:
    return ToneSpectrum(
        warmth=0.8, humor=0.9, directness=0.7, gravity=0.1, energy=0.95, vulnerability=0.3
    )


# ---------------------------------------------------------------------------
# MessageComposition model — construction
# ---------------------------------------------------------------------------


def _make_composition(**kwargs) -> MessageComposition:
    defaults = dict(
        entity_voice=_entity(),
        intent=IntentProfile(primary_intent=MessageIntent.ENERGIZE, intensity=0.7),
        tone=ToneSpectrum(warmth=0.8, humor=0.9, directness=0.7, gravity=0.1, energy=0.95, vulnerability=0.3),
        tone_adjustments_applied=[],
        signals=_bundle(),
        recipient_state=RecipientState(
            likely_availability="busy",
            likely_energy=0.55,
            likely_receptivity=0.35,
            emotional_context="neutral",
            state_confidence=0.33,
        ),
        trust_stage=TrustStage.WORKING,
        relationship_depth=14,
        recent_messages=[],
        last_user_reply=None,
        message_category="greeting",
        max_characters=160,
        channel="sms",
    )
    defaults.update(kwargs)
    return MessageComposition(**defaults)


def test_message_composition_constructs() -> None:
    comp = _make_composition()
    assert comp.entity_voice.entity_name == "Sparky"
    assert comp.intent.primary_intent == MessageIntent.ENERGIZE
    assert comp.message_category == "greeting"


def test_message_composition_max_characters_default() -> None:
    comp = _make_composition()
    assert comp.max_characters == 160


def test_message_composition_max_characters_must_be_positive() -> None:
    with pytest.raises(Exception):
        _make_composition(max_characters=0)


def test_message_composition_channel_default_sms() -> None:
    comp = _make_composition()
    assert comp.channel == "sms"


# ---------------------------------------------------------------------------
# MessageComposition — foundation fields default correctly
# ---------------------------------------------------------------------------


def test_foundation_arc_id_defaults_none() -> None:
    comp = _make_composition()
    assert comp.arc_id is None


def test_foundation_arc_position_defaults_none() -> None:
    comp = _make_composition()
    assert comp.arc_position is None


def test_foundation_recipient_id_defaults_none() -> None:
    comp = _make_composition()
    assert comp.recipient_id is None


def test_foundation_life_contexts_defaults_empty() -> None:
    comp = _make_composition()
    assert comp.life_contexts == []


def test_foundation_entity_coordination_id_defaults_none() -> None:
    comp = _make_composition()
    assert comp.entity_coordination_id is None


def test_foundation_fields_can_be_set() -> None:
    comp = _make_composition(
        arc_id="arc-001",
        arc_position=2,
        recipient_id="owner-001",
        life_contexts=["sick_day"],
        entity_coordination_id="coord-001",
    )
    assert comp.arc_id == "arc-001"
    assert comp.arc_position == 2
    assert comp.recipient_id == "owner-001"
    assert comp.life_contexts == ["sick_day"]
    assert comp.entity_coordination_id == "coord-001"


# ---------------------------------------------------------------------------
# MessageComposer.compose() — return type and structure
# ---------------------------------------------------------------------------


def test_compose_returns_message_composition() -> None:
    composer = MessageComposer()
    result = composer.compose(
        entity=_entity(),
        trigger=_trigger(),
        signals=_bundle(),
        trust=_trust(),
        message_history=[],
        tone_defaults=_tone_defaults(),
    )
    assert isinstance(result, MessageComposition)


def test_compose_entity_voice_matches_input() -> None:
    composer = MessageComposer()
    entity = _entity(name="Biscuit")
    result = composer.compose(
        entity=entity,
        trigger=_trigger(),
        signals=_bundle(),
        trust=_trust(),
        message_history=[],
        tone_defaults=_tone_defaults(),
    )
    assert result.entity_voice.entity_name == "Biscuit"


def test_compose_message_category_from_trigger() -> None:
    composer = MessageComposer()
    result = composer.compose(
        entity=_entity(),
        trigger=_trigger("caring"),
        signals=_bundle(),
        trust=_trust(),
        message_history=[],
        tone_defaults=_tone_defaults(),
    )
    assert result.message_category == "caring"


def test_compose_intent_is_intent_profile() -> None:
    composer = MessageComposer()
    result = composer.compose(
        entity=_entity(),
        trigger=_trigger(),
        signals=_bundle(),
        trust=_trust(),
        message_history=[],
        tone_defaults=_tone_defaults(),
    )
    assert isinstance(result.intent, IntentProfile)
    assert isinstance(result.intent.primary_intent, MessageIntent)


def test_compose_tone_is_tone_spectrum() -> None:
    composer = MessageComposer()
    result = composer.compose(
        entity=_entity(),
        trigger=_trigger(),
        signals=_bundle(),
        trust=_trust(),
        message_history=[],
        tone_defaults=_tone_defaults(),
    )
    assert isinstance(result.tone, ToneSpectrum)


def test_compose_recipient_state_is_recipient_state() -> None:
    composer = MessageComposer()
    result = composer.compose(
        entity=_entity(),
        trigger=_trigger(),
        signals=_bundle(),
        trust=_trust(),
        message_history=[],
        tone_defaults=_tone_defaults(),
    )
    assert isinstance(result.recipient_state, RecipientState)


def test_compose_trust_stage_matches_trust_profile() -> None:
    composer = MessageComposer()
    result = composer.compose(
        entity=_entity(),
        trigger=_trigger(),
        signals=_bundle(),
        trust=_trust(TrustStage.DEEP),
        message_history=[],
        tone_defaults=_tone_defaults(),
    )
    assert result.trust_stage == TrustStage.DEEP


def test_compose_relationship_depth_from_history_length() -> None:
    composer = MessageComposer()
    history = ["msg1", "msg2", "msg3"]
    result = composer.compose(
        entity=_entity(),
        trigger=_trigger(),
        signals=_bundle(),
        trust=_trust(),
        message_history=history,
        tone_defaults=_tone_defaults(),
    )
    assert result.relationship_depth == len(history)


def test_compose_recent_messages_stored() -> None:
    composer = MessageComposer()
    history = ["hello world", "good morning"]
    result = composer.compose(
        entity=_entity(),
        trigger=_trigger(),
        signals=_bundle(),
        trust=_trust(),
        message_history=history,
        tone_defaults=_tone_defaults(),
    )
    assert result.recent_messages == history


# ---------------------------------------------------------------------------
# compose() — foundation: recipient_id flows through
# ---------------------------------------------------------------------------


def test_compose_recipient_id_none_by_default() -> None:
    composer = MessageComposer()
    result = composer.compose(
        entity=_entity(),
        trigger=_trigger(),
        signals=_bundle(),
        trust=_trust(),
        message_history=[],
        tone_defaults=_tone_defaults(),
    )
    assert result.recipient_id is None


def test_compose_recipient_id_flows_through() -> None:
    composer = MessageComposer()
    result = composer.compose(
        entity=_entity(),
        trigger=_trigger(),
        signals=_bundle(),
        trust=_trust(),
        message_history=[],
        tone_defaults=_tone_defaults(),
        recipient_id="owner-abc",
    )
    assert result.recipient_id == "owner-abc"


def test_compose_foundation_fields_default_to_none_or_empty() -> None:
    composer = MessageComposer()
    result = composer.compose(
        entity=_entity(),
        trigger=_trigger(),
        signals=_bundle(),
        trust=_trust(),
        message_history=[],
        tone_defaults=_tone_defaults(),
    )
    assert result.arc_id is None
    assert result.arc_position is None
    assert result.life_contexts == []
    assert result.entity_coordination_id is None


# ---------------------------------------------------------------------------
# Codex review fix: life_contexts must be accepted and forwarded by compose()
# ---------------------------------------------------------------------------


def test_compose_accepts_life_contexts_param() -> None:
    """compose() must accept life_contexts as a keyword argument."""
    composer = MessageComposer()
    result = composer.compose(
        entity=_entity(),
        trigger=_trigger(),
        signals=_bundle(),
        trust=_trust(),
        message_history=[],
        tone_defaults=_tone_defaults(),
        life_contexts=["sick_day"],
    )
    assert isinstance(result, MessageComposition)


def test_compose_life_contexts_none_default() -> None:
    """Omitting life_contexts should produce empty list on composition."""
    composer = MessageComposer()
    result = composer.compose(
        entity=_entity(),
        trigger=_trigger(),
        signals=_bundle(),
        trust=_trust(),
        message_history=[],
        tone_defaults=_tone_defaults(),
    )
    assert result.life_contexts == []


def test_compose_life_contexts_explicit_none_same_as_omitted() -> None:
    """Explicit life_contexts=None should produce same result as omitting."""
    composer = MessageComposer()
    result = composer.compose(
        entity=_entity(),
        trigger=_trigger(),
        signals=_bundle(),
        trust=_trust(),
        message_history=[],
        tone_defaults=_tone_defaults(),
        life_contexts=None,
    )
    assert result.life_contexts == []


# ---------------------------------------------------------------------------
# MessageComposer.to_prompt() — 8 blocks
# ---------------------------------------------------------------------------


def test_to_prompt_returns_composed_prompt() -> None:
    composer = MessageComposer()
    comp = _make_composition()
    result = composer.to_prompt(comp)
    assert isinstance(result, ComposedPrompt)


def test_to_prompt_has_eight_blocks() -> None:
    composer = MessageComposer()
    result = composer.to_prompt(_make_composition())
    assert result.block_count == 8


def test_to_prompt_system_prompt_non_empty() -> None:
    composer = MessageComposer()
    result = composer.to_prompt(_make_composition())
    assert len(result.system_prompt.strip()) > 0


def test_to_prompt_block1_entity_voice_contains_name() -> None:
    """Block 1: entity voice — entity name must appear."""
    composer = MessageComposer()
    result = composer.to_prompt(_make_composition(entity_voice=_entity("Sparky")))
    assert "Sparky" in result.blocks[0]


def test_to_prompt_block1_contains_entity_type() -> None:
    composer = MessageComposer()
    result = composer.to_prompt(_make_composition())
    assert "pet" in result.blocks[0].lower()


def test_to_prompt_block2_intent_contains_primary_intent() -> None:
    """Block 2: message intent — primary intent value must appear."""
    composer = MessageComposer()
    comp = _make_composition(
        intent=IntentProfile(primary_intent=MessageIntent.ENERGIZE, intensity=0.7)
    )
    result = composer.to_prompt(comp)
    assert "energize" in result.blocks[1].lower()


def test_to_prompt_block2_contains_intensity() -> None:
    composer = MessageComposer()
    comp = _make_composition(
        intent=IntentProfile(primary_intent=MessageIntent.COMFORT, intensity=0.4)
    )
    result = composer.to_prompt(comp)
    assert "0.4" in result.blocks[1]


def test_to_prompt_block3_tone_contains_dimensions() -> None:
    """Block 3: tone targets — all 6 dimensions must appear."""
    composer = MessageComposer()
    result = composer.to_prompt(_make_composition())
    block3 = result.blocks[2].lower()
    for dim in ("warmth", "humor", "directness", "gravity", "energy", "vulnerability"):
        assert dim in block3, f"Missing dimension: {dim}"


def test_to_prompt_block4_context_contains_time_signal() -> None:
    """Block 4: world context — time_of_day signal value must appear."""
    composer = MessageComposer()
    signals = _bundle([_sig("time_of_day", "morning"), _sig("day_of_week", "monday")])
    result = composer.to_prompt(_make_composition(signals=signals))
    assert "morning" in result.blocks[3].lower()


def test_to_prompt_block5_user_state_contains_availability() -> None:
    """Block 5: user state — likely_availability must appear."""
    composer = MessageComposer()
    state = RecipientState(
        likely_availability="busy",
        likely_energy=0.55,
        likely_receptivity=0.35,
        emotional_context="neutral",
        state_confidence=0.33,
    )
    result = composer.to_prompt(_make_composition(recipient_state=state))
    assert "busy" in result.blocks[4].lower()


def test_to_prompt_block5_contains_emotional_context() -> None:
    composer = MessageComposer()
    state = RecipientState(
        likely_availability="free",
        likely_energy=0.5,
        likely_receptivity=0.5,
        emotional_context="stressed",
        state_confidence=0.5,
    )
    result = composer.to_prompt(_make_composition(recipient_state=state))
    assert "stressed" in result.blocks[4].lower()


def test_to_prompt_block6_trust_contains_trust_stage() -> None:
    """Block 6: relationship depth — trust stage must appear."""
    composer = MessageComposer()
    result = composer.to_prompt(_make_composition(trust_stage=TrustStage.DEEP))
    assert "deep" in result.blocks[5].lower()


def test_to_prompt_block6_contains_relationship_depth() -> None:
    composer = MessageComposer()
    result = composer.to_prompt(_make_composition(relationship_depth=42))
    assert "42" in result.blocks[5]


def test_to_prompt_block7_antipatterns_contains_forbidden_phrase() -> None:
    """Block 7: anti-patterns — forbidden phrases must appear."""
    composer = MessageComposer()
    entity = _entity(forbidden_phrases=["I'm just an AI"])
    result = composer.to_prompt(_make_composition(entity_voice=entity))
    assert "I'm just an AI" in result.blocks[6]


def test_to_prompt_block8_directive_contains_category() -> None:
    """Block 8: generation directive — message_category must appear."""
    composer = MessageComposer()
    result = composer.to_prompt(_make_composition(message_category="caring"))
    assert "caring" in result.blocks[7].lower()


def test_to_prompt_block8_directive_contains_max_characters() -> None:
    composer = MessageComposer()
    result = composer.to_prompt(_make_composition(max_characters=160))
    assert "160" in result.blocks[7]


def test_to_prompt_block8_directive_contains_channel() -> None:
    composer = MessageComposer()
    result = composer.to_prompt(_make_composition(channel="sms"))
    assert "sms" in result.blocks[7].lower()


def test_to_prompt_all_blocks_in_system_prompt() -> None:
    """Every block's content appears in the assembled system_prompt."""
    composer = MessageComposer()
    result = composer.to_prompt(_make_composition())
    for block in result.blocks:
        # At least some content from each block appears in the full prompt
        assert any(line.strip() in result.system_prompt for line in block.splitlines() if line.strip())


# ---------------------------------------------------------------------------
# Full compose() → to_prompt() pipeline
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Codex review fix: compose() must pass intent_weights, not archetype blend weights
# ---------------------------------------------------------------------------


def test_compose_accepts_intent_weights_param() -> None:
    """compose() must accept intent_weights to pass to select_intent()."""
    intent_weights = {i.value: 1.0 / 14 for i in MessageIntent}
    composer = MessageComposer()
    result = composer.compose(
        entity=_entity(),
        trigger=_trigger(),
        signals=_bundle(),
        trust=_trust(),
        message_history=[],
        tone_defaults=_tone_defaults(),
        intent_weights=intent_weights,
    )
    assert isinstance(result.intent, IntentProfile)


def test_compose_without_intent_weights_uses_balanced_fallback() -> None:
    """When intent_weights is omitted, compose() should use balanced fallback."""
    composer = MessageComposer()
    result = composer.compose(
        entity=_entity(),
        trigger=_trigger(),
        signals=_bundle(),
        trust=_trust(),
        message_history=[],
        tone_defaults=_tone_defaults(),
    )
    # Should not raise even though entity.archetype_weights are blend keys
    assert isinstance(result.intent, IntentProfile)


# ---------------------------------------------------------------------------
# Full compose() → to_prompt() pipeline
# ---------------------------------------------------------------------------


def test_compose_then_to_prompt_produces_eight_blocks() -> None:
    composer = MessageComposer()
    comp = composer.compose(
        entity=_entity(),
        trigger=_trigger("greeting"),
        signals=_bundle([
            _sig("time_of_day", "morning"),
            _sig("day_type", "workday"),
        ]),
        trust=_trust(TrustStage.WORKING),
        message_history=["Good morning!"],
        tone_defaults=_tone_defaults(),
    )
    prompt = composer.to_prompt(comp)
    assert prompt.block_count == 8
    assert "Sparky" in prompt.blocks[0]
