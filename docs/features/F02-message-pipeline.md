# F02: Message Pipeline — Triggers, Context, Generation & Quality

**Phase:** 1B  
**Priority:** 2 (build after Personality Engine)  
**Architecture Reference:** Category Architecture Section 5  
**JimiGPT Reference:** JimiGPT Architecture Sections 3, 5  

## Feature Description

Build the five-stage message pipeline: trigger evaluation, context assembly,
LLM message generation, quality gate filtering, and message queuing.
This is the engine that transforms personality into daily presence.

## Dependencies
- F01 (Personality Engine) must be complete

## What "Done" Looks Like
- Time-based and random-interval triggers evaluate correctly
- Context assembles all required fields from profile + environment
- LLM generates messages in the entity's voice
- Quality gate catches repetition, tone mismatch, forbidden phrases, and length violations
- Messages are queued for delivery with correct scheduling
- All tests pass

---

## Micro-Tasks

### Task 1: Trigger Models & Enums
**Time:** 20 min  
**Context:** Read docs/category-architecture.md Section 5, Stage 1  
**What to do:**
- Create src/messaging/__init__.py
- Create src/messaging/triggers.py with:
  TriggerType enum, TriggerRule Pydantic model
- Write tests/messaging/test_triggers.py:
  - Test TriggerRule creation with valid data
  - Test all TriggerType variants  
**Done when:** Models validate, tests pass  
**Commit:** `feat(messaging): add trigger rule models`

### Task 2: Time-Based Trigger Evaluation
**Time:** 25 min  
**Context:** Read docs/category-architecture.md Section 5, Stage 1  
**What to do:**
- Add evaluate_time_trigger(rule, current_time, timezone) function
- Handles cron-style evaluation: does this trigger fire at this time?
- Uses croniter library (add to dependencies) or simple time matching
- Write tests:
  - Trigger fires at correct time in user's timezone
  - Trigger does NOT fire outside schedule
  - Quiet hours (22:00-07:00) are respected
  - Timezone conversion works correctly  
**Done when:** Time triggers evaluate correctly across timezones  
**Commit:** `feat(messaging): add time-based trigger evaluation`

### Task 3: Random Interval Trigger
**Time:** 20 min  
**Context:** Read docs/jimigpt-architecture.md Section 5 (Trigger Configuration)  
**What to do:**
- Add evaluate_random_trigger(rule, current_time, last_fired) function
- Random triggers fire once within a time window (e.g., 11:00-14:00)
- Must respect: quiet hours, minimum 2-hour gap between messages, max 5/day
- Write tests:
  - Trigger fires within window
  - Trigger does NOT fire outside window
  - Trigger does NOT fire if already fired today
  - Respects minimum gap between messages  
**Done when:** Random triggers work within constraints  
**Commit:** `feat(messaging): add random interval trigger evaluation`

### Task 4: Trigger Evaluation Orchestrator
**Time:** 20 min  
**Context:** Read previous two tasks  
**What to do:**
- Add evaluate_triggers(rules, current_time, user_context) -> list[TriggerRule]
- Orchestrates all trigger types, returns list of triggers that fire now
- Enforces global constraints (max 5/day, 2-hour gap, quiet hours)
- Write tests:
  - Multiple triggers, only correct ones fire
  - Global constraints applied across trigger types
  - Empty result when no triggers match  
**Done when:** Orchestrator correctly filters triggers  
**Commit:** `feat(messaging): add trigger evaluation orchestrator`

### Task 5: Message Context Model
**Time:** 20 min  
**Context:** Read docs/category-architecture.md Section 5, Stage 2  
**What to do:**
- Create src/messaging/context.py with MessageContext Pydantic model
- All fields from architecture: trigger_rule, entity_profile, local_time,
  day_of_week, time_of_day, recent_messages, user_tenure_days, trust_stage,
  product_context
- Add helper: compute_time_of_day(hour: int) -> str
- Write tests:
  - MessageContext creates with all required fields
  - time_of_day correctly maps hours to morning/afternoon/evening/night  
**Done when:** MessageContext model validates correctly  
**Commit:** `feat(messaging): add message context model`

### Task 6: Context Assembly Function
**Time:** 25 min  
**Context:** Read docs/category-architecture.md Section 5, Stage 2  
**What to do:**
- Add assemble_context(trigger, entity_profile, user_data, message_history)
  -> MessageContext function to context.py
