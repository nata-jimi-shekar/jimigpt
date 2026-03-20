# Codex Review Brief — Feature-Level
## Post-Feature Code Review

> **Copy this template, fill in the bracketed sections, and feed to ChatGPT Codex.**
> One feature per review. Scope is the entire feature's code surface.

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

- **Feature:** [F## — Feature Name]
- **Feature doc:** [paste the full feature doc from docs/features/F##.md]
- **Tasks completed:** [T1 through T##]
- **Architecture references:**
  - [docs/category-architecture.md — Sections X, Y]
  - [docs/message-modeling.md — Sections X, Y] (if relevant)
  - [docs/jimigpt-architecture.md — Sections X, Y] (if relevant)

## Files Created/Modified in This Feature

```
[List ALL files this feature touched — src, tests, config]
src/messaging/__init__.py
src/messaging/triggers.py
src/messaging/signals.py
src/messaging/intent.py
src/messaging/tone.py
src/messaging/recipient.py
src/messaging/composer.py
src/messaging/generator.py
src/messaging/quality.py
src/messaging/effectiveness.py
tests/messaging/test_triggers.py
tests/messaging/test_signals.py
...
config/tone_rules.yaml
```

## What This Feature Does

[3-5 sentences. What does this feature do end-to-end? What user experience
does it enable? What are the key design decisions?]

## Specific Review Focus Areas

### 1. Correctness & Logic
- Do the functions produce correct outputs for their documented inputs?
- Are there logic errors in conditionals, calculations, or state transitions?
- Do edge cases produce safe results or exceptions?

### 2. Test Coverage
- Does every public function have at least one test?
- Are failure modes tested (not just happy paths)?
- For LLM-related code: are tests property-based (length, contains name,
  no forbidden phrases) rather than asserting exact outputs?
- Are integration tests present that verify cross-module interactions?

### 3. Architecture Conformance
- Does the code match the documented architecture?
- Is entity-agnostic vs. pet-specific properly separated?
- Are Pydantic models used for ALL data? No raw dicts? No Any types?
- Are functions under 30 lines? Is complex logic extracted?

### 4. Integration Points
- How does this feature connect to previous features?
- Are the interfaces clean? Could another feature use these modules
  without internal knowledge?
- Are there implicit dependencies that should be explicit?

### 5. Maintainability
- Could a new developer understand this code in 10 minutes?
- Are function names and module organization self-documenting?
- Are there magic numbers or hardcoded values that should be config?

## Known Decisions (Don't Flag These)

[List any deliberate decisions that might look like issues but are intentional]
- Example: "We use functional style with minimal classes — this is deliberate"
- Example: "RecipientPreference is initialized from archetype selection,
  behavioral evolution comes in Phase 2"
- Example: "Only TIME, INTERACTION, SEASONAL signals in Phase 1 — WEATHER,
  CALENDAR, LOCATION are Phase 2"

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
