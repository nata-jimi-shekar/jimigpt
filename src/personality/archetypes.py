"""Archetype configuration loading and listing."""

import uuid
from pathlib import Path

import yaml
from pydantic import BaseModel, Field, ValidationError

from src.personality.models import (
    CommunicationStyle,
    EmotionalDisposition,
    EntityProfile,
    KnowledgeAwareness,
    RelationalStance,
    ToneSpectrum,
)

_DEFAULT_CONFIG_DIR = Path(__file__).parent.parent.parent / "config" / "archetypes"


class ArchetypeConfig(BaseModel):
    """Maps an archetype YAML file to a validated Python model."""

    id: str
    name: str
    description: str
    communication: CommunicationStyle
    emotional: EmotionalDisposition
    relational: RelationalStance
    knowledge: KnowledgeAwareness
    forbidden_phrases: list[str] = []
    forbidden_topics: list[str] = []
    tone_defaults: ToneSpectrum | None = None
    intent_weights: dict[str, float] = Field(default_factory=dict)


def load_archetype(path: Path) -> ArchetypeConfig:
    """Load and validate an archetype from a YAML file.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the YAML is malformed or fails schema validation.
    """
    if not path.exists():
        raise FileNotFoundError(f"Archetype file not found: {path}")

    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ValueError(f"Invalid YAML in {path}: {exc}") from exc

    try:
        return ArchetypeConfig(**raw)
    except (ValidationError, TypeError) as exc:
        raise ValueError(f"Invalid archetype schema in {path}: {exc}") from exc


def list_archetypes(
    product: str,
    config_dir: Path | None = None,
) -> list[ArchetypeConfig]:
    """Return all valid archetypes for a product.

    Scans `config_dir/{product}/*.yaml` and loads each file.
    Files that fail validation are silently skipped.
    Returns an empty list if the product directory does not exist.
    """
    base = config_dir if config_dir is not None else _DEFAULT_CONFIG_DIR
    product_dir = base / product

    if not product_dir.exists():
        return []

    archetypes = []
    for yaml_file in sorted(product_dir.glob("*.yaml")):
        try:
            archetypes.append(load_archetype(yaml_file))
        except (FileNotFoundError, ValueError):
            continue

    return archetypes


def _merge_lists(primary: list[str], secondary: list[str]) -> list[str]:
    """Merge two lists, preserving primary order and deduplicating."""
    seen = set(primary)
    return primary + [item for item in secondary if item not in seen]


def blend_archetypes(
    primary: ArchetypeConfig,
    secondary: ArchetypeConfig | None,
    weights: dict[str, float],
) -> EntityProfile:
    """Blend two archetypes into a single EntityProfile.

    Primary archetype dominates when its weight is >= secondary's weight.
    List fields (quirks, domain_knowledge, etc.) are merged from both.
    Forbidden content is unioned from both.

    Raises:
        ValueError: If weights do not sum to 1.0.
    """
    total = sum(weights.values())
    if abs(total - 1.0) > 1e-9:
        raise ValueError(f"Weights must sum to 1.0, got {total:.6f}")

    product = primary.id.split(":")[0]

    if secondary is None:
        return EntityProfile(
            entity_id=str(uuid.uuid4()),
            entity_name=primary.name,
            entity_type="companion",
            product=product,
            communication=primary.communication,
            emotional=primary.emotional,
            relational=primary.relational,
            knowledge=primary.knowledge,
            primary_archetype=primary.id,
            archetype_weights=weights,
            forbidden_phrases=list(primary.forbidden_phrases),
            forbidden_topics=list(primary.forbidden_topics),
        )

    p_weight = weights.get(primary.id, 0.5)
    s_weight = weights.get(secondary.id, 0.5)
    use_primary = p_weight >= s_weight

    dominant_comm = primary.communication if use_primary else secondary.communication
    dominant_emot = primary.emotional if use_primary else secondary.emotional
    dominant_rela = primary.relational if use_primary else secondary.relational
    dominant_know = primary.knowledge if use_primary else secondary.knowledge

    communication = CommunicationStyle(
        sentence_length=dominant_comm.sentence_length,
        energy_level=dominant_comm.energy_level,
        emoji_usage=dominant_comm.emoji_usage,
        punctuation_style=dominant_comm.punctuation_style,
        vocabulary_level=dominant_comm.vocabulary_level,
        quirks=_merge_lists(primary.communication.quirks, secondary.communication.quirks),
    )

    knowledge = KnowledgeAwareness(
        domain_knowledge=_merge_lists(
            primary.knowledge.domain_knowledge,
            secondary.knowledge.domain_knowledge,
        ),
        user_context_fields=_merge_lists(
            primary.knowledge.user_context_fields,
            secondary.knowledge.user_context_fields,
        ),
        temporal_awareness=dominant_know.temporal_awareness,
        memory_references=dominant_know.memory_references,
    )

    return EntityProfile(
        entity_id=str(uuid.uuid4()),
        entity_name=primary.name,
        entity_type="companion",
        product=product,
        communication=communication,
        emotional=dominant_emot,
        relational=dominant_rela,
        knowledge=knowledge,
        primary_archetype=primary.id,
        secondary_archetype=secondary.id,
        archetype_weights=weights,
        forbidden_phrases=_merge_lists(primary.forbidden_phrases, secondary.forbidden_phrases),
        forbidden_topics=_merge_lists(primary.forbidden_topics, secondary.forbidden_topics),
    )