- Pulls data from trigger, profile, user record, and recent message history
- Computes derived fields (time_of_day, user_tenure_days)
- Write tests:
  - Context correctly assembled from all inputs
  - Derived fields computed correctly
  - Recent messages trimmed to last 10  
**Done when:** Context assembles correctly from all sources  
**Commit:** `feat(messaging): add context assembly function`

### Task 7: Message Generator — LLM Integration
**Time:** 25 min  
**Context:** Read docs/category-architecture.md Section 5, Stage 3  
**What to do:**
- Create src/messaging/generator.py with:
  GeneratedMessage Pydantic model
  generate_message(context, prompt, model, max_tokens) -> GeneratedMessage
- Uses Anthropic Python SDK to call Claude API
- Assembles the system prompt (from prompt_builder) + message directive
- Write tests (mock the Anthropic API call):
  - Generator returns GeneratedMessage with all fields
  - Model selection works (default to sonnet)
  - Token counts populated
  - Character count computed  
**Done when:** Generator produces messages (with mocked API)  
**Commit:** `feat(messaging): add LLM message generator`

### Task 8: Quality Gate — Core Checks
**Time:** 25 min  
**Context:** Read docs/category-architecture.md Section 5, Stage 4  
**What to do:**
- Create src/messaging/quality.py with:
  QualityCheck enum, QualityResult model, QualityGate class
- Implement checks: LENGTH, FORBIDDEN_PHRASES, REPETITION
- LENGTH: message under 160 chars for SMS
- FORBIDDEN_PHRASES: no phrases from entity's forbidden list
- REPETITION: no duplicate phrases from last 10 messages
- Write tests for each check individually  
**Done when:** Each quality check works correctly  
**Commit:** `feat(messaging): add quality gate with core checks`

### Task 9: Quality Gate — Tone & Character Checks
**Time:** 25 min  
**Context:** Read docs/category-architecture.md Section 5, Stage 4  
**What to do:**
- Add checks: TONE_MATCH, CHARACTER_CONSISTENCY, CONTENT_BOUNDARY
- TONE_MATCH: high-energy messages not sent at night
- CHARACTER_CONSISTENCY: message contains entity name reference
- CONTENT_BOUNDARY: JimiGPT-specific rules (no vet advice, no grief triggers)
- Add evaluate() method that runs ALL configured checks
- Write tests for each + orchestrated evaluation  
**Done when:** Full quality gate evaluates messages correctly  
**Commit:** `feat(messaging): add tone and character quality checks`

### Task 10: Batch Pre-Generation Skeleton
**Time:** 20 min  
**Context:** Read docs/category-architecture.md Section 5 (Batch Pre-Generation)  
**What to do:**
- Create src/messaging/batch.py with:
  BatchResult model
  generate_daily_messages(product, target_date) -> BatchResult (skeleton)
- Implement the flow as documented: load users → evaluate triggers →
  assemble context → generate → quality gate → queue
- For now, wire the skeleton with TODO comments for database calls
- Write test for the happy path with mocked dependencies  
**Done when:** Batch flow skeleton connects all pipeline stages  
**Commit:** `feat(messaging): add batch pre-generation skeleton`

### Task 11: Pipeline Integration Test
**Time:** 25 min  
**Context:** All previous tasks in this feature  
**What to do:**
- Create tests/messaging/test_integration.py
- Test full pipeline: trigger fires → context assembled → message generated
  → quality gate passes → message ready for delivery
- Use a real archetype (chaos_gremlin) with mocked LLM response
- Verify the message that comes out passes all quality checks  
**Done when:** Full pipeline integration test passes  
**Commit:** `test(messaging): add pipeline integration test`

---

## Task Summary

| # | Task | Time | Depends On |
|---|------|------|------------|
| 1 | Trigger models & enums | 20 min | F01 complete |
| 2 | Time-based trigger evaluation | 25 min | Task 1 |
| 3 | Random interval trigger | 20 min | Task 1 |
| 4 | Trigger orchestrator | 20 min | Tasks 2-3 |
| 5 | Message context model | 20 min | Task 1 |
| 6 | Context assembly function | 25 min | Task 5 |
| 7 | Message generator (LLM) | 25 min | Task 5, F01 |
| 8 | Quality gate core checks | 25 min | Task 7 |
| 9 | Quality gate tone/character | 25 min | Task 8 |
| 10 | Batch pre-generation skeleton | 20 min | Tasks 4,6,7,8 |
| 11 | Pipeline integration test | 25 min | All above |

**Total estimated time:** ~4.5 hours (9-10 reps across 3 daily sessions)
