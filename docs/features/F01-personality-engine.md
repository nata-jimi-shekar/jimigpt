# F01: Personality Engine — Core Models & Archetypes

**Phase:** 1A  
**Priority:** 1 (build this first — everything else depends on it)  
**Architecture Reference:** Category Architecture Sections 3, 4  
**JimiGPT Reference:** JimiGPT Architecture Section 2  

## Feature Description

Build the core personality system: the four-layer personality model as Pydantic
models, the archetype loading system, archetype blending logic, and the
personality-to-prompt translator that converts a structured profile into an
LLM system prompt.

This is the soul of every Emotional AI product. Get this right and everything
downstream works. Get it wrong and no amount of good messaging will save it.

## Dependencies
- None (this is the foundation)

## What "Done" Looks Like
- All Pydantic models validate correctly with mypy --strict
- 8 pet archetype YAML files load and parse without errors
- Two archetypes can be blended with configurable weights
- A complete EntityProfile produces a well-structured LLM system prompt
- All tests pass

---

## Micro-Tasks

### Task 1: Project Setup & Skeleton
**Time:** 20 min  
**Context:** Read CLAUDE.md for tech stack. No architecture docs needed.  
**What to do:**
- Create pyproject.toml with all dependencies (FastAPI, Pydantic, pytest, etc.)
- Create src/__init__.py, src/personality/__init__.py, etc. (all __init__ files)
- Create a minimal src/main.py with a FastAPI health check endpoint
- Create tests/test_health.py that tests the health endpoint
- Run pytest to verify everything works  
**Done when:** `pytest` passes, `mypy src/` passes, `ruff check src/` passes  
**Commit:** `chore(setup): initialize project with FastAPI and test infrastructure`

### Task 2: Core Personality Models
**Time:** 25 min  
**Context:** Read docs/category-architecture.md Section 3 (Four-Layer Personality Model)  
**What to do:**
- Create src/personality/models.py with all Pydantic models:
  CommunicationStyle, EmotionalDisposition, RelationalStance,
  KnowledgeAwareness, EntityProfile
- Create src/personality/enums.py for shared enums (EnergyLevel, etc.)
- Write tests/personality/test_models.py:
  - Test that valid data creates models correctly
  - Test that invalid data raises validation errors
  - Test that EntityProfile composes all four layers  
**Done when:** All model tests pass, mypy passes  
**Commit:** `feat(personality): add four-layer personality Pydantic models`

### Task 3: Pet Profile Extension
**Time:** 20 min  
**Context:** Read docs/jimigpt-architecture.md Section 2 (Pet-Specific Extensions)  
**What to do:**
- Create src/personality/pet_profile.py with PetProfile extending EntityProfile
- Add pet-specific fields: species, breed, appearance_notes, story_insights,
  feeding_times, walk_times, owner_name, pet_nicknames
- Write tests/personality/test_pet_profile.py:
  - Test PetProfile creation with all fields
  - Test PetProfile inherits EntityProfile validation
  - Test optional fields work correctly  
**Done when:** Tests pass, PetProfile validates correctly  
**Commit:** `feat(personality): add PetProfile with pet-specific fields`

### Task 4: Archetype Configuration Format
**Time:** 20 min  
**Context:** Read docs/category-architecture.md Section 11 (Archetype Configuration Format)  
**What to do:**
- Create src/personality/archetypes.py with:
  - ArchetypeConfig Pydantic model (maps YAML structure to Python)
  - load_archetype(path: Path) -> ArchetypeConfig function
  - list_archetypes(product: str) -> list[ArchetypeConfig] function
- Create ONE sample archetype YAML: config/archetypes/jimigpt/chaos_gremlin.yaml
- Write tests/personality/test_archetypes.py:
  - Test loading a valid YAML file produces correct ArchetypeConfig
  - Test loading invalid YAML raises meaningful error
  - Test list_archetypes finds files in the correct directory  
**Done when:** Can load chaos_gremlin.yaml into an ArchetypeConfig  
**Commit:** `feat(personality): add archetype config loading from YAML`

### Task 5: Create All 8 Pet Archetypes
**Time:** 25 min  
**Context:** Read docs/jimigpt-architecture.md Section 2 (Archetype table)  
**What to do:**
- Create 7 more archetype YAML files in config/archetypes/jimigpt/:
  loyal_shadow.yaml, regal_one.yaml, gentle_soul.yaml,
  food_monster.yaml, adventure_buddy.yaml, couch_potato.yaml,
  anxious_sweetheart.yaml
- Each file follows the exact format of chaos_gremlin.yaml
- Personality values should feel distinct and authentic per archetype
- Write one parametrized test that loads ALL 8 and validates each  
**Done when:** All 8 archetypes load and validate  
**Commit:** `feat(personality): add all 8 pet archetype configurations`

