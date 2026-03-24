# Codex Feature Review — F02: Message Pipeline
## Pre-Filled Brief — Ready to Paste to ChatGPT Codex

---

## Instructions for Codex

You are reviewing a completed feature for JimiGPT, an Emotional AI product
that creates Digital Twin companions for pets and sends contextual text
messages. This is a solo developer's codebase — your review is the "second
pair of eyes" that catches what the author missed.

**Your role:** Code quality reviewer. Focus on: correctness, test coverage,
integration risks, maintainability, and conformance to the documented
architecture. Be specific — cite files and functions. Don't nitpick style
(Ruff handles that) or type errors (mypy handles that).

**Important:** The architecture docs below are the source of truth. If code
deviates from docs, flag it as an issue. If you think the architecture is
wrong, note it separately — code should match docs as written.

---

## Project Overview

- **Product:** JimiGPT — sends personality-driven SMS messages from a user's
  pet. Users create a Digital Twin of their living pet with a personality
  profile, and the system sends contextual messages throughout the day.
- **Stack:** Python 3.12+, FastAPI, Pydantic v2 (strict mode), pytest,
  Ruff, mypy --strict, Supabase, Twilio, Anthropic Claude API
- **Key constraint:** All engine code must be entity-agnostic. Pet-specific
  logic lives in config/YAML only. The same engine must work for a future
  product (NeuroAmigo — neurodivergent social companion) with config changes.

## Feature Being Reviewed

- **Feature:** F02 — Message Pipeline (Signals, Composition, Generation & Quality)
- **Tasks completed:** T1 through T14
- **Architecture references:**
  - docs/category-architecture.md — Section 5 (7-Stage Message Pipeline)
  - docs/message-modeling.md — Sections 2-8 (MessageIntent, ToneSpectrum, Signals, Recipient, Composition, Prompt, Effectiveness)
  - docs/jimigpt-architecture.md — Sections 3, 5 (Pet Message Strategy, Scheduling)
  - docs/future-architecture.md — Sections 1-5 (all foundation fields: message arcs, multi-recipient, life events, user context, multi-pet)

## What This Feature Does

F02 builds the complete 7-stage message pipeline that transforms a trigger
event into a contextually-aware, personality-driven message. The pipeline
flows: Trigger Evaluation → Signal Collection (TIME, INTERACTION, SEASONAL) →
Message Composition (intent selection + tone calibration + recipient state
inference) → LLM Generation (via Anthropic Claude API) → Quality Gate (9
configurable checks) → Effectiveness Tracking. The composer produces an
8-block structured LLM prompt (entity voice, intent, tone targets, world
context, user state, trust/relationship, anti-patterns, directive). All Phase 2
foundation fields (arc_id, arc_position, recipient_id, life_contexts,
entity_coordination_id, sibling_entity_ids, context_tags, USER_CONTEXT enum)
are present with None/empty defaults and tested.

## Files Created/Modified in This Feature

### Source Files
```
src/messaging/__init__.py
src/messaging/models.py               — MessageIntent enum (14 intent types, created in F01-T10)
src/messaging/triggers.py             — TriggerType enum, TriggerRule model (foundation: arc_template, sibling_entity_ids)
src/messaging/time_trigger.py         — evaluate_time_trigger (cron-based, timezone-aware, quiet hours)
src/messaging/random_trigger.py       — evaluate_random_trigger (2-hour gap, 5/day limit, quiet hours)
src/messaging/orchestrator.py         — evaluate_triggers orchestrator (foundation: sibling_entity_schedules param)
src/messaging/signals.py              — ContextSignalSource, ContextSignal, ContextSignalBundle, SignalCollector, collect_time_signals
src/messaging/interaction_collector.py — InteractionData, collect_interaction_signals (foundation: last_reply_context_tags)
src/messaging/seasonal_collector.py    — SeasonalData, collect_seasonal_signals (season + anniversary)
src/messaging/intent.py               — TrustStage, IntentProfile, select_intent (foundation: life_contexts param)
src/messaging/tone.py                 — ToneRule, ToneCalibrationResult, calibrate_tone (foundation: life_contexts param)
src/messaging/recipient.py            — TrustProfile, RecipientState, infer_recipient_state (foundation: life_contexts param)
src/messaging/composer.py             — MessageComposition, ComposedPrompt, MessageComposer (foundation: arc_id, arc_position, recipient_id, life_contexts, entity_coordination_id)
src/messaging/generator.py            — GeneratedMessage, generate_message (async, Anthropic SDK with client injection)
src/messaging/quality.py              — QualityCheck (9 checks), QualityResult, QualityGate (foundation: CONSECUTIVE_COHERENCE)
src/messaging/effectiveness.py        — MessageEffectiveness, score_effectiveness, record_effectiveness
```

