"""Message Composer — convergence point of the message pipeline.

Orchestrates signals → intent → tone → recipient state → MessageComposition,
then translates the composition into an 8-block LLM prompt.

Foundation (Phase 2):
  - arc_id / arc_position on MessageComposition: which message arc and position
  - recipient_id: explicit recipient (owner in Phase 1, anyone in Phase 2)
  - life_contexts: active life contexts flow through intent/tone/state engines
  - entity_coordination_id: multi-pet scheduling coordination
"""

from pydantic import BaseModel, Field

from src.messaging.intent import IntentProfile, TrustStage, select_intent
from src.messaging.models import MessageIntent
from src.messaging.recipient import RecipientState, TrustProfile, infer_recipient_state
from src.messaging.signals import ContextSignalBundle
from src.messaging.tone import ToneRule, calibrate_tone
from src.messaging.triggers import TriggerRule
from src.personality.models import EntityProfile, ToneSpectrum

# Balanced intent weights — used when caller does not supply archetype-specific weights
_BALANCED_INTENT_WEIGHTS: dict[str, float] = {
    i.value: 1.0 / len(MessageIntent) for i in MessageIntent
}

# Default tone when caller does not supply archetype-specific defaults
_NEUTRAL_TONE = ToneSpectrum(
    warmth=0.6,
    humor=0.5,
    directness=0.5,
    gravity=0.3,
    energy=0.6,
    vulnerability=0.4,
)

_TRUST_INSTRUCTIONS: dict[str, str] = {
    "stranger": "Keep it light and warm. No pressure.",
    "initial": "Gently build familiarity. Stay curious.",
    "working": "You know each other. Be yourself.",
    "deep": "You share a bond. Express it naturally.",
    "alliance": "Deep mutual trust. Full emotional range available.",
}


class MessageComposition(BaseModel):
    """Complete specification for generating one message.

    This is what gets translated into the LLM prompt via to_prompt().
    """

    # Personality
    entity_voice: EntityProfile

    # Intent
    intent: IntentProfile

    # Tone
    tone: ToneSpectrum
    tone_adjustments_applied: list[ToneRule]

    # Context
    signals: ContextSignalBundle
    recipient_state: RecipientState

    # Trust
    trust_stage: TrustStage
    relationship_depth: int

    # History
    recent_messages: list[str]
    last_user_reply: str | None

    # Product
    message_category: str
    product_context: dict[str, object] = Field(default_factory=dict)

    # Constraints
    max_characters: int = Field(default=160, gt=0)
    channel: str = "sms"

    # Foundation: Phase 2+ fields (all default to None / empty)
    arc_id: str | None = None                  # Message arc this belongs to
    arc_position: int | None = None            # Position within the arc
    recipient_id: str | None = None            # Explicit recipient (owner in Phase 1)
    life_contexts: list[str] = Field(default_factory=list)  # Active life contexts
    entity_coordination_id: str | None = None  # Multi-pet coordination


class ComposedPrompt(BaseModel):
    """8-block LLM system prompt built from a MessageComposition."""

    system_prompt: str
    blocks: list[str]
    composition_id: str

    @property
    def block_count(self) -> int:
        return len(self.blocks)


class MessageComposer:
    """Orchestrates the full composition pipeline and prompt translation."""

    def compose(
        self,
        entity: EntityProfile,
        trigger: TriggerRule,
        signals: ContextSignalBundle,
        trust: TrustProfile,
        message_history: list[str],
        *,
        tone_defaults: ToneSpectrum | None = None,
        intent_weights: dict[str, float] | None = None,
        recipient_id: str | None = None,  # Foundation: Phase 2 multi-recipient
        life_contexts: list[str] | None = None,  # Foundation: Phase 2 life events
    ) -> MessageComposition:
        """Orchestrate signals → intent → tone → state → MessageComposition.

        Args:
            intent_weights: Intent-keyed weights (e.g. {"energize": 0.4}).
                Must NOT be archetype blend weights. Falls back to balanced
                distribution when omitted.
            life_contexts: Active life contexts forwarded to intent/tone/state
                engines. None in Phase 1 — Phase 2 activates overrides.
            recipient_id: Explicit recipient. Phase 1 = owner ID or None.
        """
        base_tone = tone_defaults if tone_defaults is not None else _NEUTRAL_TONE
        weights = intent_weights if intent_weights is not None else _BALANCED_INTENT_WEIGHTS

        intent = select_intent(
            trigger=trigger,
            signals=signals,
            trust_stage=trust.current_stage,
            archetype_weights=weights,
            life_contexts=life_contexts,
        )

        tone_result = calibrate_tone(
            archetype_defaults=base_tone,
            signals=signals,
            trust_stage=trust.current_stage,
            life_contexts=life_contexts,
        )

        recipient_state = infer_recipient_state(
            signals=signals,
            trust_profile=trust,
            interaction_history=[],
            life_contexts=life_contexts,
        )

        return MessageComposition(
            entity_voice=entity,
            intent=intent,
            tone=tone_result.tone,
            tone_adjustments_applied=tone_result.adjustments_applied,
            signals=signals,
            recipient_state=recipient_state,
            trust_stage=trust.current_stage,
            relationship_depth=len(message_history),
            recent_messages=message_history,
            last_user_reply=None,
            message_category=trigger.message_category,
            max_characters=160,
            channel="sms",
            recipient_id=recipient_id,
        )

    def to_prompt(self, composition: MessageComposition) -> ComposedPrompt:
        """Translate a MessageComposition into an 8-block LLM system prompt."""
        blocks = [
            _block_entity_voice(composition),
            _block_intent(composition),
            _block_tone(composition),
            _block_world_context(composition),
            _block_user_state(composition),
            _block_relationship(composition),
            _block_anti_patterns(composition),
            _block_directive(composition),
        ]
        system_prompt = "\n\n".join(b for b in blocks if b.strip())
        return ComposedPrompt(
            system_prompt=system_prompt,
            blocks=blocks,
            composition_id=composition.entity_voice.entity_id,
        )


