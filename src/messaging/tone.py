"""Tone calibration engine.

Starts from archetype ToneSpectrum defaults and applies signal-driven
adjustments loaded from config/tone_rules.yaml.  All dimensions are
clamped to [0.0, 1.0] after each rule application.

Foundation (Phase 2):
  - life_contexts param accepted but ignored in Phase 1.
    In Phase 2, active life contexts apply tone overrides
    (e.g., "user_sick" caps energy at 0.4, raises warmth).
"""

from __future__ import annotations

import copy
from pathlib import Path

import yaml
from pydantic import BaseModel, Field

from src.messaging.intent import TrustStage
from src.messaging.signals import ContextSignalBundle
from src.personality.models import ToneSpectrum

_RULES_PATH = Path(__file__).parent.parent.parent / "config" / "tone_rules.yaml"

_TONE_DIMENSIONS = {"warmth", "humor", "directness", "gravity", "energy", "vulnerability"}


class ToneRule(BaseModel):
    """A single signal-driven tone adjustment rule."""

    signal: str
    dimension: str
    adjustment: float = Field(ge=-0.5, le=0.5)
    reason: str


class ToneCalibrationResult(BaseModel):
    """Output of calibrate_tone: calibrated spectrum + audit trail."""

    tone: ToneSpectrum
    adjustments_applied: list[ToneRule]


def calibrate_tone(
    archetype_defaults: ToneSpectrum,
    signals: ContextSignalBundle,
    trust_stage: TrustStage,
    *,
    life_contexts: list[str] | None = None,  # Foundation: Phase 2 overrides
) -> ToneCalibrationResult:
    """Return a calibrated ToneSpectrum adjusted for current context.

    1. Build the active signal set from the bundle + trust stage.
    2. Load tone rules from config/tone_rules.yaml.
    3. Apply every matching rule, clamping each dimension after each step.
    4. Return calibrated tone + list of applied rules.
    """
    active_signals = _build_signal_set(signals, trust_stage)
    all_rules = _load_rules()

    dims = {
        "warmth": archetype_defaults.warmth,
        "humor": archetype_defaults.humor,
        "directness": archetype_defaults.directness,
        "gravity": archetype_defaults.gravity,
        "energy": archetype_defaults.energy,
        "vulnerability": archetype_defaults.vulnerability,
    }
    applied: list[ToneRule] = []

    for rule in all_rules:
        if rule.signal in active_signals:
            dims[rule.dimension] = _clamp(dims[rule.dimension] + rule.adjustment)
            applied.append(rule)

    return ToneCalibrationResult(
        tone=ToneSpectrum(**dims),
        adjustments_applied=applied,
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _build_signal_set(bundle: ContextSignalBundle, trust_stage: TrustStage) -> set[str]:
    """Convert bundle signals + trust stage into matchable key:value strings."""
    active: set[str] = set()
    for sig in bundle.signals:
        active.add(f"{sig.signal_key}:{sig.signal_value}")
    active.add(f"trust_stage:{trust_stage.value}")
    return active


def _load_rules() -> list[ToneRule]:
    """Load and parse tone_rules.yaml. Returns empty list on missing file."""
    if not _RULES_PATH.exists():
        return []
    with _RULES_PATH.open(encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    return [ToneRule(**r) for r in (data.get("tone_rules") or [])]


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))
