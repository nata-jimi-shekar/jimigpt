"""Shared enums for the personality engine."""

from enum import StrEnum


class EnergyLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VARIABLE = "variable"
