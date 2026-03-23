"""Tests for context signal models, TIME collector, and SignalCollector."""

from datetime import datetime, timezone

import pytest

from src.messaging.signals import (
    ContextSignal,
    ContextSignalBundle,
    ContextSignalSource,
    SignalCollector,
    collect_time_signals,
)

UTC = timezone.utc


# ---------------------------------------------------------------------------
# ContextSignalSource enum
# ---------------------------------------------------------------------------


def test_signal_source_has_all_phase1_sources() -> None:
    values = {s.value for s in ContextSignalSource}
    assert "time" in values
    assert "weather" in values
    assert "calendar" in values
    assert "location" in values
    assert "interaction" in values
    assert "seasonal" in values
    assert "entity_memory" in values
    assert "device" in values


def test_signal_source_user_context_foundation_present() -> None:
    """USER_CONTEXT must exist in the enum — foundation for Phase 2."""
    assert ContextSignalSource.USER_CONTEXT == "user_context"


def test_signal_source_values_are_strings() -> None:
    for source in ContextSignalSource:
        assert isinstance(source.value, str)


# ---------------------------------------------------------------------------
# ContextSignal model
# ---------------------------------------------------------------------------


def test_context_signal_constructs() -> None:
    sig = ContextSignal(
        source=ContextSignalSource.TIME,
        signal_key="time_of_day",
        signal_value="morning",
        timestamp=datetime(2026, 3, 23, 9, 0, tzinfo=UTC),
    )
    assert sig.source == ContextSignalSource.TIME
    assert sig.signal_key == "time_of_day"
    assert sig.signal_value == "morning"


def test_context_signal_confidence_defaults_to_one() -> None:
    sig = ContextSignal(
        source=ContextSignalSource.TIME,
        signal_key="day_type",
        signal_value="workday",
        timestamp=datetime(2026, 3, 23, 9, 0, tzinfo=UTC),
    )
    assert sig.confidence == 1.0


def test_context_signal_confidence_can_be_set() -> None:
    sig = ContextSignal(
        source=ContextSignalSource.WEATHER,
        signal_key="weather:condition",
        signal_value="rainy",
        confidence=0.8,
        timestamp=datetime(2026, 3, 23, 9, 0, tzinfo=UTC),
    )
    assert sig.confidence == 0.8


# ---------------------------------------------------------------------------
# ContextSignalBundle model
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_bundle() -> ContextSignalBundle:
    ts = datetime(2026, 3, 23, 9, 0, tzinfo=UTC)
    return ContextSignalBundle(
        signals=[
            ContextSignal(
                source=ContextSignalSource.TIME,
                signal_key="time_of_day",
                signal_value="morning",
                timestamp=ts,
            ),
            ContextSignal(
                source=ContextSignalSource.TIME,
                signal_key="day_type",
                signal_value="workday",
                timestamp=ts,
            ),
            ContextSignal(
                source=ContextSignalSource.INTERACTION,
                signal_key="interaction:last_response_sentiment",
                signal_value="positive",
                timestamp=ts,
            ),
        ],
        user_id="user-001",
        entity_id="entity-001",
        generated_at=ts,
    )


def test_bundle_constructs(sample_bundle: ContextSignalBundle) -> None:
    assert sample_bundle.user_id == "user-001"
    assert len(sample_bundle.signals) == 3


def test_bundle_get_signal_found(sample_bundle: ContextSignalBundle) -> None:
    sig = sample_bundle.get_signal("time_of_day")
    assert sig is not None
    assert sig.signal_value == "morning"


def test_bundle_get_signal_not_found(sample_bundle: ContextSignalBundle) -> None:
    assert sample_bundle.get_signal("nonexistent_key") is None


def test_bundle_get_signal_returns_first_match(sample_bundle: ContextSignalBundle) -> None:
    sig = sample_bundle.get_signal("time_of_day")
    assert sig is not None
    assert sig.signal_key == "time_of_day"


def test_bundle_has_signal_true_for_present_source(sample_bundle: ContextSignalBundle) -> None:
    assert sample_bundle.has_signal(ContextSignalSource.TIME) is True
    assert sample_bundle.has_signal(ContextSignalSource.INTERACTION) is True