### Task 6: Archetype Blending
**Time:** 25 min  
**Context:** Read docs/category-architecture.md Section 3 (Archetype Blending)  
**What to do:**
- Add blend_archetypes() function to src/personality/archetypes.py
- Takes primary ArchetypeConfig, optional secondary, and weights dict
- Returns a complete EntityProfile with blended values
- Write tests/personality/test_archetypes.py (add to existing):
  - Equal weights produce averaged/merged values
  - Weight 1.0 on primary returns primary unchanged
  - Weights not summing to 1.0 raises ValueError
  - Blending two archetypes produces valid EntityProfile  
**Done when:** Blending tests pass  
**Commit:** `feat(personality): add archetype blending with configurable weights`

### Task 7: Prompt Template Fragments
**Time:** 20 min  
**Context:** Read docs/category-architecture.md Section 4 (Prompt Assembly Architecture)  
**What to do:**
- Create Jinja2 templates in config/prompts/:
  - base_identity.j2 (entity name, type, product identity)
  - communication_style.j2 (how the entity talks)
  - emotional_disposition.j2 (baseline mood, humor)
  - relational_stance.j2 (attachment, initiative)
  - knowledge_awareness.j2 (domain knowledge, temporal)
  - anti_patterns.j2 (forbidden phrases, topics)
  - message_directive.j2 (per-message instructions)
- Each template takes its corresponding Pydantic model as input
- No tests for templates directly — tested via prompt builder in Task 8  
**Done when:** All template files created, Jinja2 syntax valid  
**Commit:** `feat(personality): add prompt template fragments`

### Task 8: Prompt Builder
**Time:** 25 min  
**Context:** Read docs/category-architecture.md Section 4 (Personality-to-Prompt Translator)  
**What to do:**
- Create src/personality/prompt_builder.py with:
  - PromptBlock and AssembledPrompt Pydantic models
  - assemble_prompt(profile: EntityProfile, message_context: dict) -> AssembledPrompt
  - Uses Jinja2 templates from config/prompts/
- Write tests/personality/test_prompt_builder.py:
  - Test that a complete EntityProfile produces a non-empty prompt
  - Test that all 7 blocks are present in the assembled prompt
  - Test that entity name appears in the prompt
  - Test that forbidden phrases appear in anti-patterns block
  - Snapshot test: same profile always produces same prompt structure  
**Done when:** Prompt builder tests pass  
**Commit:** `feat(personality): add personality-to-prompt translator`

### Task 9: Integration Test — Profile to Prompt
**Time:** 20 min  
**Context:** This task ties everything together. Read previous task outputs.  
**What to do:**
- Create tests/personality/test_integration.py:
  - Load chaos_gremlin archetype from YAML
  - Blend with loyal_shadow at 70/30
  - Create a PetProfile from the blend
  - Assemble a prompt from the profile
  - Verify prompt contains expected personality markers
  - Verify prompt doesn't contain forbidden phrases
  - Verify prompt is well-formed (no empty blocks, no template artifacts)
- Fix any issues found during integration  
**Done when:** Full pipeline works: YAML → ArchetypeConfig → blend → EntityProfile → AssembledPrompt  
**Commit:** `test(personality): add integration test for full personality pipeline`

### Task 10: Add Tone Spectrum Defaults to Archetypes
**Time:** 20 min  
**Context:** Read docs/message-modeling.md Sections 2-3 (Intent, Tone Calibration)  
**What to do:**
- Add ToneSpectrum Pydantic model to src/personality/models.py
  (warmth, humor, directness, gravity, energy, vulnerability — all 0.0-1.0)
- Add tone_defaults section to each archetype YAML file with appropriate values
  (chaos_gremlin: high humor/energy, low gravity; loyal_shadow: high warmth/vulnerability)
- Add MessageIntent enum to src/messaging/models.py (shared intent types)
- Add intent_weights section to each archetype YAML:
  which intents this archetype naturally excels at
- Update ArchetypeConfig to load tone_defaults and intent_weights
- Write tests: verify tone loads correctly, verify intent weights sum properly  
**Done when:** Each archetype has tone defaults and intent weights  
**Commit:** `feat(personality): add tone spectrum and intent weights to archetypes`

---

## Task Summary

| # | Task | Time | Depends On |
|---|------|------|------------|
| 1 | Project setup & skeleton | 20 min | — |
| 2 | Core personality models | 25 min | Task 1 |
| 3 | Pet profile extension | 20 min | Task 2 |
| 4 | Archetype config format | 20 min | Task 2 |
| 5 | Create all 8 archetypes | 25 min | Task 4 |
| 6 | Archetype blending | 25 min | Task 4 |
| 7 | Prompt template fragments | 20 min | Task 2 |
| 8 | Prompt builder | 25 min | Task 7 |
| 9 | Integration test | 20 min | All above |
| 10 | Tone spectrum & intent weights | 20 min | Tasks 5, 8 |

**Total estimated time:** ~4 hours (8 reps across 2-3 daily sessions)
