"""Shared messaging models — intent, tone, composition."""

from enum import Enum


class MessageIntent(str, Enum):
    """Universal emotional intentions — what the message is trying to DO."""

    # Connection intents
    AFFIRM = "affirm"
    ACCOMPANY = "accompany"
    CELEBRATE = "celebrate"

    # Support intents
    COMFORT = "comfort"
    GROUND = "ground"
    ENCOURAGE = "encourage"

    # Engagement intents
    ENERGIZE = "energize"
    SURPRISE = "surprise"
    INVITE = "invite"

    # Practical intents
    REMIND = "remind"
    NUDGE = "nudge"
    REFLECT = "reflect"

    # Boundary intents
    DEFER = "defer"
    RESPECT = "respect"
