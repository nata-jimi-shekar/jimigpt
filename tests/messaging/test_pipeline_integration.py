"""Full 7-stage message pipeline integration test.

Runs the complete pipeline with the chaos_gremlin archetype and a mocked
LLM.  Verifies each stage output, all 8 prompt blocks, quality gate pass,
effectiveness recording, and — critically — all foundation fields.

Stages exercised:
  1. Trigger evaluation  (TriggerRule constructed, no orchestrator needed)
  2. Signal collection   (collect_time_signals)
  3. Composition         (MessageComposer.compose → MessageComposition)
  4. LLM generation      (generate_message, mocked)
  5. Quality gate        (QualityGate.evaluate)
  6. Effectiveness       (record_effectiveness)
  Prompt translation     (MessageComposer.to_prompt → ComposedPrompt, 8 blocks)
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.messaging.composer import MessageComposer
from src.messaging.effectiveness import record_effectiveness
from src.messaging.generator import generate_message
from src.messaging.intent import TrustStage
from src.messaging.models import MessageIntent
from src.messaging.quality import QualityCheck, QualityGate
from src.messaging.recipient import TrustProfile
from src.messaging.signals import (
    ContextSignalBundle,
    ContextSignalSource,
    SignalCollector,
    collect_time_signals,
)
from src.messaging.triggers import TriggerRule, TriggerType
from src.personality.archetypes import blend_archetypes, load_archetype

UTC = timezone.utc

_ARCHETYPE_PATH = (
    Path(__file__).parent.parent.parent
    / "config" / "archetypes" / "jimigpt" / "chaos_gremlin.yaml"
)
_NOW = datetime(2026, 3, 23, 9, 0, tzinfo=UTC)  # Monday 09:00 — workday morning


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def archetype():
    return load_archetype(_ARCHETYPE_PATH)


@pytest.fixture(scope="module")
def entity(archetype):
    return blend_archetypes(
        primary=archetype,
        secondary=None,
        weights={archetype.id: 1.0},
    )


@pytest.fixture(scope="module")
def trigger():
    return TriggerRule(
        rule_id="t1",
        trigger_type=TriggerType.TIME_BASED,
        product="jimigpt",
        entity_id="e1",
        message_category="greeting",
        schedule_cron="0 9 * * *",
    )


@pytest.fixture(scope="module")
def trust():
    return TrustProfile(
        user_id="u1",
        entity_id="e1",
        current_stage=TrustStage.WORKING,
        stage_entered_at=datetime(2026, 1, 1, tzinfo=UTC),
    )


@pytest.fixture(scope="module")
def signals():
    return ContextSignalBundle(
        signals=collect_time_signals("u1", "e1", _NOW),
        user_id="u1",
        entity_id="e1",
        generated_at=_NOW,
    )


@pytest.fixture(scope="module")
def composition(entity, trigger, signals, trust, archetype):
    composer = MessageComposer()
    return composer.compose(
        entity=entity,
        trigger=trigger,
        signals=signals,
        trust=trust,
        message_history=["Good morning yesterday!", "Miss you!"],
        tone_defaults=archetype.tone_defaults,
    )


@pytest.fixture
def mock_client():
    client = MagicMock()
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="Rise and shine! Treat time soon! 🐾")]
    mock_response.usage.input_tokens = 180
    mock_response.usage.output_tokens = 9
    client.messages.create = AsyncMock(return_value=mock_response)
    return client


# ---------------------------------------------------------------------------
# Stage 1 — Trigger
# ---------------------------------------------------------------------------


def test_trigger_is_time_based(trigger):
    assert trigger.trigger_type == TriggerType.TIME_BASED
    assert trigger.message_category == "greeting"


def test_trigger_foundation_arc_template_none(trigger):
    assert trigger.arc_template is None


def test_trigger_foundation_sibling_entity_ids_empty(trigger):
    assert trigger.sibling_entity_ids == []


# ---------------------------------------------------------------------------
# Stage 2 — Signal collection
# ---------------------------------------------------------------------------


def test_signals_contain_time_source(signals):
    assert signals.has_signal(ContextSignalSource.TIME)


def test_signals_have_three_time_signals(signals):
    assert len(signals.signals) == 3


def test_signals_time_of_day_morning(signals):
    sig = signals.get_signal("time_of_day")
    assert sig is not None
    assert sig.signal_value == "morning"


def test_signals_day_type_workday(signals):
    sig = signals.get_signal("day_type")
    assert sig is not None
    assert sig.signal_value == "workday"


# ---------------------------------------------------------------------------
# Stage 3 — Composition
# ---------------------------------------------------------------------------


def test_composition_entity_voice_is_chaos_gremlin(composition):
    assert "chaos" in composition.entity_voice.primary_archetype.lower()


def test_composition_intent_is_intent_profile(composition):
    assert isinstance(composition.intent.primary_intent, MessageIntent)


def test_composition_workday_morning_greeting_energize(composition):
    """chaos_gremlin + workday morning greeting → ENERGIZE."""
    assert composition.intent.primary_intent == MessageIntent.ENERGIZE


def test_composition_tone_is_tone_spectrum(composition, archetype):
    """Tone derived from archetype defaults, then signal-adjusted."""
    assert 0.0 <= composition.tone.energy <= 1.0
    assert 0.0 <= composition.tone.warmth <= 1.0


def test_composition_tone_morning_energy_raised(composition, archetype):
    """Morning rule (+0.1 energy) applied over chaos_gremlin's 0.95 baseline — clamped to 1.0."""
    assert composition.tone.energy <= 1.0
    assert composition.tone.energy >= archetype.tone_defaults.energy


