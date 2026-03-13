# F02: Message Pipeline — Signals, Composition, Generation & Quality

**Phase:** 1B  
**Priority:** 2 (build after Personality Engine)  
**Architecture Reference:** Category Architecture Section 5, docs/message-modeling.md  
**JimiGPT Reference:** JimiGPT Architecture Sections 3, 5  

## Feature Description

Build the 7-stage message pipeline: trigger evaluation, signal collection,
message composition (intent selection + tone calibration + recipient state
inference), LLM message generation, quality gate filtering, delivery queuing,
and effectiveness tracking.

**User Experience Moment this serves:** "This message made me smile" and
"How did it know?" — messages must feel contextually aware and emotionally
resonant, not randomly generated.

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
- All tests pass

---

## Micro-Tasks

### Task 1: Trigger Models & Enums
**Time:** 20 min  
**Context:** Read docs/category-architecture.md Section 5, Stage 1  
**What to do:**
- Create src/messaging/__init__.py
- Create src/messaging/triggers.py with TriggerType enum, TriggerRule model
- Write tests/messaging/test_triggers.py  
**Done when:** Models validate, tests pass  
**Commit:** `feat(messaging): add trigger rule models`

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
**Time:** 20 min  
**Context:** Tasks 2-3  
**What to do:**
- Add evaluate_triggers(rules, current_time, user_context) -> list[TriggerRule]
- Enforces global constraints across trigger types
- Write tests  
**Done when:** Orchestrator correctly filters triggers  
**Commit:** `feat(messaging): add trigger evaluation orchestrator`

### Task 5: Context Signal Models & TIME Collector
**Time:** 25 min  
**Context:** Read docs/message-modeling.md Section 4  
**What to do:**
- Create src/messaging/signals.py with ContextSignalSource, ContextSignal, ContextSignalBundle, SignalCollector
- Implement TIME collector: time_of_day, day_of_week, day_type
- Write tests  
**Done when:** TIME signals collect correctly  
**Commit:** `feat(messaging): add context signal framework and TIME collector`

### Task 6: INTERACTION & SEASONAL Signal Collectors
**Time:** 25 min  
**Context:** Read docs/message-modeling.md Section 4  
**What to do:**
- INTERACTION: last_response_sentiment, days_since_last_reply, reply_pattern, recent_reaction
- SEASONAL: season, entity_anniversary
- Write tests for each  
**Done when:** All Phase 1 signal sources working  
**Commit:** `feat(messaging): add INTERACTION and SEASONAL signal collectors`

### Task 7: Message Intent Selection
**Time:** 25 min  
**Context:** Read docs/message-modeling.md Section 2  
**What to do:**
- Create src/messaging/intent.py with IntentProfile, select_intent()
- Morning greeting → ENERGIZE or ACCOMPANY (based on day type)
- Pet needs → REMIND with personality flavor
- Caring check-in → AFFIRM or COMFORT (based on interaction signals)
- Personality moment → SURPRISE or ENERGIZE
- Negative sentiment → shift toward COMFORT
- Trust stranger → lower intensity
- Write tests for each scenario  
**Done when:** Intent selection produces appropriate intents per context  
**Commit:** `feat(messaging): add message intent selection engine`

### Task 8: Tone Calibration Engine
**Time:** 25 min  
**Context:** Read docs/message-modeling.md Section 3  
**What to do:**
- Create src/messaging/tone.py with ToneRule, calibrate_tone()
- Create config/tone_rules.yaml with signal→tone adjustment rules
- Start from archetype defaults, apply matching rules, clamp 0.0-1.0
- Write tests: night reduces energy, negative sentiment reduces humor, rules stack  
**Done when:** Tone calibrates correctly based on signals  
**Commit:** `feat(messaging): add tone calibration engine`

### Task 9: Recipient State Inference
**Time:** 20 min  
**Context:** Read docs/message-modeling.md Section 5  
**What to do:**
- Create src/messaging/recipient.py with RecipientState, infer_recipient_state()
- Workday morning → busy, low receptivity; weekend → free, high receptivity
- Recent negative reply → stressed; long silence → lonely or disengaged
- State confidence = available signal count / max possible
- Write tests  
**Done when:** Recipient state infers reasonable states  
**Commit:** `feat(messaging): add recipient state inference`

### Task 10: Message Composer
**Time:** 25 min  
**Context:** Read docs/message-modeling.md Section 6  
**What to do:**
- Create src/messaging/composer.py with MessageComposition, MessageComposer
- compose(): orchestrates signals→intent→tone→state→MessageComposition
- to_prompt(): translates into 8-block LLM prompt (entity voice, intent, tone targets, context, user state, trust, anti-patterns, directive)
- Write tests: composition complete, prompt has all blocks  
**Done when:** Full composition pipeline works  
**Commit:** `feat(messaging): add message composer with rich prompt generation`

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
**Time:** 25 min  
**Context:** Category Architecture Section 5, Stage 5  
**What to do:**
- Create src/messaging/quality.py with all checks including INTENT_ALIGNMENT
- Write tests for each check  
**Done when:** Full quality gate evaluates all dimensions  
**Commit:** `feat(messaging): add quality gate with intent alignment check`

### Task 13: Effectiveness Tracking
**Time:** 20 min  
**Context:** Read docs/message-modeling.md Section 8  
**What to do:**
- Create src/messaging/effectiveness.py with MessageEffectiveness model
- Score: positive reaction +0.3, reply +0.2, positive sentiment +0.2, no response = 0.0
- Write tests  
**Done when:** Effectiveness records and scores correctly  
**Commit:** `feat(messaging): add message effectiveness tracking`

### Task 14: Pipeline Integration Test
**Time:** 25 min  
**Context:** All previous tasks  
**What to do:**
- Test full 7-stage pipeline with chaos_gremlin archetype and mocked LLM
- Verify composed prompt includes all 8 blocks
- Verify quality gate passes
- Verify effectiveness can be recorded  
**Done when:** Full pipeline integration test passes  
**Commit:** `test(messaging): add full pipeline integration test`

---

## Task Summary

| # | Task | Time | Depends On |
|---|------|------|------------|
| 1 | Trigger models & enums | 20 min | F01 complete |
| 2 | Time-based trigger evaluation | 25 min | Task 1 |
| 3 | Random interval trigger | 20 min | Task 1 |
| 4 | Trigger orchestrator | 20 min | Tasks 2-3 |
| 5 | Signal models & TIME collector | 25 min | Task 1 |
| 6 | INTERACTION & SEASONAL collectors | 25 min | Task 5 |
| 7 | Message intent selection | 25 min | Task 5, F01-T10 |
| 8 | Tone calibration engine | 25 min | Task 6, F01-T10 |
| 9 | Recipient state inference | 20 min | Task 6 |
| 10 | Message composer | 25 min | Tasks 7-9 |
| 11 | LLM message generator | 25 min | Task 10 |
| 12 | Quality gate | 25 min | Task 11 |
| 13 | Effectiveness tracking | 20 min | Task 11 |
| 14 | Pipeline integration test | 25 min | All above |

**Total estimated time:** ~5.5 hours (11-12 reps across 3-4 daily sessions)
