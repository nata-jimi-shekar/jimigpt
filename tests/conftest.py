"""Shared test fixtures for JimiGPT."""

import pytest


@pytest.fixture
def sample_communication_style() -> dict:
    """Sample communication style config for testing."""
    return {
        "sentence_length": "short",
        "energy_level": "high",
        "emoji_usage": "heavy",
        "punctuation_style": "excited_exclamations",
        "vocabulary_level": "simple",
        "quirks": ["uses ALL CAPS for excitement"],
    }


@pytest.fixture
def sample_emotional_disposition() -> dict:
    """Sample emotional disposition config for testing."""
    return {
        "baseline_mood": "playful",
        "emotional_range": "wide",
        "need_expression": "dramatic",
        "humor_style": "silly",
    }


@pytest.fixture
def sample_relational_stance() -> dict:
    """Sample relational stance config for testing."""
    return {
        "attachment_style": "clingy",
        "initiative_style": "proactive",
        "boundary_respect": "moderate",
        "warmth_level": "intense",
    }


@pytest.fixture
def sample_knowledge_awareness() -> dict:
    """Sample knowledge awareness config for testing."""
    return {
        "domain_knowledge": ["food and treats", "toys and play"],
        "user_context_fields": ["owner_schedule", "feeding_times"],
        "temporal_awareness": True,
        "memory_references": True,
    }
