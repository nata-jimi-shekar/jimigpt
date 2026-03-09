# F04: Trust & Safety System

**Phase:** 1B  
**Priority:** 4  
**Architecture Reference:** Category Architecture Sections 6, 7  
**JimiGPT Reference:** JimiGPT Architecture Sections 6, 8  

## Feature Description

Build the trust ladder (progressive relationship deepening) and the safety
escalation system. Trust stage affects message tone and depth. Escalation
detects when a user needs more than an AI companion can provide.

## Dependencies
- F01 (Personality Engine) — trust modifies personality behavior
- F02 (Message Pipeline) — trust stage is part of message context

## What "Done" Looks Like
- Trust stage evaluates and progresses based on interaction signals
- Message generation adapts to current trust stage
- Escalation detects distress signals and responds appropriately
- JimiGPT-specific vet deflection works
- All tests pass

---

## Micro-Tasks

### Task 1: Trust Models
**Time:** 20 min  
**Context:** Read docs/category-architecture.md Section 6  
**What to do:**
- Create src/trust/__init__.py
- Create src/trust/ladder.py with:
  TrustStage enum, TrustProfile model, TrustEvent model
- Write tests/trust/test_ladder.py for model validation  
**Done when:** Models validate, tests pass  
**Commit:** `feat(trust): add trust stage and profile models`

### Task 2: Trust Stage Evaluation
**Time:** 25 min  
**Context:** Read docs/jimigpt-architecture.md Section 6 (Stage-Specific Behavior)  
**What to do:**
- Add evaluate_trust_progression(profile: TrustProfile) -> TrustStage
- Progression rules: stranger→initial (24h + 3 interactions),
  initial→working (7 days + 10 interactions), etc.
- Write tests:
  - New user starts at STRANGER
  - Progression after meeting thresholds
  - No regression (trust never goes backward)
  - Multiple simultaneous signals handled  
**Done when:** Trust progression evaluates correctly  
**Commit:** `feat(trust): add trust stage progression evaluation`

### Task 3: Escalation Detection
**Time:** 25 min  
**Context:** Read docs/category-architecture.md Section 7, JimiGPT Architecture Section 8  
**What to do:**
- Create src/trust/escalation.py with:
  EscalationLevel enum, EscalationSignal model
  assess_escalation(user_message, history, product_rules) -> EscalationSignal
- JimiGPT rules: vet deflection, basic distress detection
- Write tests:
  - Normal messages → Level 0
  - Pet health questions → vet deflection response
  - Distress language → Level 2 with support suggestion
  - Crisis language → Level 3 with resources  
**Done when:** Escalation correctly identifies signal levels  
**Commit:** `feat(trust): add escalation detection for JimiGPT`

### Task 4: Trust Integration with Message Context
**Time:** 20 min  
**Context:** Read F02 Task 5 (Message Context)  
**What to do:**
- Update MessageContext to include trust_stage from TrustProfile
- Update prompt builder to include trust-aware instructions
  (stranger = gentle, working = reference past, deep = reflect patterns)
- Write test: same entity produces different prompt at different trust stages  
**Done when:** Trust stage affects prompt generation  
**Commit:** `feat(trust): integrate trust stage with message generation`

---

## Task Summary

| # | Task | Time | Depends On |
|---|------|------|------------|
| 1 | Trust models | 20 min | F01, F02 |
| 2 | Trust stage evaluation | 25 min | Task 1 |
| 3 | Escalation detection | 25 min | Task 1 |
| 4 | Trust-message integration | 20 min | Task 2, F02 |

**Total estimated time:** ~1.5 hours (4 reps, 1 daily session)
