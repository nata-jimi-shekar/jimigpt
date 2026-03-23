"""Tests for INTERACTION and SEASONAL signal collectors."""

from datetime import datetime, timezone

import pytest

from src.messaging.signals import (
    ContextSignal,
    ContextSignalBundle,
    ContextSignalSource,
    SignalCollector,
    collect_time_signals,
)
from src.messaging.interaction_collector import InteractionData, collect_interaction_signals
from src.messaging.seasonal_collector import SeasonalData, collect_seasonal_signals

UTC = timezone.utc


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _dt(year: int = 2026, month: int = 3, day: int = 23, hour: int = 10) -> datetime:
    return datetime(year, month, day, hour, 0, tzinfo=UTC)


# ---------------------------------------------------------------------------
# InteractionData model
# ---------------------------------------------------------------------------


def test_interaction_data_constructs() -> None:
    data = InteractionData(
        last_response_sentiment="positive",
        days_since_last_reply=1,
        reply_pattern="frequent",
        recent_reaction="heart",
    )
    assert data.last_response_sentiment == "positive"
    assert data.days_since_last_reply == 1
    assert data.reply_pattern == "frequent"
    assert data.recent_reaction == "heart"


def test_interaction_data_context_tags_defaults_to_empty_list() -> None:
    """Foundation: last_reply_context_tags must default to empty list."""
    data = InteractionData(
        last_response_sentiment="neutral",
        days_since_last_reply=3,
        reply_pattern="occasional",
        recent_reaction=None,
    )
    assert data.last_reply_context_tags == []


def test_interaction_data_context_tags_can_be_set() -> None:
    """Foundation: last_reply_context_tags accepts values for Phase 2 readiness."""
    data = InteractionData(
        last_response_sentiment="positive",
        days_since_last_reply=0,
        reply_pattern="frequent",
        recent_reaction=None,
        last_reply_context_tags=["park", "outdoor", "excited"],
    )
    assert data.last_reply_context_tags == ["park", "outdoor", "excited"]


def test_interaction_data_recent_reaction_optional() -> None:
    data = InteractionData(
        last_response_sentiment="neutral",
        days_since_last_reply=5,
        reply_pattern="rare",
        recent_reaction=None,
    )
    assert data.recent_reaction is None


# ---------------------------------------------------------------------------
# collect_interaction_signals — signal keys
# ---------------------------------------------------------------------------


def _interaction_data_standard() -> InteractionData:
    return InteractionData(
        last_response_sentiment="positive",
        days_since_last_reply=2,
        reply_pattern="frequent",
        recent_reaction="heart",
    )


def test_interaction_signals_returns_four_signals() -> None:
    signals = collect_interaction_signals("u", "e", _dt(), _interaction_data_standard())
    assert len(signals) == 4


def test_interaction_signals_all_have_interaction_source() -> None:
    signals = collect_interaction_signals("u", "e", _dt(), _interaction_data_standard())
    assert all(s.source == ContextSignalSource.INTERACTION for s in signals)


def test_interaction_signals_keys_present() -> None:
    signals = collect_interaction_signals("u", "e", _dt(), _interaction_data_standard())
    keys = {s.signal_key for s in signals}
    assert keys == {
        "interaction:last_response_sentiment",
        "interaction:days_since_last_reply",
        "interaction:reply_pattern",
        "interaction:recent_reaction",
    }


def test_interaction_signals_sentiment_value() -> None:
    signals = collect_interaction_signals("u", "e", _dt(), _interaction_data_standard())
    sig = next(s for s in signals if s.signal_key == "interaction:last_response_sentiment")
    assert sig.signal_value == "positive"


def test_interaction_signals_days_since_last_reply_value() -> None:
    signals = collect_interaction_signals("u", "e", _dt(), _interaction_data_standard())
    sig = next(s for s in signals if s.signal_key == "interaction:days_since_last_reply")
    assert sig.signal_value == "2"


def test_interaction_signals_reply_pattern_value() -> None:
    signals = collect_interaction_signals("u", "e", _dt(), _interaction_data_standard())
    sig = next(s for s in signals if s.signal_key == "interaction:reply_pattern")
    assert sig.signal_value == "frequent"


def test_interaction_signals_recent_reaction_value() -> None:
    signals = collect_interaction_signals("u", "e", _dt(), _interaction_data_standard())
    sig = next(s for s in signals if s.signal_key == "interaction:recent_reaction")
    assert sig.signal_value == "heart"


