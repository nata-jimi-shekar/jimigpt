"""Archetype configuration loading and listing."""

from pathlib import Path

import yaml
from pydantic import BaseModel, ValidationError

from src.personality.models import (
    CommunicationStyle,
    EmotionalDisposition,
    KnowledgeAwareness,
    RelationalStance,
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
