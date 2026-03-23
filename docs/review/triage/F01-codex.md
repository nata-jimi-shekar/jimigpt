# Codex Feature-Level Triage — F01: Personality Engine

**Date:** [03/23/2026]
**Reviewer:** ChatGPT Codex
**Feature reviewed:** F01 — Personality Engine
**Tasks covered:** T1 through T10
**Files reviewed:** See F01-codex-brief-READY.md for full list

---

 ### Critical Issues (Fix Now)

  1. blend_archetypes() accepts invalid weight maps and can produce a profile from weights that do not reference either
     archetype.
     File: /C:/shekar73/Documents/Projects/jimigpt-reviews/F01/src/personality/archetypes.py:90
     Issue: the function only checks sum(weights.values()) == 1.0 and then falls back to 0.5 when primary.id or
     secondary.id is missing (/C:/shekar73/Documents/Projects/jimigpt-reviews/F01/src/personality/archetypes.py:104, /
     C:/shekar73/Documents/Projects/jimigpt-reviews/F01/src/personality/archetypes.py:126). blend_archetypes(primary,
     secondary, {"wrong:key": 1.0}) succeeds and returns a profile anyway.
     Impact: callers can persist a logically invalid EntityProfile whose archetype_weights do not describe the blend
     that produced it. That will leak into downstream analytics, debugging, and any F02 logic that trusts those weights.
     Suggested fix: require the weight keys to be exactly {primary.id} when secondary is None, or exactly {primary.id,
     secondary.id} otherwise; require each weight to be 0.0 <= w <= 1.0; reject cross-product blends.
  2. assemble_prompt() does not implement the architecture contract F02 is supposed to build on.
     Files: /C:/shekar73/Documents/Projects/jimigpt-reviews/F01/src/personality/prompt_builder.py:13, /C:/shekar73/
     Documents/Projects/jimigpt-reviews/F01/config/prompts/base_identity.j2:1, /C:/shekar73/Documents/Projects/jimigpt-
     reviews/F01/config/prompts/message_directive.j2:1
     Issue: the builder is hard-coded to 7 blocks and only accepts an untyped dict[str, object] with message_category,
     max_characters, and channel (/C:/shekar73/Documents/Projects/jimigpt-reviews/F01/src/personality/
     prompt_builder.py:42). The architecture docs for Section 4 / message-modeling Section 6 expect the prompt bridge to
     carry intent, tone targets, world context, user state, and relationship depth into an 8-block composition.
     Impact: F02 cannot use assemble_prompt() as a clean public interface; it will have to reach inside F01 or rewrite
     this module. That is exactly the integration coupling the brief warns about.
     Suggested fix: replace the raw dict with a validated composition/input model and make block assembly data-driven so
     new F02 blocks can be added without changing function internals.

  ### Important Issues (Fix Later)

  1. ArchetypeConfig does not enforce the new F02-facing fields strongly enough.
     File: /C:/shekar73/Documents/Projects/jimigpt-reviews/F01/src/personality/archetypes.py:21
     Issue: tone_defaults is optional and intent_weights is just dict[str, float] with no validation of allowed intent
     keys, numeric bounds, or sum-to-1.0. I confirmed the model accepts tone_defaults=None and
     intent_weights={"not_a_real_intent": 1.5}.
     Impact: the current 8 YAMLs are fine, but archetype #9 can silently violate the documented config contract and
     break F02 at runtime.
     Suggested fix: make tone_defaults required, type intent_weights against MessageIntent, and validate completeness/
     range/sum in the model.
  2. Pydantic strict mode is documented but not actually enforced in the models.
     Files: /C:/shekar73/Documents/Projects/jimigpt-reviews/F01/src/personality/models.py:8, /C:/shekar73/Documents/
     Projects/jimigpt-reviews/F01/src/personality/pet_profile.py:1
     Issue: the models inherit plain BaseModel with no strict config. In practice, values like "0.8" for
     ToneSpectrum.warmth and "true" for booleans are coerced successfully.
     Impact: this drifts from the architecture requirement and makes config/input bugs harder to catch early.
     Suggested fix: add a shared strict base model or model_config = ConfigDict(strict=True) where appropriate, then
     adjust tests for explicit validation behavior.
  3. list_archetypes() silently drops invalid YAML files.
     File: /C:/shekar73/Documents/Projects/jimigpt-reviews/F01/src/personality/archetypes.py:58
     Issue: any ValueError during load is swallowed and the file is skipped.
     Impact: a broken archetype can disappear from the catalog with no signal, which is a bad failure mode for config-
     driven behavior.
     Suggested fix: either fail fast, or return structured load errors / log them explicitly.
  4. Test coverage is good on happy paths, but it misses the schema and interface risks above.
     Files: /C:/shekar73/Documents/Projects/jimigpt-reviews/F01/tests/personality/test_archetypes.py:257, /C:/shekar73/
     Documents/Projects/jimigpt-reviews/F01/tests/personality/test_tone_intent.py:101, /C:/shekar73/Documents/Projects/
     jimigpt-reviews/F01/tests/personality/test_prompt_builder.py:98
     Issue: there are no tests for invalid weight keys, negative weights, cross-product blends, missing tone_defaults,
     invalid intent names, or the richer F02 prompt inputs.
     Impact: the most likely future regressions are currently unguarded.
     Suggested fix: add explicit failure tests for these cases before F02 starts depending on them.

  ### Observations

  - The 8 current JimiGPT archetype YAMLs do include tone_defaults, use valid current intent names, and their
    intent_weights sum to 1.0 from inspection of the files under config/archetypes/jimigpt/.
  - models.py stays entity-agnostic; the pet-specific extension is cleanly isolated in /C:/shekar73/Documents/Projects/
    jimigpt-reviews/F01/src/personality/pet_profile.py.
  - blend_archetypes() is materially over the “functions under 30 lines” guideline; even if behavior is fixed, it would
    be easier to maintain if split into validation, dominant-field selection, and merged-field assembly helpers.

  ### Strengths

  - The entity-agnostic vs. pet-specific separation is mostly disciplined.
  - The current archetype YAML set is internally consistent and readable.
  - Tests cover most public happy paths and the end-to-end YAML -> blend -> PetProfile -> prompt path.
  - AssembledPrompt already carries structured blocks, which is the right direction even though the current block set is
    too narrow.

  ### Summary

  The feature is a solid Phase 1 foundation, but two interface-level issues are blocking: blend_archetypes() does not
  validate its weight contract tightly enough, and assemble_prompt() is not yet shaped like the documented bridge F02
  needs. The existing codebase is readable and mostly well-tested, but schema validation and prompt-builder contracts
  need to be tightened before this becomes a stable platform for the message pipeline.

  Verification: I reviewed the referenced docs, source, tests, and archetype YAMLs. I also ran the test suite; 142 tests
  passed, and 2 failed only because tmp_path tried to use a sandbox-blocked temp directory rather than due to feature
  logic.
