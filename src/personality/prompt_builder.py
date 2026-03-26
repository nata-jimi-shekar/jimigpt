"""Personality-to-prompt translator using Jinja2 templates."""

from datetime import UTC, datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from pydantic import BaseModel, Field

from src.personality.models import EntityProfile
from src.trust.ladder import TrustStage

_DEFAULT_PROMPTS_DIR = Path(__file__).parent.parent.parent / "config" / "prompts"

_BLOCK_DEFINITIONS: list[tuple[str, str, int]] = [
    ("identity", "base_identity.j2", 1),
    ("communication", "communication_style.j2", 2),
    ("emotional", "emotional_disposition.j2", 3),
    ("relational", "relational_stance.j2", 4),
    ("knowledge", "knowledge_awareness.j2", 5),
    ("trust_relationship", "trust_relationship.j2", 6),
    ("anti_patterns", "anti_patterns.j2", 7),
    ("message_directive", "message_directive.j2", 8),
]

# Stage-specific instructions for the trust_relationship prompt block.
# Stranger = gentle intro; working = reference past; deep = reflect patterns.
_TRUST_INSTRUCTIONS: dict[TrustStage, str] = {
    TrustStage.STRANGER: (
        "You're just getting to know each other. "
        "Keep messages warm, simple, and low-pressure. "
        "No references to shared history."
    ),
    TrustStage.INITIAL: (
        "You're building familiarity. "
        "Gently reference what you learned during onboarding. "
        "Stay curious and warm."
    ),
    TrustStage.WORKING: (
        "You know each other well. "
        "Reference past interactions naturally and express your full personality."
    ),
    TrustStage.DEEP: (
        "You share a deep bond. "
        "Reflect on patterns you've noticed. "
        "Deeper emotional expression is natural here."
    ),
    TrustStage.ALLIANCE: (
        "Deep, sustained mutual trust. "
        "The full emotional range is available. "
        "Reference long-term patterns freely."
    ),
}


class MessageContext(BaseModel):
    """Validated input context for prompt assembly."""

    message_category: str
    max_characters: int = Field(default=160, gt=0)
    channel: str | None = None
    trust_stage: TrustStage = TrustStage.STRANGER


class PromptBlock(BaseModel):
    """One section of the assembled system prompt."""

    layer: str
    content: str
    priority: int


class AssembledPrompt(BaseModel):
    """Complete system prompt ready for LLM."""

    system_prompt: str
    entity_profile_id: str
    assembled_at: datetime
    block_count: int
    blocks: list[PromptBlock]


def _template_vars(
    profile: EntityProfile, message_context: MessageContext
) -> dict[str, object]:
    return {
        "entity_name": profile.entity_name,
        "entity_type": profile.entity_type,
        "product": profile.product,
        "communication": profile.communication,
        "emotional": profile.emotional,
        "relational": profile.relational,
        "knowledge": profile.knowledge,
        "forbidden_phrases": profile.forbidden_phrases,
        "forbidden_topics": profile.forbidden_topics,
        "message_category": message_context.message_category,
        "max_characters": message_context.max_characters,
        "channel": message_context.channel,
        "trust_stage": message_context.trust_stage.value,
        "trust_instructions": _TRUST_INSTRUCTIONS[message_context.trust_stage],
    }


def assemble_prompt(
    profile: EntityProfile,
    message_context: MessageContext,
    prompts_dir: Path | None = None,
) -> AssembledPrompt:
    """Assemble a complete system prompt from an EntityProfile.

    Each personality layer contributes one prompt block.
    Blocks are ordered by priority (lowest first).
    """
    directory = prompts_dir if prompts_dir is not None else _DEFAULT_PROMPTS_DIR
    env = Environment(loader=FileSystemLoader(str(directory)), autoescape=False)
    variables = _template_vars(profile, message_context)

    blocks: list[PromptBlock] = []
    for layer, template_file, priority in _BLOCK_DEFINITIONS:
        template = env.get_template(template_file)
        content = template.render(**variables).strip()
        blocks.append(PromptBlock(layer=layer, content=content, priority=priority))

    blocks.sort(key=lambda b: b.priority)
    system_prompt = "\n\n".join(b.content for b in blocks if b.content)

    return AssembledPrompt(
        system_prompt=system_prompt,
        entity_profile_id=profile.entity_id,
        assembled_at=datetime.now(tz=UTC),
        block_count=len(blocks),
        blocks=blocks,
    )
