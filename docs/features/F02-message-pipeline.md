# F02: Message Pipeline — Signals, Composition, Generation & Quality

**Phase:** 1B
**Priority:** 2 (build after Personality Engine)
**Architecture Reference:** Category Architecture Section 5, docs/message-modeling.md
**JimiGPT Reference:** JimiGPT Architecture Sections 3, 5
**Future Architecture Reference:** docs/future-architecture.md (foundation fields only)

## Feature Description

Build the 7-stage message pipeline: trigger evaluation, signal collection,
message composition (intent selection + tone calibration + recipient state
inference), LLM message generation, quality gate filtering, delivery queuing,
and effectiveness tracking.

**User Experience Moment this serves:** "This message made me smile" and
"How did it know?" — messages must feel contextually aware and emotionally
resonant, not randomly generated.

**Foundation work included:** This feature lays the groundwork for Phase 2
features (message arcs, multi-recipient, life events) by including optional
fields and forward-compatible interfaces. These add minimal implementation
time (~5 min per task) but save significant refactoring later. All foundation
fields are optional/None in Phase 1 — no new behavior, just the right
interfaces.

## Dependencies
- F01 (Personality Engine) must be complete, including Task 10 (tone/intent)

## What "Done" Looks Like
- Triggers evaluate correctly (time-based, random-interval)
- Context signals collected from TIME + INTERACTION + SEASONAL sources
- Message intent selected based on trigger + signals + trust
- Tone calibrated from archetype defaults + signal-based adjustments
- Recipient state inferred from available signals
- LLM generates messages using rich composed prompt
- Quality gate catches repetition, tone mismatch, intent misalignment
- Messages queued for delivery
- Effectiveness tracking records user reactions
- All foundation fields present and tested with None/empty defaults
- All tests pass

---

## Micro-Tasks

### Task 1: Trigger Models & Enums
**Time:** 25 min (was 20 — added foundation fields)
**Context:** Read docs/category-architecture.md Section 5, Stage 1.
Read docs/future-architecture.md Sections 1, 5 (arc_template, sibling awareness).
**What to do:**
- Create src/messaging/__init__.py
- Create src/messaging/triggers.py with:
  - TriggerType enum (TIME_BASED, EVENT_BASED, RANDOM_INTERVAL, RESPONSE_TRIGGERED, MILESTONE)
  - TriggerRule model with all fields from category architecture
  - **FOUNDATION:** Add `arc_template: str | None = None` field
    (which message arc template this trigger starts — None in Phase 1)
  - **FOUNDATION:** Add `sibling_entity_ids: list[str] = Field(default_factory=list)`
    (other entities belonging to same user — empty in Phase 1)
- Write tests/messaging/test_triggers.py:
  - Test model validation for all trigger types
  - Test that arc_template defaults to None
  - Test that sibling_entity_ids defaults to empty list
**Done when:** Models validate, foundation fields default correctly, tests pass
**Commit:** `feat(messaging): add trigger rule models with arc and sibling foundations`

### Task 2: Time-Based Trigger Evaluation
**Time:** 25 min
**Context:** Read docs/category-architecture.md Section 5, Stage 1
**What to do:**
- Add evaluate_time_trigger(rule, current_time, timezone) function
- Write tests: fires at correct time, respects quiet hours, timezone works
**Done when:** Time triggers evaluate correctly across timezones
**Commit:** `feat(messaging): add time-based trigger evaluation`

### Task 3: Random Interval Trigger
**Time:** 20 min
**Context:** Read docs/jimigpt-architecture.md Section 5
**What to do:**
- Add evaluate_random_trigger(rule, current_time, last_fired) function
- Must respect: quiet hours, min 2-hour gap, max 5/day
- Write tests
**Done when:** Random triggers work within constraints
**Commit:** `feat(messaging): add random interval trigger evaluation`

### Task 4: Trigger Evaluation Orchestrator
**Time:** 25 min (was 20 — added sibling awareness parameter)
**Context:** Tasks 2-3. Read docs/future-architecture.md Section 5.
**What to do:**
- Add evaluate_triggers(rules, current_time, user_context,
  sibling_entity_schedules=None) -> list[TriggerRule]
- **FOUNDATION:** Accept `sibling_entity_schedules: list[dict] | None = None`
  parameter. In Phase 1, this is always None and ignored. The interface is
  ready for multi-pet scheduling coordination in Phase 2.