### Test Files
```
tests/messaging/__init__.py
tests/messaging/test_triggers.py             — TriggerType enum, TriggerRule model, foundation fields
tests/messaging/test_time_trigger.py         — Time-based trigger evaluation, cron, quiet hours, timezones
tests/messaging/test_random_trigger.py       — Random interval trigger, gap enforcement, daily limits
tests/messaging/test_orchestrator.py         — Trigger orchestrator, global constraints, sibling_entity_schedules foundation
tests/messaging/test_signals.py              — Signal models, TIME collector, SignalCollector, USER_CONTEXT enum
tests/messaging/test_interaction_seasonal.py — INTERACTION + SEASONAL collectors, functools.partial registration
tests/messaging/test_intent.py               — Intent selection across all categories, trust stages, overrides
tests/messaging/test_tone.py                 — Tone calibration, rule stacking, clamping, signal matching
tests/messaging/test_recipient.py            — Recipient state inference, availability, emotional context
tests/messaging/test_composer.py             — MessageComposition, 8-block prompt, foundation fields, compose pipeline
tests/messaging/test_generator.py            — LLM generation with mocked Anthropic client
tests/messaging/test_quality.py              — All 9 quality checks individually + gate integration
tests/messaging/test_effectiveness.py        — Scoring components, factory function, model bounds
tests/messaging/test_pipeline_integration.py — Full 7-stage pipeline with chaos_gremlin archetype
```

### Configuration Files
```
config/tone_rules.yaml             — 14 signal→dimension tone adjustment rules
```

## Specific Review Focus Areas

### 1. Correctness & Logic
- Does `select_intent()` correctly implement the precedence chain? Anniversary
  override → negative sentiment override → category rules → trust intensity.
  Is the category→intent mapping correct for all 5 categories (greeting, need,
  caring, celebrate, personality_moment)?
- Does `calibrate_tone()` correctly build the signal set as `"{key}:{value}"`
  strings, inject trust stage, match rules, and apply per-step clamping?
  Are adjustments applied in the right order? Does clamping happen per-rule
  (not just at the end)?
- Does `infer_recipient_state()` produce reasonable states for all time/day
  combinations? Is the emotional inference precedence correct (anniversary →
  negative → silence → positive → neutral)?
- Does `score_effectiveness()` produce correct scores for all combinations?
  The max is 0.7 (0.3 + 0.2 + 0.2). Does it handle edge cases like
  `reply_sentiment="positive"` with `user_replied=False`?
- Does the quality gate's `_check_consecutive_coherence()` correctly use
  previous_message.intended_intent vs composition.intent.primary_intent?
  Are the jarring transitions (COMFORT→ENERGIZE, COMFORT→SURPRISE,
  GROUND→ENERGIZE, GROUND→SURPRISE) the right set?
- Does `evaluate_random_trigger()` in `random_trigger.py` correctly enforce
  the 2-hour gap and 5/day limit? Are quiet hours respected?
- Does `evaluate_triggers()` in `orchestrator.py` correctly route rules to
  the right evaluator and enforce global constraints?
- Does the `SignalCollector.collect()` method correctly handle async and
  missing collectors?

### 2. Test Coverage
- Does every public function have at least one test?
- Are failure modes tested? (invalid cron expressions, out-of-bounds tone
  values, empty signal bundles, quality gate with no checks configured)
- Are edge cases covered? (clamping at 0.0 and 1.0, alliance trust stage,
  anniversary on exact day, midnight boundary for time_of_day)
- For LLM-related code: are tests property-based (mock client, check structure)
  rather than asserting exact LLM output?
- Are integration tests present? The pipeline integration test
  (`test_pipeline_integration.py`) should verify cross-module interactions
  across all 7 stages.
- **Foundation field tests:** Are all foundation fields tested with their
  None/empty defaults? Do they NOT change Phase 1 behavior?
- Is `functools.partial` registration tested for INTERACTION and SEASONAL
  collectors that need extra data beyond the `CollectorFn` signature?

### 3. Architecture Conformance
- Does the code match the documented 7-stage pipeline in category-architecture.md Section 5?
- Is entity-agnostic vs. pet-specific properly separated?
  - `intent.py`, `tone.py`, `recipient.py`, `composer.py` should have NO pet references
  - `config/tone_rules.yaml` should be product-neutral rules
  - Archetype-specific config remains in `config/archetypes/jimigpt/`
