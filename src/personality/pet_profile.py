"""PetProfile — JimiGPT-specific extension of the entity-agnostic EntityProfile."""

from pydantic import Field

from src.personality.models import EntityProfile


class PetProfile(EntityProfile):
    """Extends EntityProfile with pet-specific fields for JimiGPT."""

    # Pet identity
    species: str  # "dog" | "cat" | "bird" | "rabbit" | etc.
    breed: str | None = None
    age_years: float | None = None
    size: str | None = None  # "small" | "medium" | "large"

    # Appearance extracted from photos via vision API
    appearance_notes: list[str] = Field(
        default_factory=list,
        description='e.g. ["one ear always up", "wears blue bandana"]',
    )

    # Behavioural context from user stories
    story_insights: list[str] = Field(
        default_factory=list,
        description='e.g. ["steals socks", "afraid of thunder"]',
    )

    # Owner relationship
    owner_name: str
    pet_nicknames: list[str] = Field(default_factory=list)

    # Schedule context
    feeding_times: list[str] = Field(
        default_factory=list, description='e.g. ["08:00", "18:00"]'
    )
    walk_times: list[str] = Field(
        default_factory=list, description='e.g. ["07:00", "17:30"]'
    )
    bedtime: str | None = None