def test_bundle_has_signal_false_for_absent_source(sample_bundle: ContextSignalBundle) -> None:
    assert sample_bundle.has_signal(ContextSignalSource.WEATHER) is False
    assert sample_bundle.has_signal(ContextSignalSource.SEASONAL) is False


def test_bundle_get_signal_empty_bundle() -> None:
    bundle = ContextSignalBundle(
        signals=[],
        user_id="u",
        entity_id="e",
        generated_at=datetime(2026, 3, 23, tzinfo=UTC),
    )
    assert bundle.get_signal("time_of_day") is None
    assert bundle.has_signal(ContextSignalSource.TIME) is False


# ---------------------------------------------------------------------------
# TIME collector — time_of_day values
# ---------------------------------------------------------------------------


def _dt(hour: int, minute: int = 0, weekday_offset: int = 0) -> datetime:
    """Monday 2026-03-23 + optional weekday offset at given hour."""
    from datetime import timedelta
    base = datetime(2026, 3, 23, hour, minute, tzinfo=UTC)  # Monday
    return base + timedelta(days=weekday_offset)


def _time_of_day(dt: datetime) -> str:
    signals = collect_time_signals("u", "e", dt)
    return next(s.signal_value for s in signals if s.signal_key == "time_of_day")


def test_time_collector_late_night_midnight() -> None:
    assert _time_of_day(_dt(0)) == "late_night"


def test_time_collector_late_night_before_five() -> None:
    assert _time_of_day(_dt(4, 59)) == "late_night"


def test_time_collector_early_morning() -> None:
    assert _time_of_day(_dt(5)) == "early_morning"
    assert _time_of_day(_dt(7, 59)) == "early_morning"


def test_time_collector_morning() -> None:
    assert _time_of_day(_dt(8)) == "morning"
    assert _time_of_day(_dt(11, 59)) == "morning"


def test_time_collector_midday() -> None:
    assert _time_of_day(_dt(12)) == "midday"
    assert _time_of_day(_dt(13, 59)) == "midday"


def test_time_collector_afternoon() -> None:
    assert _time_of_day(_dt(14)) == "afternoon"
    assert _time_of_day(_dt(17, 59)) == "afternoon"


def test_time_collector_evening() -> None:
    assert _time_of_day(_dt(18)) == "evening"
    assert _time_of_day(_dt(20, 59)) == "evening"


def test_time_collector_night() -> None:
    assert _time_of_day(_dt(21)) == "night"
    assert _time_of_day(_dt(23, 59)) == "night"


# ---------------------------------------------------------------------------
# TIME collector — day_of_week and day_type
# ---------------------------------------------------------------------------


def _day_of_week(dt: datetime) -> str:
    signals = collect_time_signals("u", "e", dt)
    return next(s.signal_value for s in signals if s.signal_key == "day_of_week")


def _day_type(dt: datetime) -> str:
    signals = collect_time_signals("u", "e", dt)
    return next(s.signal_value for s in signals if s.signal_key == "day_type")


def test_time_collector_monday() -> None:
    assert _day_of_week(_dt(9, weekday_offset=0)) == "monday"
    assert _day_type(_dt(9, weekday_offset=0)) == "workday"


def test_time_collector_tuesday() -> None:
    assert _day_of_week(_dt(9, weekday_offset=1)) == "tuesday"


def test_time_collector_wednesday() -> None:
    assert _day_of_week(_dt(9, weekday_offset=2)) == "wednesday"


def test_time_collector_thursday() -> None:
    assert _day_of_week(_dt(9, weekday_offset=3)) == "thursday"


def test_time_collector_friday() -> None:
    dt = _dt(9, weekday_offset=4)
    assert _day_of_week(dt) == "friday"
    assert _day_type(dt) == "workday"


def test_time_collector_saturday() -> None:
    dt = _dt(9, weekday_offset=5)
    assert _day_of_week(dt) == "saturday"
    assert _day_type(dt) == "weekend"


def test_time_collector_sunday() -> None:
    dt = _dt(9, weekday_offset=6)
    assert _day_of_week(dt) == "sunday"
    assert _day_type(dt) == "weekend"


# ---------------------------------------------------------------------------
# TIME collector — signal structure
# ---------------------------------------------------------------------------