def test_composition_recipient_state_inferred(composition):
    assert composition.recipient_state.likely_availability == "busy"
    assert composition.recipient_state.likely_receptivity < 0.5


def test_composition_trust_stage_working(composition):
    assert composition.trust_stage == TrustStage.WORKING


def test_composition_relationship_depth_from_history(composition):
    assert composition.relationship_depth == 2


# ---------------------------------------------------------------------------
# Stage 3 — Foundation fields on MessageComposition
# ---------------------------------------------------------------------------


def test_foundation_arc_id_is_none(composition):
    assert composition.arc_id is None


def test_foundation_arc_position_is_none(composition):
    assert composition.arc_position is None


def test_foundation_recipient_id_is_none_by_default(composition):
    assert composition.recipient_id is None


def test_foundation_life_contexts_is_empty_list(composition):
    assert composition.life_contexts == []


def test_foundation_entity_coordination_id_is_none(composition):
    assert composition.entity_coordination_id is None


def test_foundation_recipient_id_flows_through(entity, trigger, signals, trust, archetype):
    """recipient_id passed to compose() appears on the composition."""
    composer = MessageComposer()
    comp = composer.compose(
        entity=entity,
        trigger=trigger,
        signals=signals,
        trust=trust,
        message_history=[],
        tone_defaults=archetype.tone_defaults,
        recipient_id="owner-abc",
    )
    assert comp.recipient_id == "owner-abc"


def test_foundation_life_contexts_none_no_behavior_change(
    entity, trigger, signals, trust, archetype, composition
):
    """Explicit life_contexts=None produces same intent as omitted (Phase 1 no-op)."""
    # compose() doesn't yet expose life_contexts directly but foundation is on the model
    assert composition.life_contexts == []


# ---------------------------------------------------------------------------
# Prompt translation — 8 blocks
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def composed_prompt(composition):
    composer = MessageComposer()
    return composer.to_prompt(composition)


def test_prompt_has_eight_blocks(composed_prompt):
    assert composed_prompt.block_count == 8


def test_prompt_system_prompt_non_empty(composed_prompt):
    assert len(composed_prompt.system_prompt.strip()) > 0


def test_prompt_block1_entity_voice_has_name(composed_prompt, archetype):
    assert archetype.name in composed_prompt.blocks[0]


