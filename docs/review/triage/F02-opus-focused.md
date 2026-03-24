# Opus Focused Review — F02: Message Pipeline (High-Blast-Radius Tasks)

**Date:** 2026-03-23
**Reviewer:** Claude Opus 4.6 (self-review, same model as author — treating as
read-only review against architecture docs and emotional safety criteria)
**Tasks reviewed:** T7 (intent), T8 (tone), T10 (composer), T11 (generator), T12 (quality gate)

---

## Critical (Fix Now)

### C1. Generator crashes on empty API response
**File:** src/messaging/generator.py:69
**Issue:** `response.content[0].text` assumes the API returns at least one
content block. If Anthropic returns an empty content list (rate limit, content
filter, model refusal), this raises `IndexError` and crashes the pipeline.
**Why it matters:** In production, this means a single unusual API response
takes down the message generation for that user. No message is sent, no
effectiveness is recorded, and the failure is unhandled.
**Verified:** `asyncio.run(generate_message(comp, client=mock_empty))` raises
`IndexError: list index out of range`.
**Suggested fix:** Check `len(response.content) > 0` before accessing. Return
a sentinel GeneratedMessage with empty content (the quality gate's
INTENT_ALIGNMENT check will catch it and discard), or raise a domain-specific
`GenerationError` that the orchestrator can handle.

