# Fix Later Backlog

Non-blocking issues captured from code reviews. Address before the relevant
Phase 2 work begins or MVP launch. Review weekly to check if any items have
become blocking.

---

## Open Items

### 1. SignalCollector.collect() does not support async collectors

**Feature:** F02 | **Source:** Codex F02 review, Important Issue #1
**File:** src/messaging/signals.py:97
**Priority:** Medium — fix before Phase 2 collectors

SignalCollector.collect() is async but calls collectors synchronously via
`collector_fn(...)`. If a future collector returns a coroutine, it will be
silently dropped (unawaited coroutine warning) and the source will be skipped.

All three current collectors (TIME, INTERACTION, SEASONAL) are synchronous, so
this cannot manifest today. Fix before implementing WEATHER or CALENDAR
collectors in Phase 2, which will hit external APIs and must be async.

**Fix:** Check if the collector return is a coroutine and await it, or use
`inspect.iscoroutinefunction()` at registration time to dispatch correctly.

---

### 2. Overnight scheduling windows are unsupported

**Feature:** F02 | **Source:** Codex F02 review, Important Issue #3
**Files:** src/messaging/time_trigger.py:50, src/messaging/random_trigger.py:47
**Priority:** Low — no current config uses overnight windows

Window checks use `start <= local_time < end` which fails for cross-midnight
windows like 22:00-07:00. Such windows can never match. No current trigger
config uses overnight windows — all windows are daytime (e.g., 09:00-21:00).

**Fix:** When `start > end`, use `local_time >= start or local_time < end`.
Address before allowing user-configurable scheduling or if any product adds
overnight-active entities.

---

### 3. Pipeline integration test should pass real intent_weights from archetype

**Feature:** F02 | **Source:** Codex F02 review, Important Issue #4 (partial)
**File:** tests/messaging/test_pipeline_integration.py:104
**Priority:** Low — unit tests cover the weights-dependent paths

The pipeline integration test doesn't pass `intent_weights=archetype.intent_weights`
to compose(). It uses the balanced fallback. The greeting path (exercised by the
integration test) doesn't use weights, so this is fine. The weights-dependent
paths (personality_moment, anniversary) are covered by unit tests with correct
intent-keyed weights.

**Fix:** Pass `intent_weights=archetype.intent_weights` to compose() in the
integration test fixtures. Do next time the integration test is touched.

---

### 4. Tone rule dimension names are not validated at load time

**Feature:** F02 | **Source:** Codex F02 review, Observations (implicit)
**Files:** config/tone_rules.yaml, src/messaging/tone.py
**Priority:** Low — current rules are correct, no user-facing editor yet

If a tone rule references a non-existent dimension (e.g., typo "enrgy" instead
of "energy"), calibrate_tone() silently skips it. No load-time validation that
rule dimensions match ToneSpectrum fields.

**Fix:** Validate dimension names against ToneSpectrum model_fields at YAML
load time. Address when tone rules become user-configurable.

---

## Completed Items

| # | Feature | Issue | Resolution | Date |
|---|---------|-------|-----------|------|
| | | | | |