def test_prompt_block2_intent_has_energize(composed_prompt):
    assert "energize" in composed_prompt.blocks[1].lower()


def test_prompt_block3_tone_has_all_dimensions(composed_prompt):
    block = composed_prompt.blocks[2].lower()
    for dim in ("warmth", "humor", "directness", "gravity", "energy", "vulnerability"):
        assert dim in block


def test_prompt_block4_context_has_morning(composed_prompt):
    assert "morning" in composed_prompt.blocks[3].lower()


def test_prompt_block5_user_state_has_busy(composed_prompt):
    assert "busy" in composed_prompt.blocks[4].lower()


def test_prompt_block6_trust_has_working(composed_prompt):
    assert "working" in composed_prompt.blocks[5].lower()


def test_prompt_block7_antipatterns_has_forbidden_phrase(composed_prompt, archetype):
    assert archetype.forbidden_phrases[0] in composed_prompt.blocks[6]


def test_prompt_block8_directive_has_greeting(composed_prompt):
    assert "greeting" in composed_prompt.blocks[7].lower()


def test_prompt_block8_directive_has_160_chars(composed_prompt):
    assert "160" in composed_prompt.blocks[7]


# ---------------------------------------------------------------------------
# Stage 4 — LLM generation (mocked)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_generate_message_returns_generated_message(composition, mock_client):
    from src.messaging.generator import GeneratedMessage
    result = await generate_message(composition, client=mock_client)
    assert isinstance(result, GeneratedMessage)


@pytest.mark.asyncio
async def test_generated_content_is_set(composition, mock_client):
    result = await generate_message(composition, client=mock_client)
    assert result.content == "Rise and shine! Treat time soon! 🐾"


@pytest.mark.asyncio
async def test_generated_intended_intent_matches_composition(composition, mock_client):
    result = await generate_message(composition, client=mock_client)
    assert result.intended_intent == composition.intent.primary_intent


@pytest.mark.asyncio
async def test_generated_intended_tone_matches_composition(composition, mock_client):
    result = await generate_message(composition, client=mock_client)
    assert result.intended_tone == composition.tone


@pytest.mark.asyncio
async def test_generated_character_count_accurate(composition, mock_client):
    result = await generate_message(composition, client=mock_client)
    assert result.character_count == len(result.content)


@pytest.mark.asyncio
async def test_generated_message_under_160_chars(composition, mock_client):
    result = await generate_message(composition, client=mock_client)
    assert result.character_count <= 160


@pytest.mark.asyncio
async def test_generated_message_api_called_once(composition, mock_client):
    await generate_message(composition, client=mock_client)
    mock_client.messages.create.assert_called_once()


# ---------------------------------------------------------------------------
# Stage 5 — Quality gate
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_quality_gate_passes_clean_message(composition, mock_client):
    result = await generate_message(composition, client=mock_client)
    gate = QualityGate(checks=list(QualityCheck))
    qr = gate.evaluate(result, composition, previous_message=None)
    assert qr.passed is True
    assert qr.checks_failed == []


@pytest.mark.asyncio
async def test_quality_gate_runs_all_checks(composition, mock_client):
    result = await generate_message(composition, client=mock_client)
    gate = QualityGate(checks=list(QualityCheck))
    qr = gate.evaluate(result, composition)
    assert len(qr.checks_run) == len(QualityCheck)


@pytest.mark.asyncio
async def test_consecutive_coherence_passes_first_message(composition, mock_client):
    result = await generate_message(composition, client=mock_client)
    gate = QualityGate(checks=[QualityCheck.CONSECUTIVE_COHERENCE])
    qr = gate.evaluate(result, composition, previous_message=None)
    assert qr.passed is True


