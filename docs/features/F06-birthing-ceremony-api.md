# F06: Birthing Ceremony — Backend API

**Phase:** 1C  
**Priority:** 6  
**Architecture Reference:** Category Architecture Section 3  
**JimiGPT Reference:** JimiGPT Architecture Section 4  

## Feature Description

Build the backend API for the birthing ceremony: photo analysis via Claude Vision,
personality extraction from story prompts, archetype suggestion, entity creation,
first message generation, and birth certificate generation.

## Dependencies
- F01 (Personality Engine), F05 (Database & Auth)

## What "Done" Looks Like
- Photos analyzed via Claude Vision API → species, breed, appearance notes
- Story prompt processed → personality signals extracted
- System suggests primary + secondary archetype with confidence
- Full entity created and persisted with personality profile
- First message generated in the new entity's voice
- Birth certificate image generated (PNG)
- All tests pass

---

## Micro-Tasks

### Task 1: Photo Analysis Endpoint
**Time:** 25 min  
**Context:** Anthropic Vision API docs, JimiGPT Architecture Section 4  
**What to do:**
- Create src/api/jimigpt.py with POST /api/v1/jimigpt/analyze-photos
- Accepts base64 images, sends to Claude Vision API
- Returns: species, breed_guess, appearance_notes, energy_estimate
- Write tests (mock Claude API):
  - Returns structured analysis from photo
  - Handles multiple photos
  - Handles invalid image gracefully  
**Done when:** Photo analysis returns structured pet data  
**Commit:** `feat(jimigpt): add photo analysis via Claude Vision`

### Task 2: Story Prompt → Personality Signals
**Time:** 25 min  
**Context:** JimiGPT Architecture Section 4 (Archetype Selection Flow)  
**What to do:**
- Add function: extract_personality_signals(story_text: str) -> dict
- Uses Claude API to analyze the story and extract personality indicators
  (energy level, humor, attachment style, quirks)
- Maps signals to archetype compatibility scores
- Write tests (mock Claude API):
  - High-energy story maps to high-energy archetypes
  - Calm story maps to calm archetypes
  - Short story still produces usable signals  
**Done when:** Story text produces personality signal scores  
**Commit:** `feat(jimigpt): add story prompt personality extraction`

### Task 3: Archetype Suggestion Engine
**Time:** 20 min  
**Context:** JimiGPT Architecture Section 2 (Archetype Selection Flow)  
**What to do:**
- Add function: suggest_archetypes(photo_analysis, story_signals)
  -> tuple[ArchetypeConfig, ArchetypeConfig | None, dict[str, float]]
- Combines photo analysis (breed/energy) with story signals
- Returns primary archetype, optional secondary, and confidence weights
- Write tests:
  - High-energy breed + high-energy story → adventure_buddy or chaos_gremlin
  - Calm breed + calm story → gentle_soul or couch_potato
  - Mixed signals → primary + secondary with split weights  
**Done when:** Suggestion engine produces reasonable archetype matches  
**Commit:** `feat(jimigpt): add archetype suggestion engine`

### Task 4: Birth Endpoint — Full Flow
**Time:** 25 min  
**Context:** JimiGPT Architecture Section 4, Category Architecture Section 9  
**What to do:**
- Add POST /api/v1/jimigpt/birth endpoint to src/api/jimigpt.py
- Accepts: name, photos (optional, may already be analyzed), story,
  confirmed_archetype, secondary_archetype, weights
- Creates EntityProfile (blended from confirmed archetypes + pet details)
- Persists entity to database
- Generates first message using new profile
- Returns: entity_id, first_message, entity_profile summary
- Write tests:
  - Birth creates entity in database
  - First message is in the entity's voice
  - All required fields returned  
**Done when:** Birth endpoint creates a complete Digital Twin  
**Commit:** `feat(jimigpt): add birth endpoint for Digital Twin creation`

### Task 5: Birth Certificate Generator
**Time:** 25 min  
**Context:** JimiGPT Architecture Section 4 (Birth Certificate)  
**What to do:**
- Create src/personality/certificate.py (or shared/certificate.py)
- Uses Pillow to generate a PNG certificate with:
  Pet name, born date, archetype name, owner name, certificate number
- Template-based: base image + dynamic text overlay
- Add GET /api/v1/jimigpt/certificate/{entity_id} endpoint
- Write tests:
  - Certificate generates as valid PNG
  - Contains correct pet name and date
  - Returns correct content type  
**Done when:** Certificate generates and serves as downloadable image  
**Commit:** `feat(jimigpt): add birth certificate generation`

---

## Task Summary

| # | Task | Time | Depends On |
|---|------|------|------------|
| 1 | Photo analysis endpoint | 25 min | F01, F05 |
| 2 | Story → personality signals | 25 min | F01 |
| 3 | Archetype suggestion | 20 min | Tasks 1-2 |
| 4 | Birth endpoint (full flow) | 25 min | Task 3, F05 |
| 5 | Birth certificate generator | 25 min | Task 4 |

**Total estimated time:** ~2 hours (5 reps, 1-2 daily sessions)