- Are Pydantic models used for ALL data? No raw dicts? No Any types?
- Are functions under 30 lines? Is complex logic extracted?
- Does the 8-block prompt structure match docs/message-modeling.md Section 7?
- Does the MessageComposition model match docs/message-modeling.md Section 6?
- Are all foundation fields from docs/future-architecture.md present?
  - `arc_template` and `sibling_entity_ids` on TriggerRule
  - `USER_CONTEXT` in ContextSignalSource enum
  - `last_reply_context_tags` on InteractionData
  - `life_contexts` parameter on select_intent, calibrate_tone, infer_recipient_state
  - `arc_id`, `arc_position`, `recipient_id`, `life_contexts`, `entity_coordination_id` on MessageComposition
  - `CONSECUTIVE_COHERENCE` in QualityCheck enum

### 4. Integration Points
- **F01 → F02 integration:** F02 depends heavily on:
  - `EntityProfile` and `ToneSpectrum` from `src/personality/models.py`
  - `MessageIntent` from `src/messaging/models.py`
  - `ArchetypeConfig.tone_defaults` and `intent_weights` from `src/personality/archetypes.py`
  - `blend_archetypes()` from `src/personality/archetypes.py`
  - Are these interfaces used correctly? Does `MessageComposer.compose()` handle
    the case where `tone_defaults` is not on `EntityProfile` (it's on `ArchetypeConfig`)?
- **F02 internal integration:** The pipeline has a strict data flow:
  TriggerRule → SignalCollector → select_intent/calibrate_tone/infer_recipient_state →
  MessageComposition → generate_message → QualityGate → record_effectiveness.
  Are the data types at each boundary correct? Does each stage's output type
  match the next stage's input type?
- **F03+ forward compatibility:** F03 (Delivery & Scheduling) will need:
  - `GeneratedMessage` to be deliverable
  - `QualityResult` to determine if a message should be sent
  - `MessageEffectiveness` to be recordable after delivery
  - Are these models complete enough for F03 to use without modification?

### 5. Maintainability
- Could a new developer understand the pipeline flow in 10 minutes?
- Are there magic numbers? Check:
  - Trust intensity values in `intent.py` (0.35, 0.55, 0.70, 0.80, 0.85)
  - Effectiveness scoring weights (0.3, 0.2, 0.2) — should they be configurable?
  - Quality gate thresholds (caps_ratio > 0.3, exclamation_count >= 2)
  - Recipient state constants (receptivity values, silence thresholds)
  - Max character count (160) — is it configurable per product?
- Are the tone rules in `config/tone_rules.yaml` well-structured?
  Could a non-developer tweak them?
- Is `MessageComposer` doing too much? It orchestrates intent + tone +
  recipient + builds composition + translates to prompt. Should any of
  this be extracted?

## Known Decisions (Don't Flag These)

- **Functional style over classes:** We deliberately minimize classes. Pydantic
  models for data, plain functions for logic. `MessageComposer` is the exception
  because it genuinely encapsulates composition state and prompt building.
- **ToneSpectrum defaults on ArchetypeConfig, not EntityProfile:** `tone_defaults`
  is passed as a keyword parameter to `MessageComposer.compose()` with a neutral
  fallback. This is deliberate — the blend function doesn't carry tone defaults.
- **Phase 1 signal sources only:** Only TIME, INTERACTION, SEASONAL collectors
  implemented. WEATHER, CALENDAR, LOCATION come in Phase 2. USER_CONTEXT enum
  value exists but has no collector.
- **Foundation fields are no-ops:** All foundation fields (arc_id, arc_position,
  life_contexts, entity_coordination_id, etc.) default to None/empty and do NOT
  change Phase 1 behavior. They exist only to prevent refactoring when Phase 2
  activates them.
- **RecipientPreference omitted:** The architecture doc mentions
  `RecipientPreference` on `MessageComposition` but it's Phase 2. Skipped entirely.
- **Effectiveness max score is 0.7:** The ceiling is intentional — a perfect
  message still has 0.3 of unmeasured impact. Phase 2 introduces richer signals.
- **`functools.partial` for collector registration:** INTERACTION and SEASONAL
  collectors need extra data beyond the standard `CollectorFn(user_id, entity_id,
  datetime)` signature. `functools.partial` at registration time solves this.
- **Signal matching via string sets:** Tone rules match signals using
  `"{signal_key}:{signal_value}"` string sets. This uniform mechanism handles
  both signal-based and trust-based rules in the same loop.
- **160-character max is hardcoded:** SMS character limit. This is correct
  for JimiGPT's Twilio integration.

## Output Format

Structure your review as:

### Critical Issues (Fix Now)
Bugs, incorrect logic, missing validation, security issues, broken
integration points. Each with: file, function, issue, impact, suggested fix.

### Important Issues (Fix Later)
Test gaps, missing edge cases, suboptimal patterns, minor architecture drift.
Non-blocking but should be addressed before MVP.

### Observations
Things that aren't issues but worth noting — patterns forming, potential
future problems, suggestions for improvement.

### Strengths
What's working well. Good patterns to continue.

### Summary
2-3 sentence overall assessment of the feature's code quality.
