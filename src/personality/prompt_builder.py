"""Personality-to-prompt translator using Jinja2 templates."""

from datetime import datetime, timezone
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from pydantic import BaseModel

from src.personality.models import EntityProfile

_DEFAULT_PROMPTS_DIR = Path(__file__).parent.parent.parent / "config" / "prompts"

_BLOCK_DEFINITIONS: list[tuple[str, str, int]] = [
    ("identity", "base_identity.j2", 1),
    ("communication", "communication_style.j2", 2),
    ("emotional", "emotional_disposition.j2", 3),
    ("relational", "relational_stance.j2", 4),
    ("knowledge", "knowledge_awareness.j2", 5),
    ("anti_patterns", "anti_patterns.j2", 6),
    ("message_directive", "message_directive.j2", 7),
]


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
    profile: EntityProfile, message_context: dict[str, object]
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
        "message_category": message_context.get("message_category", "general"),
        "max_characters": message_context.get("max_characters", 160),
        "channel": message_context.get("channel"),
    }


def assemble_prompt(
    profile: EntityProfile,
    message_context: dict[str, object],
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
        assembled_at=datetime.now(tz=timezone.utc),
        block_count=len(blocks),
        blocks=blocks,
    )