- Enforces global constraints across trigger types
- Write tests:
  - Orchestrator correctly filters triggers
  - None sibling_entity_schedules works (Phase 1 default)
  - Empty list sibling_entity_schedules works
**Done when:** Orchestrator correctly filters triggers, accepts sibling param
**Commit:** `feat(messaging): add trigger evaluation orchestrator with multi-pet interface`

### Task 5: Context Signal Models & TIME Collector
**Time:** 25 min
**Context:** Read docs/message-modeling.md Section 4.
Read docs/future-architecture.md Section 4 (USER_CONTEXT source).
**What to do:**
- Create src/messaging/signals.py with:
  - ContextSignalSource enum — include all sources from message-modeling.md
  - **FOUNDATION:** Include `USER_CONTEXT = "user_context"` in the enum now.
    No collector implemented for it in Phase 1, but the enum value exists.
  - ContextSignal, ContextSignalBundle, SignalCollector models
- Implement TIME collector: time_of_day, day_of_week, day_type
- Write tests:
  - TIME signals collect correctly
  - USER_CONTEXT exists in enum
  - SignalCollector handles missing collectors gracefully (returns empty, no error)
**Done when:** TIME signals collect correctly, USER_CONTEXT enum value exists
**Commit:** `feat(messaging): add context signal framework and TIME collector`

### Task 6: INTERACTION & SEASONAL Signal Collectors
**Time:** 30 min (was 25 — added context_tags field)
**Context:** Read docs/message-modeling.md Section 4.
Read docs/future-architecture.md Section 4 (user context extraction).
**What to do:**
- INTERACTION collector produces signals for:
  - last_response_sentiment
  - days_since_last_reply
  - reply_pattern (frequent | occasional | rare | silent)
  - recent_reaction
  - **FOUNDATION:** `last_reply_context_tags: list[str] = []`
    (extracted keywords from last reply — empty list in Phase 1, populated
    by reply classification in Phase 2)
- SEASONAL: season, entity_anniversary
- Write tests for each
- **Test:** context_tags field defaults to empty list and is included
  in the signal bundle
**Done when:** All Phase 1 signal sources working, context_tags field present
**Commit:** `feat(messaging): add INTERACTION and SEASONAL signal collectors with context tags foundation`

### Task 7: Message Intent Selection
**Time:** 30 min (was 25 — added life_contexts parameter)
**Context:** Read docs/message-modeling.md Section 2.
Read docs/future-architecture.md Section 3 (life event intent overrides).
**What to do:**
- Create src/messaging/intent.py with IntentProfile, select_intent()
- Function signature: select_intent(trigger, signals, trust_stage,
  archetype_weights, life_contexts=None)
- **FOUNDATION:** `life_contexts: list[str] | None = None` parameter.
  In Phase 1, always None and ignored. In Phase 2, life contexts will
  override intent selection (e.g., sick_day blocks ENERGIZE intent).
  Add a comment documenting the Phase 2 behavior.
- Phase 1 intent selection logic:
  - Morning greeting → ENERGIZE or ACCOMPANY (based on day type)
  - Pet needs → REMIND with personality flavor
  - Caring check-in → AFFIRM or COMFORT (based on interaction signals)
  - Personality moment → SURPRISE or ENERGIZE
  - Negative sentiment → shift toward COMFORT
  - Trust stranger → lower intensity
  - **Milestone/anniversary signals → weight CELEBRATE and SURPRISE higher**
- Write tests for each scenario, plus:
  - Test that None life_contexts works (Phase 1 default)
**Done when:** Intent selection produces appropriate intents, life_contexts param accepted
**Commit:** `feat(messaging): add message intent selection engine with life context interface`

### Task 8: Tone Calibration Engine
**Time:** 30 min (was 25 — added life_contexts parameter)
**Context:** Read docs/message-modeling.md Section 3.
Read docs/future-architecture.md Section 3 (life event tone overrides).
**What to do:**
- Create src/messaging/tone.py with ToneRule, calibrate_tone()
- Function signature: calibrate_tone(archetype_defaults, signals,
  trust_stage, life_contexts=None)
- Create config/tone_rules.yaml with signal→tone adjustment rules
- **FOUNDATION:** `life_contexts: list[str] | None = None` parameter.
  In Phase 1, always None and ignored. In Phase 2, life contexts apply
  tone overrides (e.g., sick_day caps energy at 0.4). Add a comment.
