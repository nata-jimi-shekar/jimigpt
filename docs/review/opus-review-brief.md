# Opus Review Brief — Task-Level
## High-Blast-Radius Code Review

> **Copy this template, fill in the bracketed sections, and paste to Opus.**
> One task per review. Focus on the specific concerns listed.

---

## Instructions for Opus

You are reviewing code for JimiGPT, an Emotional AI product that creates
Digital Twin companions for pets. This code sends personalized text messages
to real people about their real pets. Errors in this code have direct
emotional impact on users.

**Your role:** Read-only code reviewer. You do NOT write code. You identify
issues and explain why they matter. Be specific — cite file names and line
numbers. Prioritize by blast radius (what hurts a user vs. what hurts dev speed).

**Architecture source of truth:** The architecture docs listed below are the
canonical decisions. If you see code that deviates from these docs, flag it.
If you think the architecture is wrong, say so separately — but the code
should match the docs as they exist.

---

## Project Context

- **Product:** JimiGPT — Digital Twin for Pets. Sends contextual SMS messages
  in the pet's personality voice. Celebration-first positioning.
- **Stack:** Python 3.12+, FastAPI, Pydantic v2 (strict mode), pytest, Ruff, mypy --strict
- **Key principle:** Entity-agnostic engine code. Pet-specific logic in config/YAML only.
  Everything must work for a different product (NeuroAmigo) with config changes only.

## Feature Being Reviewed

- **Feature:** [F## — Feature Name]
- **Task:** [T## — Task Name]
- **Feature doc:** [paste or reference docs/features/F##.md]
- **Architecture references:** [list relevant sections from docs/]

## Files to Review

```
[List the specific files this task created or modified]
src/messaging/intent.py
src/messaging/tone.py
tests/messaging/test_intent.py
tests/messaging/test_tone.py
config/tone_rules.yaml
```

## What This Code Does

[2-3 sentences describing what this task implements and why it matters]

## Specific Review Concerns

Focus your review on these areas. Skip cosmetic issues — Ruff and mypy
handle those.

### For ALL High-Blast-Radius Tasks:
1. **Emotional safety:** Could this code produce a message that harms a user
   emotionally? Wrong tone at wrong time? Inappropriate intimacy level?
2. **Edge cases at boundaries:** What happens at midnight? On holidays? When
   signals are missing? When the user hasn't replied in 30 days?
3. **Graceful degradation:** When a signal source fails or returns unexpected
   data, does the system produce a safe default or does it crash/produce garbage?
4. **Architecture conformance:** Does this code match the documented architecture?
   Are entity-agnostic and pet-specific concerns properly separated?
5. **Test coverage of failure modes:** Tests exist for happy paths — do they
   also cover the dangerous paths? Missing signal data, extreme values, 
   concurrent access?

### Feature-Specific Concerns:

**If F02 (Message Pipeline):**
- Does intent selection produce appropriate emotional intents for each trigger
  type + signal combination?
- Can tone calibration produce values outside 0.0-1.0 after stacking adjustments?
- Does the quality gate catch messages that don't match the intended tone/intent?
- Is the composed prompt structure complete (all 8 blocks) and well-formed?
- Could the LLM receive a prompt that produces an emotionally unsafe message?

**If F03 (Delivery Layer):**
- Can a message EVER be delivered during quiet hours? Trace all code paths.
- What happens if Twilio fails mid-delivery? Is the message marked correctly?
- Can retry logic cause duplicate SMS sends?
- Timezone handling: does it work for UTC+14, UTC-12, DST transitions?

**If F04 (Trust & Safety):**
- Can trust ever regress? Should it? Trace the evaluation logic.
- Escalation: what user messages does the detector MISS? Think adversarially.
- Vet deflection: can a pet health question slip through without the deflection?
- Does the trust stage correctly modulate message generation prompts?

**If F05 (Database, Auth, Payments):**
- SQL injection: are all queries parameterized?
- Auth: can a user access another user's entity or messages?
- Stripe webhook: can a replayed or forged webhook change subscription state?
- Schema: are there missing indexes, wrong constraints, or data that should
  be encrypted at rest?

## Output Format

Structure your review as:

### Critical (Fix Now)
Issues that could cause emotional harm, data loss, security breach, or
incorrect message delivery. Each with: file, line, issue, why it matters,
suggested fix direction.

### Important (Fix Later)
Valid issues that don't cause immediate harm but weaken the system.
Missing edge case handling, suboptimal patterns, test gaps.

### Architecture Notes
Deviations from documented architecture, or suggestions that the
architecture itself should be updated.

### What Looks Good
Briefly note what's working well. This helps calibrate trust in the review.