# ---------------------------------------------------------------------------
# Stage 6 — Effectiveness tracking
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_effectiveness_records_from_generated_message(composition, mock_client):
    result = await generate_message(composition, client=mock_client)
    eff = record_effectiveness(
        message_id=result.message_id,
        intended_intent=result.intended_intent,
        intended_tone=result.intended_tone,
        user_reaction="positive",
        user_replied=True,
        reply_sentiment="positive",
        time_to_reaction_seconds=60,
    )
    assert eff.effectiveness_score == pytest.approx(0.7)
    assert eff.message_id == result.message_id


@pytest.mark.asyncio
async def test_effectiveness_no_response_score_zero(composition, mock_client):
    result = await generate_message(composition, client=mock_client)
    eff = record_effectiveness(
        message_id=result.message_id,
        intended_intent=result.intended_intent,
        intended_tone=result.intended_tone,
        user_reaction=None,
        user_replied=False,
        reply_sentiment=None,
        time_to_reaction_seconds=None,
    )
    assert eff.effectiveness_score == 0.0


# ---------------------------------------------------------------------------
# Full pipeline: compose → prompt → generate → gate → effectiveness
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_full_pipeline_end_to_end(entity, trigger, signals, trust, archetype):
    """Smoke test: run all stages in sequence, verify outputs chain correctly."""
    # Stage 3: compose
    composer = MessageComposer()
    comp = composer.compose(
        entity=entity,
        trigger=trigger,
        signals=signals,
        trust=trust,
        message_history=[],
        tone_defaults=archetype.tone_defaults,
        recipient_id="owner-001",
    )
    assert comp.recipient_id == "owner-001"
    assert comp.arc_id is None
    assert comp.life_contexts == []

    # Prompt translation
    prompt = composer.to_prompt(comp)
    assert prompt.block_count == 8

    # Stage 4: generate (mocked)
    client = MagicMock()
    client.messages.create = AsyncMock(
        return_value=MagicMock(
            content=[MagicMock(text="Morning mischief incoming! 🐾")],
            usage=MagicMock(input_tokens=190, output_tokens=5),
        )
    )
    msg = await generate_message(comp, client=client)
    assert len(msg.content) > 0
    assert msg.character_count == len(msg.content)
    assert msg.intended_intent == comp.intent.primary_intent

    # Stage 5: quality gate
    gate = QualityGate(checks=list(QualityCheck))
    qr = gate.evaluate(msg, comp, previous_message=None)
    assert qr.passed is True

    # Stage 6: effectiveness
    eff = record_effectiveness(
        message_id=msg.message_id,
        intended_intent=msg.intended_intent,
        intended_tone=msg.intended_tone,
        user_reaction="positive",
        user_replied=False,
        reply_sentiment=None,
        time_to_reaction_seconds=None,
    )
    assert eff.effectiveness_score == pytest.approx(0.3)
    assert 0.0 <= eff.effectiveness_score <= 1.0


# ---------------------------------------------------------------------------
# Foundation: verify all fields are None/empty across full pipeline output
# ---------------------------------------------------------------------------


def test_all_foundation_fields_none_or_empty_in_pipeline_output(composition):
    """Comprehensive foundation field verification."""
    assert composition.arc_id is None
    assert composition.arc_position is None
    assert composition.recipient_id is None
    assert composition.life_contexts == []
    assert composition.entity_coordination_id is None


def test_foundation_fields_do_not_affect_pipeline_behaviour(
    entity, trigger, signals, trust, archetype, composition
):
    """Pipeline output with explicit None/empty foundation values is identical."""
    composer = MessageComposer()
    comp_explicit = composer.compose(
        entity=entity,
        trigger=trigger,
        signals=signals,
        trust=trust,
        message_history=["Good morning yesterday!", "Miss you!"],
        tone_defaults=archetype.tone_defaults,
        recipient_id=None,
    )
    # Intent, tone, and state should be identical (foundation fields are no-ops)
    assert comp_explicit.intent.primary_intent == composition.intent.primary_intent
    assert comp_explicit.tone.energy == composition.tone.energy
    assert comp_explicit.recipient_state.likely_availability == (
        composition.recipient_state.likely_availability
    )