- Start from archetype defaults, apply matching rules, clamp 0.0-1.0
- Write tests:
  - Night reduces energy
  - Negative sentiment reduces humor
  - Rules stack correctly
  - Clamping works at boundaries
  - None life_contexts works (Phase 1 default)
**Done when:** Tone calibrates correctly based on signals, life_contexts param accepted
**Commit:** `feat(messaging): add tone calibration engine with life context interface`

### Task 9: Recipient State Inference
**Time:** 25 min (was 20 — added life_contexts parameter)
**Context:** Read docs/message-modeling.md Section 5.
Read docs/future-architecture.md Section 3.
**What to do:**
- Create src/messaging/recipient.py with RecipientState, infer_recipient_state()
- Function signature: infer_recipient_state(signals, trust_profile,
  interaction_history, life_contexts=None)
- **FOUNDATION:** `life_contexts: list[str] | None = None` parameter.
  In Phase 2, active life contexts directly influence inferred state
  (e.g., user_sick → emotional_context="unwell", likely_energy=low).
- Phase 1 inference:
  - Workday morning → busy, low receptivity
  - Weekend → free, high receptivity
  - Recent negative reply → stressed
  - Long silence → lonely or disengaged
  - State confidence = available signal count / max possible
- Write tests, plus:
  - Test None life_contexts works
**Done when:** Recipient state infers reasonable states, life_contexts param accepted
**Commit:** `feat(messaging): add recipient state inference with life context interface`

### Task 10: Message Composer
**Time:** 30 min (was 25 — added foundation fields)
**Context:** Read docs/message-modeling.md Section 6.
Read docs/future-architecture.md Sections 1, 2, 3 (all foundation fields).
**What to do:**
- Create src/messaging/composer.py with MessageComposition, MessageComposer
- MessageComposition model includes ALL standard fields plus:
  - **FOUNDATION:** `arc_id: str | None = None` (message arc this belongs to)
  - **FOUNDATION:** `arc_position: int | None = None` (position within arc)
  - **FOUNDATION:** `recipient_id: str | None = None` (explicit recipient —
    in Phase 1, populated from entity owner; ready for multi-recipient)
  - **FOUNDATION:** `life_contexts: list[str] = Field(default_factory=list)`
    (active life contexts — empty in Phase 1)
  - **FOUNDATION:** `entity_coordination_id: str | None = None`
    (for multi-pet scheduling coordination)
- MessageComposer.compose() signature:
  compose(entity, trigger, signals, trust, message_history, recipient_id=None)
  - **FOUNDATION:** Takes explicit `recipient_id` rather than inferring
    from entity. In Phase 1, caller passes entity owner's ID. Ready for
    multi-recipient in Phase 2.
- compose(): orchestrates signals→intent→tone→state→MessageComposition
- to_prompt(): translates into 8-block LLM prompt (entity voice, intent,
  tone targets, context, user state, trust, anti-patterns, directive)
- Write tests:
  - Composition complete with all required fields
  - All foundation fields default to None/empty correctly
  - Prompt has all 8 blocks
  - recipient_id flows through correctly
**Done when:** Full composition pipeline works, foundation fields present and tested
**Commit:** `feat(messaging): add message composer with future-proofing foundations`

### Task 11: LLM Message Generator
**Time:** 25 min
**Context:** Category Architecture Section 5, Stage 4
**What to do:**
- Create src/messaging/generator.py with GeneratedMessage, generate_message()
- Uses Anthropic SDK with composed prompt
- Records intended_intent and intended_tone on generated message
- Write tests (mock API)
**Done when:** Generator produces messages from composed specifications
**Commit:** `feat(messaging): add LLM message generator with composition`

### Task 12: Quality Gate
**Time:** 30 min (was 25 — added consecutive coherence concept)
**Context:** Category Architecture Section 5, Stage 5.
Read docs/future-architecture.md Section 1 (arc coherence).
**What to do:**
- Create src/messaging/quality.py with all checks:
  - CHARACTER_CONSISTENCY
  - REPETITION
  - TONE_MATCH
  - CONTENT_BOUNDARY
  - LENGTH
  - SAFETY
  - FORBIDDEN_PHRASES
  - INTENT_ALIGNMENT
  - **FOUNDATION:** CONSECUTIVE_COHERENCE — checks that this message doesn't
    emotionally contradict the previous message to the same recipient.
    Phase 1 implementation: basic check — if previous message was COMFORT
    intent and this is ENERGIZE, flag for review. Simple rule-based, not
    arc-aware. In Phase 2, this becomes arc-coherence-aware.