### C2. Tone rule with invalid dimension name crashes calibration
**File:** src/messaging/tone.py:75
**Issue:** `dims[rule.dimension]` does a dict lookup. If a tone rule in YAML
has a typo in the dimension field (e.g., "enrgy" instead of "energy"), this
raises `KeyError` and crashes `calibrate_tone()`.
**Why it matters:** A single bad rule in `config/tone_rules.yaml` takes down
tone calibration for ALL messages, not just the affected dimension. This is a
configuration-driven crash with blast radius across all users.
**Verified:** Adding `{"signal": "test", "dimension": "enrgy", "adjustment": 0.1,
"reason": "test"}` to tone_rules.yaml raises `KeyError: 'enrgy'`.
**Suggested fix:** Skip unknown dimensions with a warning log, or validate
dimensions at YAML load time against `_TONE_DIMENSIONS`. The per-rule skip
is safer (one bad rule doesn't block other rules).

### C3. TONE_MATCH quality check is asymmetric — misses flat messages on high energy spec
**File:** src/messaging/quality.py:208-224
**Issue:** `_check_tone_match()` only detects high-excitement content (ALL CAPS +
exclamations) contradicting a low energy spec (< 0.3). It does NOT detect the
reverse: a flat, lifeless message when the energy spec is high (e.g., 0.95).
A COMFORT-intent check catches the caps case, but an ENERGIZE-intent message
saying "hey. i guess it is morning." passes all quality checks.
**Why it matters:** A pet personality configured as high-energy chaos_gremlin
(energy=0.95) could send a depressed-sounding message. This breaks character
consistency and could confuse or concern the user. "Why is my usually-bouncy
pet suddenly flat?"
**Verified:** Message "hey. i guess it is morning." with energy spec 0.95
passes TONE_MATCH and INTENT_ALIGNMENT.
**Suggested fix:** Add a reverse check: when energy spec > 0.7, verify the
content has at least some excitement markers (exclamation count >= 1, or
sentence structure isn't all lowercase + periods). Keep the threshold
conservative to avoid false positives.

---

## Important (Fix Later)

### I1. Generator has no error handling for API failures
**File:** src/messaging/generator.py:62-67
**Issue:** The `await _client.messages.create(...)` call has no try/except.
API errors (rate limits, network timeouts, 500s, auth failures) propagate as
unhandled exceptions. In production, this means transient API issues crash the
pipeline.
**Why it matters:** The architecture spec says "regenerate up to 3 attempts"
on quality gate failure. The generator itself has no retry logic. The
orchestrator (not yet built) will need to handle this, but the generator should
at minimum wrap the API call and raise a domain-specific error.
**Suggested fix:** Catch `anthropic.APIError` and subclasses. Raise a
`GenerationError(message, retryable=True/False)` so the orchestrator can
decide whether to retry.

### I2. IntentProfile missing `urgency` field from architecture spec
**File:** src/messaging/intent.py:55-60
**Issue:** The architecture doc (message-modeling.md Section 2) specifies
`urgency: float (0.0-1.0)` on IntentProfile. The implementation only has
`primary_intent`, `secondary_intent`, and `intensity`.
**Why it matters:** Without urgency, the delivery scheduler (F03) cannot
distinguish "send this when convenient" from "send this NOW." All messages
are treated as equal priority.
**Suggested fix:** Add `urgency: float = Field(default=0.0, ge=0.0, le=1.0)`
to IntentProfile. Default 0.0 = "anytime" which preserves Phase 1 behavior.
Set urgency based on trigger type or signal context in select_intent().

### I3. Tone rules loaded from disk on every calibrate_tone() call
**File:** src/messaging/tone.py:98-104
**Issue:** `_load_rules()` reads and parses `config/tone_rules.yaml` on every
call. No caching.
**Why it matters:** In production, this means a file I/O + YAML parse on
every single message generation. With 5 messages/day/user and 1000 users,
that's 5000 unnecessary disk reads per day.
**Suggested fix:** Cache rules at module level with a simple `_cached_rules`
variable, or use `functools.lru_cache`. Rules only change on deployment.

### I4. Composer always passes empty interaction_history
**File:** src/messaging/composer.py:140 (after fix)
**Issue:** `infer_recipient_state()` is called with `interaction_history=[]`
always. The function accepts this parameter for Phase 2 enrichment, but the
composer never populates it.
**Why it matters:** When interaction history becomes available (Phase 2+),
someone will need to remember to wire this. It's a subtle gap that could be
missed.
**Suggested fix:** Accept `interaction_history` parameter on `compose()` or
derive it from `message_history`. For Phase 1, the default `[]` is correct.

### I5. Safety phrases are hardcoded, not configurable per product
**File:** src/messaging/quality.py:27-46
**Issue:** Both `_AI_BREAKING_PHRASES` and `_UNSAFE_PHRASES` are module-level
constants. Different products (JimiGPT vs NeuroAmigo) may need different
safety phrase lists.
**Why it matters:** NeuroAmigo (neurodivergent social companion) would likely
need a much broader safety phrase list, including mental health-specific
content. The current architecture violates the entity-agnostic principle by
hardcoding safety content.
**Suggested fix:** Move safety phrases to product-level configuration (YAML).
The quality gate already accepts per-entity forbidden_phrases — extend the
pattern to safety phrases.

---

## Architecture Notes

### A1. RecipientPreference entirely omitted
The architecture spec (message-modeling.md Section 3) defines
`RecipientPreference` with humor_receptivity, warmth_preference, etc. and a
`apply_preference_adjustment()` function. This is completely absent from the
implementation. Already documented as a known decision (Phase 2), but the
architecture doc should be annotated to reflect this.

### A2. No retry/regeneration loop
The architecture spec says the quality gate should "regenerate up to 3 attempts"
on failure, then discard. The current implementation has no regeneration loop —
the quality gate returns a result but nothing acts on failures. This will be
the orchestrator's job (F03 or later), but it's an open integration gap.

### A3. ENTITY_MEMORY signal source has no collector
The architecture lists `ENTITY_MEMORY` as a Phase 1A signal source, but no
collector exists. `USER_CONTEXT` is documented as Phase 2 foundation (enum
only), which is correct. But ENTITY_MEMORY is listed as Phase 1A in the
architecture, suggesting it should have a collector.

---

## What Looks Good

1. **Per-step clamping in tone calibration is correct.** Each rule application
   clamps immediately, preventing cascading overflow. This matches the spec and
   is safer than end-of-pipeline clamping.

2. **Signal-to-rule matching via string sets is elegant.** The
   `"{key}:{value}"` pattern with trust injection is clean, extensible, and
   avoids complex conditional logic.

3. **Quality gate is well-factored.** Checks are isolated pure functions,
   composable via the `checks` list, and easy to extend. Adding a new check
   requires only a new function + enum value.

4. **Intent selection precedence chain is sound.** Anniversary > negative
   sentiment > category rules > trust intensity is a reasonable emotional
   hierarchy. The override mechanism means crisis moments (negative sentiment)
   always get COMFORT regardless of the trigger category.

5. **Foundation fields are present and tested.** All Phase 2 fields (arc_id,
   arc_position, life_contexts, etc.) default correctly and have explicit tests
   verifying they don't change Phase 1 behavior.

6. **Graceful degradation on missing signals.** When signals are empty,
   intent defaults to category-based selection, tone stays at archetype defaults,
   and recipient state falls back to "free / medium" — all reasonable safe defaults.

7. **Consecutive coherence check is forward-looking.** The jarring transition
   table (COMFORT→ENERGIZE, GROUND→SURPRISE) captures real emotional safety
   concerns. Phase 2 arc-awareness will refine this correctly.

---

## Summary

The F02 pipeline has a solid modular architecture and the emotional safety
fundamentals are mostly right — intent precedence, trust-gated vulnerability,
forbidden phrase checks, and consecutive coherence all work correctly.

The three critical issues are all in the "what happens when things go wrong"
category: empty API response crashes the generator (C1), bad YAML config
crashes tone calibration (C2), and flat messages slip through the quality
gate when high energy is specified (C3). None of these affect the happy path,
but all three can cause user-facing harm in production — either via pipeline
crashes (no message sent) or character-breaking messages (flat tone from an
energetic pet).

The important issues are Phase 2 preparation gaps (urgency, interaction
history, per-product safety phrases) and a performance concern (tone rules
disk I/O). These don't affect Phase 1 correctness but should be addressed
before scaling.