def test_time_collector_returns_exactly_three_signals() -> None:
    signals = collect_time_signals("u", "e", _dt(9))
    assert len(signals) == 3


def test_time_collector_all_signals_have_time_source() -> None:
    signals = collect_time_signals("u", "e", _dt(9))
    assert all(s.source == ContextSignalSource.TIME for s in signals)


def test_time_collector_all_signals_confidence_one() -> None:
    signals = collect_time_signals("u", "e", _dt(9))
    assert all(s.confidence == 1.0 for s in signals)


def test_time_collector_signal_keys_present() -> None:
    signals = collect_time_signals("u", "e", _dt(9))
    keys = {s.signal_key for s in signals}
    assert keys == {"time_of_day", "day_of_week", "day_type"}


# ---------------------------------------------------------------------------
# SignalCollector — empty / missing collectors
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_collector_no_collectors_returns_empty_bundle() -> None:
    collector = SignalCollector()
    bundle = await collector.collect("u1", "e1", _dt(9))
    assert isinstance(bundle, ContextSignalBundle)
    assert bundle.signals == []
    assert bundle.user_id == "u1"
    assert bundle.entity_id == "e1"


@pytest.mark.asyncio
async def test_collector_with_time_collector_returns_time_signals() -> None:
    collector = SignalCollector()
    collector.register_collector(ContextSignalSource.TIME, collect_time_signals)
    bundle = await collector.collect("u1", "e1", _dt(9))
    assert bundle.has_signal(ContextSignalSource.TIME)
    assert len(bundle.signals) == 3


@pytest.mark.asyncio
async def test_collector_missing_source_produces_no_error() -> None:
    """Requesting collection without a registered source just produces no signals."""
    collector = SignalCollector()
    # Only TIME registered — INTERACTION missing — no error
    collector.register_collector(ContextSignalSource.TIME, collect_time_signals)
    bundle = await collector.collect("u1", "e1", _dt(9))
    assert not bundle.has_signal(ContextSignalSource.INTERACTION)


@pytest.mark.asyncio
async def test_collector_failing_collector_skipped_gracefully() -> None:
    """A collector that raises does not crash collect() — other signals still returned."""

    def _bad_collector(user_id: str, entity_id: str, current_time: datetime) -> list:
        raise RuntimeError("simulated failure")

    collector = SignalCollector()
    collector.register_collector(ContextSignalSource.WEATHER, _bad_collector)
    collector.register_collector(ContextSignalSource.TIME, collect_time_signals)

    bundle = await collector.collect("u1", "e1", _dt(9))
    # WEATHER failed — no WEATHER signals
    assert not bundle.has_signal(ContextSignalSource.WEATHER)
    # TIME still collected
    assert bundle.has_signal(ContextSignalSource.TIME)


@pytest.mark.asyncio
async def test_collector_generated_at_matches_current_time() -> None:
    collector = SignalCollector()
    now = _dt(9)
    bundle = await collector.collect("u1", "e1", now)
    assert bundle.generated_at == now


# ---------------------------------------------------------------------------
# Foundation: USER_CONTEXT — no collector in Phase 1, enum value exists
# ---------------------------------------------------------------------------


def test_user_context_in_enum() -> None:
    assert ContextSignalSource.USER_CONTEXT in ContextSignalSource


@pytest.mark.asyncio
async def test_no_user_context_collector_registered_no_error() -> None:
    """Phase 1: USER_CONTEXT in enum but no collector — collect() works fine."""
    collector = SignalCollector()
    collector.register_collector(ContextSignalSource.TIME, collect_time_signals)
    bundle = await collector.collect("u1", "e1", _dt(9))
    assert not bundle.has_signal(ContextSignalSource.USER_CONTEXT)


@pytest.mark.asyncio
async def test_can_register_user_context_collector() -> None:
    """USER_CONTEXT collector can be registered without error (Phase 2 readiness)."""

    def _stub(user_id: str, entity_id: str, current_time: datetime) -> list:
        return []

    collector = SignalCollector()
    collector.register_collector(ContextSignalSource.USER_CONTEXT, _stub)
    bundle = await collector.collect("u1", "e1", _dt(9))
    assert bundle.user_id == "u1"