- Write tests for each check, including:
  - Consecutive coherence catches COMFORT→ENERGIZE contradiction
  - Consecutive coherence passes compatible sequences (ACCOMPANY→COMFORT)
  - No previous message → check passes (first message)
**Done when:** Full quality gate evaluates all dimensions including coherence
**Commit:** `feat(messaging): add quality gate with consecutive coherence check`

### Task 13: Effectiveness Tracking
**Time:** 20 min
**Context:** Read docs/message-modeling.md Section 8
**What to do:**
- Create src/messaging/effectiveness.py with MessageEffectiveness model
- Score: positive reaction +0.3, reply +0.2, positive sentiment +0.2,
  no response = 0.0
- Write tests
**Done when:** Effectiveness records and scores correctly
**Commit:** `feat(messaging): add message effectiveness tracking`

### Task 14: Pipeline Integration Test
**Time:** 30 min (was 25 — verify foundation fields)
**Context:** All previous tasks
**What to do:**
- Test full 7-stage pipeline with chaos_gremlin archetype and mocked LLM
- Verify composed prompt includes all 8 blocks
- Verify quality gate passes (including consecutive coherence)
- Verify effectiveness can be recorded
- **FOUNDATION VERIFICATION:**
  - Verify all foundation fields (arc_id, arc_position, recipient_id,
    life_contexts, entity_coordination_id) are None/empty in output
  - Verify pipeline works correctly with these None/empty values
  - Verify recipient_id flows from compose() input to composition output
  - Verify life_contexts=None flows through intent, tone, and recipient state
**Done when:** Full pipeline integration test passes, foundation fields verified
**Commit:** `test(messaging): add full pipeline integration test with foundation verification`

---

## Task Summary

| # | Task | Time | Depends On | Foundation Work |
|---|------|------|------------|-----------------|
| 1 | Trigger models & enums | 25 min | F01 complete | arc_template, sibling_entity_ids |
| 2 | Time-based trigger evaluation | 25 min | Task 1 | — |
| 3 | Random interval trigger | 20 min | Task 1 | — |
| 4 | Trigger orchestrator | 25 min | Tasks 2-3 | sibling_entity_schedules param |
| 5 | Signal models & TIME collector | 25 min | Task 1 | USER_CONTEXT enum value |
| 6 | INTERACTION & SEASONAL collectors | 30 min | Task 5 | context_tags field |
| 7 | Message intent selection | 30 min | Task 5, F01-T10 | life_contexts param |
| 8 | Tone calibration engine | 30 min | Task 6, F01-T10 | life_contexts param |
| 9 | Recipient state inference | 25 min | Task 6 | life_contexts param |
| 10 | Message composer | 30 min | Tasks 7-9 | arc_id, recipient_id, life_contexts, coordination_id |
| 11 | LLM message generator | 25 min | Task 10 | — |
| 12 | Quality gate | 30 min | Task 11 | CONSECUTIVE_COHERENCE check |
| 13 | Effectiveness tracking | 20 min | Task 11 | — |
| 14 | Pipeline integration test | 30 min | All above | Verify all foundation fields |

**Total estimated time:** ~6.5 hours (was 5.5 — added ~1 hour for foundation work)
**(13-14 reps across 4-5 daily sessions)**

---

## Opus Review Tasks (High-Blast-Radius)

The following tasks require Opus review per docs/review/REVIEW-WORKFLOW.md:

- **T7: Message intent selection** — wrong intent = wrong emotional impact
- **T8: Tone calibration engine** — miscalibration = message feels off
- **T10: Message composer** — convergence point, foundation fields critical
- **T11: LLM message generator** — prompt quality = message quality
- **T12: Quality gate** — last defense before message reaches a human

---

## Parallel Message Testing

After T11 is complete, create `scripts/generate_samples.py` and begin
parallel testing per docs/review/parallel-testing-rubric.md. Generate
sample messages and evaluate against the 3-tier rubric. Don't wait for
the full pipeline — test generation quality immediately.