def test_interaction_signals_recent_reaction_none_uses_empty_string() -> None:
    data = InteractionData(
        last_response_sentiment="neutral",
        days_since_last_reply=0,
        reply_pattern="silent",
        recent_reaction=None,
    )
    signals = collect_interaction_signals("u", "e", _dt(), data)
    sig = next(s for s in signals if s.signal_key == "interaction:recent_reaction")
    assert sig.signal_value == ""


def test_interaction_signals_all_confidence_one() -> None:
    signals = collect_interaction_signals("u", "e", _dt(), _interaction_data_standard())
    assert all(s.confidence == 1.0 for s in signals)


# ---------------------------------------------------------------------------
# collect_interaction_signals — reply_pattern values
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("pattern", ["frequent", "occasional", "rare", "silent"])
def test_interaction_signals_valid_reply_patterns(pattern: str) -> None:
    data = InteractionData(
        last_response_sentiment="neutral",
        days_since_last_reply=1,
        reply_pattern=pattern,
        recent_reaction=None,
    )
    signals = collect_interaction_signals("u", "e", _dt(), data)
    sig = next(s for s in signals if s.signal_key == "interaction:reply_pattern")
    assert sig.signal_value == pattern


# ---------------------------------------------------------------------------
# Foundation: context_tags in InteractionData does not affect signal count
# ---------------------------------------------------------------------------


def test_interaction_signals_context_tags_does_not_add_extra_signals() -> None:
    """Foundation: context_tags is stored on the input model, not emitted as a signal."""
    data = InteractionData(
        last_response_sentiment="positive",
        days_since_last_reply=1,
        reply_pattern="frequent",
        recent_reaction="laugh",
        last_reply_context_tags=["park", "walk"],
    )
    signals = collect_interaction_signals("u", "e", _dt(), data)
    assert len(signals) == 4  # same as without context_tags


# ---------------------------------------------------------------------------
# SeasonalData model
# ---------------------------------------------------------------------------


def test_seasonal_data_constructs() -> None:
    data = SeasonalData(entity_created_at=datetime(2024, 3, 23, tzinfo=UTC))
    assert data.entity_created_at == datetime(2024, 3, 23, tzinfo=UTC)


# ---------------------------------------------------------------------------
# collect_seasonal_signals — signal keys
# ---------------------------------------------------------------------------


def test_seasonal_signals_returns_two_signals() -> None:
    created = datetime(2024, 6, 15, tzinfo=UTC)
    signals = collect_seasonal_signals("u", "e", _dt(), SeasonalData(entity_created_at=created))
    assert len(signals) == 2


def test_seasonal_signals_all_have_seasonal_source() -> None:
    created = datetime(2024, 6, 15, tzinfo=UTC)
    signals = collect_seasonal_signals("u", "e", _dt(), SeasonalData(entity_created_at=created))
    assert all(s.source == ContextSignalSource.SEASONAL for s in signals)


def test_seasonal_signals_keys_present() -> None:
    created = datetime(2024, 6, 15, tzinfo=UTC)
    signals = collect_seasonal_signals("u", "e", _dt(), SeasonalData(entity_created_at=created))
    keys = {s.signal_key for s in signals}
    assert keys == {"seasonal:season", "seasonal:entity_anniversary"}


def test_seasonal_signals_all_confidence_one() -> None:
    created = datetime(2024, 6, 15, tzinfo=UTC)
    signals = collect_seasonal_signals("u", "e", _dt(), SeasonalData(entity_created_at=created))
    assert all(s.confidence == 1.0 for s in signals)


# ---------------------------------------------------------------------------
# collect_seasonal_signals — season values (Northern Hemisphere)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "month, expected_season",
    [
        (1, "winter"),
        (2, "winter"),
        (3, "spring"),
        (4, "spring"),
        (5, "spring"),
        (6, "summer"),
        (7, "summer"),
        (8, "summer"),
        (9, "fall"),
        (10, "fall"),
        (11, "fall"),
        (12, "winter"),
    ],
)
def test_seasonal_signals_season_by_month(month: int, expected_season: str) -> None:
    now = datetime(2026, month, 15, 10, 0, tzinfo=UTC)
    created = datetime(2024, 6, 15, tzinfo=UTC)
    signals = collect_seasonal_signals("u", "e", now, SeasonalData(entity_created_at=created))
    sig = next(s for s in signals if s.signal_key == "seasonal:season")
    assert sig.signal_value == expected_season


