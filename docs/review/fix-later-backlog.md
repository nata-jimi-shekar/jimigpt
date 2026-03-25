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

## Watch Items (Not Bugs — Monitor for Future Action)

### 5. Circular import between generator ↔ quality ↔ generation_log

**Feature:** R01 | **Source:** Codex R01 review, Observation
**Files:** src/messaging/generator.py, src/messaging/quality.py, src/shared/generation_log.py
**Priority:** Low — working correctly, cosmetic concern

TYPE_CHECKING + lazy import is pragmatic. A structural fix (extracting
GeneratedMessage to its own module) would be cleaner but requires touching
many test files. Consider during a future refactor if the cycle grows.

---

### 6. Quality gate hardcoded in generator.py

**Feature:** R01 | **Source:** Codex R01 review, Observation
**File:** src/messaging/generator.py:125
**Priority:** Medium — address in F03

Uses 4 fixed checks (LENGTH, SAFETY, CHARACTER_CONSISTENCY, FORBIDDEN_PHRASES).
Should become configurable in F03 when delivery orchestration is built.

---

### 7. Fingerprint word sets are English-only and pet-centric

**Feature:** R01 | **Source:** Codex R01 review, Observation
**Files:** src/shared/fingerprint.py (_WARM_WORDS, _HUMOR_MARKERS)
**Priority:** Low — acceptable for Phase 1 / JimiGPT

Move to config/YAML in Phase 2 for entity-agnostic support (NeuroAmigo).

---

### 8. log_generation is synchronous — may slow generation at scale

**Feature:** R01 | **Source:** Opus R01 review, Important #2
**File:** src/messaging/generator.py:145
**Priority:** Low — in-memory store is fast; only matters with DB persistence

`log_generation()` is called synchronously (fire-and-forget via try/except).
Currently appends to in-memory list which is trivially fast. When F05 adds
database persistence, this should become a background task (asyncio.create_task
or queue) to avoid adding latency to message generation.

**Fix:** Move to `asyncio.create_task()` when log_generation becomes async in F05.

---

### 9. _default_provider in generator.py duplicates routing logic

**Feature:** R01 | **Source:** Opus R01 review, Important #3
**File:** src/messaging/generator.py:65
**Priority:** Medium — address when routing is fully wired

`_default_provider()` builds an ad-hoc ModelConfig + RoutingDecision. This
duplicates logic that should come from routing.py's `get_provider()`. Kept for
backward compatibility during R01 transition.

**Fix:** Wire `get_provider("default")` as the fallback in generate_message()
once all callers pass an explicit provider.

---

### 10. Fingerprint compare_fingerprints normalizes by hardcoded ranges

**Feature:** R01 | **Source:** Opus R01 review, Important #4
**File:** src/shared/fingerprint.py
**Priority:** Low — acceptable for Phase 1

`compare_fingerprints()` uses hardcoded normalization ranges (e.g., max
exclamation_rate=5.0). If real data exceeds these ranges, drift scores
compress. Move ranges to config when fingerprinting is used in production.

**Fix:** Move normalization ranges to config/fingerprint.yaml in Phase 2.

---

### 11. AnthropicProvider._GENERATE_TRIGGER duplicated in generator.py

**Feature:** R01 | **Source:** Opus R01 review, Important #5
**File:** src/shared/llm.py:98, src/messaging/generator.py:37
**Priority:** Low — cosmetic

The trigger string "Please generate the message now." is defined in both files.
Single source of truth would be cleaner.

**Fix:** Remove from one location and import from the other, or move to a shared
constant. Address opportunistically during next generator.py change.

---

## Completed Items

| # | Feature | Issue | Resolution | Date |
|---|---------|-------|-----------|------|
| R01-OC1 | R01 | model_id not on BaseProvider interface | Abstract property on BaseProvider; all subclasses implement | 2026-03-24 |
| R01-C1 | R01 | generator overrides routing-selected model | Use provider's model_id; record from LLMResponse | 2026-03-24 |
| R01-C2 | R01 | _default_provider uses Haiku pricing for Sonnet | Centralized MODEL_COSTS in llm.py | 2026-03-24 |
| R01-I1 | R01 | Malformed provider strings silently fall back | _parse_provider_string raises InvalidRoutingConfig | 2026-03-24 |
| R01-I2 | R01 | recipient_id always None in generation logs | log_generation falls back to composition.recipient_id | 2026-03-24 |
| R01-I3 | R01 | Cross-archetype fingerprint comparison unguarded | compare_fingerprints raises ValueError by default | 2026-03-24 |
| R01-I4 | R01 | CachedProvider only tested for empty pool | Added non-empty pool + zero-token tests | 2026-03-24 |
| R01-I5 | R01 | AnthropicProvider empty response untested directly | Added direct provider-level test | 2026-03-24 |
| R01-I6 | R01 | Alert threshold tests too loose | Added exact boundary tests | 2026-03-24 |