# ---------------------------------------------------------------------------
# Prompt block builders
# ---------------------------------------------------------------------------


def _block_entity_voice(c: MessageComposition) -> str:
    e = c.entity_voice
    return (
        f"You are {e.entity_name}, a {e.entity_type} for {e.product}.\n"
        f"Personality: {e.emotional.baseline_mood} mood, "
        f"{e.relational.warmth_level} warmth, "
        f"{e.communication.sentence_length} sentences, "
        f"{e.communication.emoji_usage} emoji usage."
    )


def _block_intent(c: MessageComposition) -> str:
    intent = c.intent
    lines = [
        f"The purpose of this message is to {intent.primary_intent.value}.",
        f"Express this with {intent.intensity:.1f} intensity.",
    ]
    if intent.secondary_intent:
        lines.append(f"Secondary intent: {intent.secondary_intent.value}.")
    return "\n".join(lines)


def _block_tone(c: MessageComposition) -> str:
    t = c.tone
    lines = [
        "Calibrate your tone:",
        f"- Warmth: {t.warmth:.2f}/1.0",
        f"- Humor: {t.humor:.2f}/1.0",
        f"- Directness: {t.directness:.2f}/1.0",
        f"- Gravity: {t.gravity:.2f}/1.0",
        f"- Energy: {t.energy:.2f}/1.0",
        f"- Vulnerability: {t.vulnerability:.2f}/1.0",
    ]
    if c.tone_adjustments_applied:
        lines.append("Tone adjusted for context:")
        for rule in c.tone_adjustments_applied:
            lines.append(f"  • {rule.reason}")
    return "\n".join(lines)


def _block_world_context(c: MessageComposition) -> str:
    lines = ["Current context (weave in naturally — never state explicitly):"]
    for sig in c.signals.signals:
        lines.append(f"- {sig.signal_key}: {sig.signal_value}")
    if not c.signals.signals:
        lines.append("- No additional context available.")
    lines.append("A pet doesn't say 'Based on the time...' — it just acts accordingly.")
    return "\n".join(lines)


def _block_user_state(c: MessageComposition) -> str:
    rs = c.recipient_state
    return (
        f"The user is likely: {rs.likely_availability}.\n"
        f"Their energy level is probably: {rs.likely_energy:.2f}/1.0.\n"
        f"Emotional context: {rs.emotional_context}.\n"
        f"Receptivity: {rs.likely_receptivity:.2f}/1.0.\n"
        f"Adjust your message to meet them where they are, not where you are."
    )


def _block_relationship(c: MessageComposition) -> str:
    stage = c.trust_stage.value
    instructions = _TRUST_INSTRUCTIONS.get(stage, "Be yourself.")
    return (
        f"Trust stage: {stage}. {instructions}\n"
        f"You have had {c.relationship_depth} interactions."
    )


def _block_anti_patterns(c: MessageComposition) -> str:
    e = c.entity_voice
    parts: list[str] = ["NEVER say or imply:"]
    if e.forbidden_phrases:
        parts.append(", ".join(f'"{p}"' for p in e.forbidden_phrases))
    if e.forbidden_topics:
        parts.append("Avoid topics: " + ", ".join(e.forbidden_topics))
    if len(parts) == 1:
        parts.append("(no specific restrictions)")
    return "\n".join(parts)


def _block_directive(c: MessageComposition) -> str:
    lines = [
        f"Generate a {c.message_category} message.",
        f"Maximum length: {c.max_characters} characters.",
        f"Channel: {c.channel.upper()}.",
        "Be concise, in-character, and emotionally resonant.",
    ]
    return "\n".join(lines)
