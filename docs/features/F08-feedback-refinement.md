# F08: Feedback Loop & Personality Refinement

**Phase:** 1D  
**Priority:** 8  
**Architecture Reference:** Category Architecture Section 3 (Personality Evolution)  
**JimiGPT Reference:** JimiGPT Architecture Section 6  

## Feature Description

Build the mechanisms that make the Digital Twin smarter over time: the debrief
loop (entity asks "Am I getting this right?"), message reactions (thumbs up/down),
quiet mode, and personality weight adjustment based on accumulated feedback.

## Dependencies
- F01-F06 (full backend), F07 (frontend birthing complete)

## What "Done" Looks Like
- Digital Twin periodically asks personality refinement questions
- User can react positively/negatively to any message
- Reactions adjust archetype weights over time
- Quiet Mode pauses messages instantly without guilt
- Personality visibly improves based on feedback
- All tests pass

---

## Micro-Tasks

### Task 1: Debrief Question Generator
**Time:** 25 min  
**Context:** Category Architecture Section 3 (Personality Evolution, Debrief Loop)  
**What to do:**
- Create src/personality/debrief.py with:
  generate_debrief_question(entity_profile, interaction_count) -> str
- Questions are in the pet's voice, asking about personality accuracy
- Only generates after 5+ interactions (Initial Trust stage)
- Max 1 debrief question per 3 days
- Write tests:
  - Generates question in entity's voice
  - Respects frequency limits
  - Not generated for new users  
**Done when:** Debrief questions generate appropriately  
**Commit:** `feat(personality): add debrief question generator`

### Task 2: Debrief Response Processing
**Time:** 25 min  
**Context:** JimiGPT Architecture Section 2 (Archetype Selection Flow)  
**What to do:**
- Add POST /api/v1/jimigpt/debrief endpoint
- Processes user's response to debrief question
- Adjusts archetype weights based on response
  (e.g., "less energetic" shifts primary weight away from high-energy archetype)
- Updates entity personality_profile in database
- Write tests:
  - Response adjusts weights correctly
  - Weights still sum to 1.0 after adjustment
  - Changes persist to database  
**Done when:** Debrief responses modify personality  
**Commit:** `feat(personality): add debrief response processing`

### Task 3: Message Reaction System
**Time:** 20 min  
**Context:** Category Architecture Section 5 (Quality Gate feedback)  
**What to do:**
- Ensure POST /messages/reaction endpoint works (from F05)
- Add: process_reaction(message_id, reaction) function
  - Tracks positive/negative per message_category
  - If a category gets 3+ negative reactions in a week,
    flag for quality gate adjustment
- Update trust events with reaction data
- Write tests:
  - Reaction persists correctly
  - Category-level tracking accumulates
  - Trust events created  
**Done when:** Reactions tracked and accumulated  
**Commit:** `feat(messaging): add message reaction tracking and analysis`

### Task 4: Quiet Mode
**Time:** 20 min  
**Context:** Trust Framework Principle 4 (User Agency)  
**What to do:**
- Add PATCH /api/v1/triggers/quiet-mode endpoint
  - Accepts: {enabled: true, duration_hours: int | null}
  - Immediately pauses all scheduled messages
  - If duration specified, auto-resumes after duration
  - No guilt-inducing language in any response
- Write tests:
  - Quiet mode stops all deliveries
  - Timed quiet mode resumes correctly
  - Trigger evaluation respects quiet mode  
**Done when:** Quiet mode works instantly  
**Commit:** `feat(delivery): add quiet mode with timed auto-resume`

### Task 5: Frontend — Reaction & Quiet Mode UI
**Time:** 25 min  
**Context:** Previous tasks in this feature  
**What to do:**
- Add reaction buttons (thumbs up/down) to message display if/when viewing
  message history in app
- Add Quiet Mode toggle in settings (with optional duration picker)
- Show current quiet mode status prominently
- Write tests: toggle interaction, API calls  
**Done when:** Users can react to messages and toggle quiet mode  
**Commit:** `feat(frontend): add reaction buttons and quiet mode UI`

### Task 6: Recipient Preference Evolution
**Time:** 25 min  
**Context:** Read docs/message-modeling.md Section 5b (Recipient Preference Model)  
**What to do:**
- Create src/messaging/recipient_preference.py with:
  update_recipient_preference(current, message_effectiveness) -> RecipientPreference
- Wire into message reaction flow: when user reacts (Task 3),
  look up the message's intended tone, compare with reaction,
  and adjust relevant preference dimensions
- Rules: positive reaction to high-humor → humor_receptivity += 0.03,
  negative reaction to high-humor → humor_receptivity -= 0.05,
  ignored high-energy → energy_tolerance -= 0.02
  (negative adjustments stronger than positive — loss aversion)
- Update confidence: min(1.0, data_points / 50)
- Update tone calibration to include apply_preference_adjustment()
- Write tests:
  - Positive reaction adjusts preference correctly
  - Negative reaction has stronger effect
  - Values clamp at 0.0 and 1.0
  - Confidence increases with data points  
**Done when:** Reactions evolve recipient preference, tone calibration uses it  
**Commit:** `feat(messaging): add recipient preference evolution from reactions`

---

## Task Summary

| # | Task | Time | Depends On |
|---|------|------|------------|
| 1 | Debrief question generator | 25 min | F01-F06 |
| 2 | Debrief response processing | 25 min | Task 1 |
| 3 | Message reaction system | 20 min | F05 |
| 4 | Quiet mode | 20 min | F03 |
| 5 | Frontend reaction & quiet mode | 25 min | Tasks 3-4 |
| 6 | Recipient preference evolution | 25 min | Task 3, F02 |

**Total estimated time:** ~2.5 hours (6 reps, 2 daily sessions)
