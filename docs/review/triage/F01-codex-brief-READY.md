# Codex Feature Review — F01: Personality Engine
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

- **Feature:** F01 — Personality Engine (Core Models & Archetypes)
- **Tasks completed:** T1 through T10
- **Architecture references:**
  - docs/category-architecture.md — Sections 1, 3 (Entity-Agnostic Principle, Four-Layer Personality Model), 4 (Prompt Assembly), 11 (Archetype Config Format)
  - docs/jimigpt-architecture.md — Section 2 (Pet-Specific Extensions, Archetype Table)
  - docs/message-modeling.md — Sections 2, 3 (MessageIntent enum, ToneSpectrum model)

## What This Feature Does

F01 builds the personality foundation. It implements the four-layer personality
model (CommunicationStyle, EmotionalDisposition, RelationalStance,
KnowledgeAwareness) as Pydantic models. It provides an archetype system that
loads personality configurations from YAML files, supports blending two
archetypes with configurable weights, and translates a complete EntityProfile
into a structured LLM system prompt via Jinja2 templates. Task 10 added
ToneSpectrum (6-dimensional tone model) and MessageIntent (14 intent types)
as the bridge to the upcoming message pipeline (F02).

This is the soul of every Emotional AI product — if the personality models
are wrong, no amount of good messaging will save it.

## Files Created/Modified in This Feature

### Source Files
```
src/personality/__init__.py
src/personality/enums.py          — EnergyLevel enum
src/personality/models.py         — Four-layer models, ToneSpectrum, EntityProfile
src/personality/pet_profile.py    — PetProfile (JimiGPT-specific extension)
src/personality/archetypes.py     — ArchetypeConfig, load/list/blend functions
src/personality/prompt_builder.py — Jinja2 prompt assembly, PromptBlock, AssembledPrompt
src/messaging/__init__.py
src/messaging/models.py           — MessageIntent enum (14 intent types)
src/main.py                       — FastAPI app with health endpoint
```

### Test Files
```
tests/conftest.py                        — Shared fixtures
tests/test_health.py                     — Health endpoint test
tests/personality/__init__.py
tests/personality/test_models.py         — Four-layer model validation tests
tests/personality/test_pet_profile.py    — PetProfile extension tests
tests/personality/test_archetypes.py     — Load, list, blend tests
tests/personality/test_prompt_builder.py — Prompt assembly tests
tests/personality/test_integration.py    — Full pipeline: YAML → blend → prompt
tests/personality/test_tone_intent.py    — ToneSpectrum + intent weights tests
```

### Configuration Files
```
config/archetypes/jimigpt/chaos_gremlin.yaml
config/archetypes/jimigpt/loyal_shadow.yaml
config/archetypes/jimigpt/regal_one.yaml
config/archetypes/jimigpt/gentle_soul.yaml
config/archetypes/jimigpt/food_monster.yaml
config/archetypes/jimigpt/adventure_buddy.yaml
config/archetypes/jimigpt/couch_potato.yaml
config/archetypes/jimigpt/anxious_sweetheart.yaml
config/prompts/base_identity.j2
config/prompts/communication_style.j2
config/prompts/emotional_disposition.j2
config/prompts/relational_stance.j2
config/prompts/knowledge_awareness.j2
config/prompts/anti_patterns.j2
config/prompts/message_directive.j2
```

### Other
```
pyproject.toml
CLAUDE.md
.env.example
.github/workflows/ci.yml
```

## Specific Review Focus Areas

### 1. Correctness & Logic
- Does `blend_archetypes()` correctly apply weights? Is the dominant-archetype
  selection logic (p_weight >= s_weight) correct for all weight combinations?
- Do all 8 archetype YAML files have complete, valid tone_defaults and
  intent_weights sections?
- Does intent_weights sum correctly in each archetype? Should it sum to 1.0?
- Is ToneSpectrum clamping handled correctly (all values 0.0-1.0)?

### 2. Test Coverage
- Does every public function have at least one test?
- Are failure modes tested? (invalid YAML, missing files, bad weights)
- Are edge cases covered? (blend with None secondary, weights at exact 0.5/0.5)
- Is the integration test comprehensive enough to catch cross-module issues?

### 3. Architecture Conformance
- Is entity-agnostic vs. pet-specific properly separated?
  - `models.py` should have NO pet references
  - `pet_profile.py` should ONLY extend, not modify core models
  - Archetype YAML is in `config/archetypes/jimigpt/` (product-specific)
- Are Pydantic models used for ALL data? No raw dicts? No Any types?
- Are functions under 30 lines?
- Does the prompt builder's block structure match the 7-block prompt spec
  in category-architecture.md Section 4?

### 4. Integration Points (Critical for F02)
- F02 (Message Pipeline) will depend heavily on:
  - `EntityProfile` and `ToneSpectrum` from models.py
  - `MessageIntent` from messaging/models.py
  - `assemble_prompt()` from prompt_builder.py
  - `ArchetypeConfig.tone_defaults` and `intent_weights`
- Are these interfaces clean? Will F02 be able to use them without
  internal knowledge of F01?
- Is `AssembledPrompt` flexible enough to accommodate the 8-block prompt
  structure that F02's MessageComposer will need (adding intent, tone targets,
  context, user state blocks)?

### 5. Maintainability
- Could a new developer understand this code in 10 minutes?
- Are there magic numbers or hardcoded values that should be config?
- Is the archetype YAML format documented well enough that someone could
  create archetype #9 without reading the source code?

## Known Decisions (Don't Flag These)

- **Functional style over classes:** We deliberately minimize classes. Pydantic
  models for data, plain functions for logic. This is intentional.
- **ToneSpectrum on models.py, not messaging:** ToneSpectrum is a personality
  property (archetype defaults), not just a messaging concept. It lives in
  the personality module deliberately.
- **MessageIntent in messaging/models.py:** Intent is a messaging concept.
  It lives in messaging even though F01-T10 created it. This is the bridge
  to F02.
- **`entity_type` is always "companion" in blend:** This will be overridden
  by PetProfile ("pet") when used in JimiGPT. The blend function works at
  the entity-agnostic level.
- **Phase 1 signal sources only:** Only TIME, INTERACTION, SEASONAL signals
  are planned for now. WEATHER, CALENDAR, LOCATION come in Phase 2.

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
