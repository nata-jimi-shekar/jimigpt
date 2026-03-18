"""Four-layer personality Pydantic models — entity-agnostic core."""

from pydantic import BaseModel, Field

from src.personality.enums import EnergyLevel


class CommunicationStyle(BaseModel):
    """HOW the entity talks."""

    sentence_length: str = Field(description="short | medium | long")
    energy_level: EnergyLevel
    emoji_usage: str = Field(description="none | minimal | moderate | heavy")
    punctuation_style: str = Field(
        description="calm_periods | excited_exclamations | mixed"
    )
    vocabulary_level: str = Field(
        description="simple | moderate | sophisticated"
    )
    quirks: list[str] = Field(
        default_factory=list, description="Unique speech patterns"
    )


class EmotionalDisposition(BaseModel):
    """WHAT the entity's baseline mood is."""

    baseline_mood: str = Field(
        description="cheerful | calm | anxious | intense | playful"
    )
    emotional_range: str = Field(description="narrow | moderate | wide")
    need_expression: str = Field(
        description="dramatic | matter_of_fact | subtle | whiny"
    )
    humor_style: str = Field(description="none | dry | silly | sarcastic | warm")


class RelationalStance(BaseModel):
    """WHY the entity reaches out and HOW it relates."""

    attachment_style: str = Field(
        description="clingy | balanced | independent | protective"
    )
    initiative_style: str = Field(
        description="proactive | responsive | mixed"
    )
    boundary_respect: str = Field(
        description="high | moderate — how much it respects user silence"
    )
    warmth_level: str = Field(description="cool | warm | intense")


class KnowledgeAwareness(BaseModel):
    """WHAT the entity knows about and references."""

    domain_knowledge: list[str] = Field(
        description="Topics this entity can reference"
    )
    user_context_fields: list[str] = Field(
        description="What it tracks about the user"
    )
    temporal_awareness: bool = Field(
        description="Knows time of day, day of week, seasons"
    )
    memory_references: bool = Field(
        description="References past interactions naturally"
    )


class EntityProfile(BaseModel):
    """Complete personality profile — universal across all products."""

    entity_id: str
    entity_name: str
    entity_type: str = Field(description="pet | companion | coach | ally")
    product: str = Field(description="jimigpt | neuroamigo | etc")

    communication: CommunicationStyle
    emotional: EmotionalDisposition
    relational: RelationalStance
    knowledge: KnowledgeAwareness

    # Archetype metadata
    primary_archetype: str
    secondary_archetype: str | None = None
    archetype_weights: dict[str, float] = Field(default_factory=dict)

    # Anti-patterns: things this entity should NEVER say
    forbidden_phrases: list[str] = Field(default_factory=list)
    forbidden_topics: list[str] = Field(default_factory=list)