# ---------------------------------------------------------------------------
# collect_seasonal_signals — entity_anniversary
# ---------------------------------------------------------------------------


def test_seasonal_anniversary_on_exact_anniversary() -> None:
    """Entity created exactly 2 years ago today → anniversary=true."""
    created = datetime(2024, 3, 23, tzinfo=UTC)
    now = datetime(2026, 3, 23, 10, 0, tzinfo=UTC)
    signals = collect_seasonal_signals("u", "e", now, SeasonalData(entity_created_at=created))
    sig = next(s for s in signals if s.signal_key == "seasonal:entity_anniversary")
    assert sig.signal_value == "true"


def test_seasonal_anniversary_not_on_anniversary() -> None:
    """Created on June 15 — checked on March 23 → anniversary=false."""
    created = datetime(2024, 6, 15, tzinfo=UTC)
    now = datetime(2026, 3, 23, 10, 0, tzinfo=UTC)
    signals = collect_seasonal_signals("u", "e", now, SeasonalData(entity_created_at=created))
    sig = next(s for s in signals if s.signal_key == "seasonal:entity_anniversary")
    assert sig.signal_value == "false"


def test_seasonal_anniversary_first_year_not_triggered() -> None:
    """Entity created less than a year ago → anniversary=false."""
    created = datetime(2025, 12, 1, tzinfo=UTC)
    now = datetime(2026, 3, 23, 10, 0, tzinfo=UTC)
    signals = collect_seasonal_signals("u", "e", now, SeasonalData(entity_created_at=created))
    sig = next(s for s in signals if s.signal_key == "seasonal:entity_anniversary")
    assert sig.signal_value == "false"


def test_seasonal_anniversary_one_year_old_today() -> None:
    """Entity created exactly 1 year ago → anniversary=true."""
    created = datetime(2025, 3, 23, tzinfo=UTC)
    now = datetime(2026, 3, 23, 10, 0, tzinfo=UTC)
    signals = collect_seasonal_signals("u", "e", now, SeasonalData(entity_created_at=created))
    sig = next(s for s in signals if s.signal_key == "seasonal:entity_anniversary")
    assert sig.signal_value == "true"


# ---------------------------------------------------------------------------
# Integration with SignalCollector
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_signal_collector_with_interaction_and_seasonal() -> None:
    from functools import partial

    interaction_data = _interaction_data_standard()
    seasonal_data = SeasonalData(entity_created_at=datetime(2024, 3, 23, tzinfo=UTC))

    collector = SignalCollector()
    collector.register_collector(ContextSignalSource.TIME, collect_time_signals)
    collector.register_collector(
        ContextSignalSource.INTERACTION,
        partial(collect_interaction_signals, interaction_data=interaction_data),
    )
    collector.register_collector(
        ContextSignalSource.SEASONAL,
        partial(collect_seasonal_signals, seasonal_data=seasonal_data),
    )

    now = datetime(2026, 3, 23, 10, 0, tzinfo=UTC)
    bundle = await collector.collect("u1", "e1", now)

    assert bundle.has_signal(ContextSignalSource.TIME)
    assert bundle.has_signal(ContextSignalSource.INTERACTION)
    assert bundle.has_signal(ContextSignalSource.SEASONAL)
    assert len(bundle.signals) == 9  # 3 TIME + 4 INTERACTION + 2 SEASONAL


@pytest.mark.asyncio
async def test_signal_collector_context_tags_in_bundle_via_interaction() -> None:
    """Foundation: context_tags on InteractionData flows through correctly."""
    from functools import partial

    data = InteractionData(
        last_response_sentiment="positive",
        days_since_last_reply=1,
        reply_pattern="frequent",
        recent_reaction=None,
        last_reply_context_tags=["park", "walk", "happy"],
    )

    collector = SignalCollector()
    collector.register_collector(
        ContextSignalSource.INTERACTION,
        partial(collect_interaction_signals, interaction_data=data),
    )

    bundle = await collector.collect("u1", "e1", _dt())
    assert bundle.has_signal(ContextSignalSource.INTERACTION)
    # context_tags don't become signals — they stay on the input model
    assert len(bundle.signals) == 4
