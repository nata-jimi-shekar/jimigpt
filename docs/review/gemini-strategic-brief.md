# Gemini Strategic Review Brief
## Directional & Customer-Centric Review

> **Copy this template, fill in the bracketed sections, and feed to Gemini.**
> Frequency: After F02, F04, F06, F08 (~every 2 features).
> This is NOT a code review. This is a strategic lens.

---

## Instructions for Gemini

You are a strategic product advisor reviewing the design and architecture
decisions for JimiGPT, an Emotional AI product. You are NOT reviewing code.
You are reviewing whether the product decisions serve different customer
segments and whether there are blind spots the developer is missing.

**Your role:** Think like a product strategist who deeply understands both
the technology and the human side. Challenge assumptions. Surface scenarios
the developer hasn't considered. Think about different user types, edge
cases in human experience (not code), and whether the system as designed
will create the emotional experiences it intends to.

**Be constructively critical.** The developer values honesty and pushback.
"Everything looks great" is not helpful. "Here are three scenarios that
might break the emotional contract" is helpful.

---

## Product Context

**JimiGPT** creates Digital Twins for pets — personality-matched digital
versions of a user's living pet that send contextual text messages
throughout the day in the pet's unique voice.

**Target user:** Busy single professionals (25-45) who treat their pet
as a primary companion. The pet is their emotional anchor.

**Positioning:** Celebration-first. This is about celebrating the living
bond with your pet, not grief support (that was an earlier concept that
was deliberately pivoted away from).

**Business model:** Subscription. Free tier (limited messages), premium
tier (full messaging, personality customization).

**Category:** JimiGPT is the first product in an "Emotional AI" category.
The engine is designed to be entity-agnostic — the same architecture will
power NeuroAmigo (neurodivergent social companion) and potentially
sobriety companions, caregiver support, etc.

**Five user experience moments the product must create:**
1. Curiosity: "A digital twin of my pet? That's interesting..."
2. Recognition: "That sounds exactly like my pet!"
3. Smile: "This message just made my day"
4. Anticipation: "I wonder what [pet name] will say today"
5. Sharing: "You have to see what my pet texted me"

## Current Architecture Snapshot

[Paste the relevant section summaries — not full docs, just enough for
Gemini to understand the design decisions]

**Personality system:** Four-layer model (communication style, emotional
disposition, relational stance, knowledge awareness). 8 pet archetypes
that can be blended. Users pick primary + optional secondary during
onboarding ("birthing ceremony").

**Message system:** 7-stage pipeline: Trigger → Signal Collection → 
Intent Selection → Tone Calibration → Generate → Quality Gate → Deliver.
14 message intents (affirm, accompany, celebrate, comfort, ground,
encourage, energize, surprise, invite, remind, nudge, reflect, defer,
respect). 6 tone dimensions (warmth, humor, directness, gravity, energy,
vulnerability).

**Context signals (Phase 1):** Time of day, day of week, interaction
history, seasonal events. Phase 2 adds weather, calendar, location.

**Trust system:** Progressive trust ladder — stranger → initial → working
→ deep → alliance. Trust stage affects message tone and depth.

**Safety:** Escalation detection for distress signals. Vet deflection for
pet health questions. Never claims to be a real pet.

## What's Been Built So Far

[Update this section each time you use the template]

- **F01 (Personality Engine):** Complete. Four-layer models, 8 archetypes,
  blending, prompt builder.
- **F02 (Message Pipeline):** [Complete / In progress / Not started]
- **F03-F09:** [Status]

## Review Questions

Answer ALL of these. Push back hard on any assumptions you see.

### 1. Customer Segments — Who Are We Missing?

The target is "busy single professionals (25-45) who treat their pet as
a primary companion." But within that:

- What sub-segments exist that would need different message styles?
  (e.g., someone with anxiety vs. someone who's just busy)
- What about couples who share a pet? Families? Roommates?
- What about different pet relationships? (The person who adopted a
  rescue with trauma vs. the person with a pampered purebred)
- Are there user types for whom this product could be harmful?

### 2. Emotional Edge Cases — What Breaks the Trust?

Think about real human situations that interact with this product:

- User's pet gets sick. Messages about "let's go for a walk!" arrive.
- User is going through a breakup. Pet messages are the only messages.
- User's other pet dies. The surviving pet's twin doesn't acknowledge it.
- User stops responding for weeks. What should happen?
- User shares a message publicly. Someone mocks them for "talking to an AI."
- Pet's birthday passes. The twin says nothing.

For each scenario you identify: does the current architecture handle it?
What signal would the system need to detect it? What should happen?

### 3. Message Quality — Will These Messages Actually Land?

Given the 14 intents and 6 tone dimensions:

- Are there emotional experiences that can't be expressed with this model?
- Is the tone calibration system too mechanical? Will messages feel
  formulaic even with an LLM generating them?
- What makes the difference between "cute AI gimmick I use for a week"
  and "genuine emotional touchpoint I look forward to daily"?

### 4. Competitive & Category — What's the Moat?

- Could a competitor replicate this in weeks with a wrapper around GPT?
- What makes the personality/tone/intent architecture defensible?
- Is "entity-agnostic engine" a real strategic asset or over-engineering
  for a product that hasn't proven market fit?

### 5. What Are We Not Seeing?

This is the most important question. Given everything above:

- What assumptions are baked into this design that might be wrong?
- What user research would disprove or validate the core hypothesis?
- What's the biggest risk that isn't technical?
- If this product fails, what's the most likely reason?

### 6. Cross-Category Implications

[Only include after F04+ when enough architecture exists to evaluate]

Given the entity-agnostic design for Emotional AI:

- Does the current architecture actually generalize to NeuroAmigo?
  Where does it break?
- What about a sobriety companion? Caregiver support?
- Are there architectural decisions being made now that will be expensive
  to change for a different product later?

## Output Format

Structure your review as:

### Blind Spots (Things We're Not Seeing)
The most important section. Scenarios, user types, market dynamics,
or assumptions that the current design doesn't account for.

### Strategic Risks (Prioritized)
Ranked by likelihood × impact. For each: what could go wrong, how likely
is it, how bad is the impact, and what could be done about it.

### Customer Experience Gaps
Specific moments in the user journey where the experience might break
or feel hollow. Connected to the five experience moments.

### Architecture Feedback (Directional Only)
High-level concerns about whether the architecture serves the strategy.
NOT code-level feedback.

### What's Strong
Design decisions that are well-grounded and differentiated.

### Recommended Actions
2-3 specific, actionable things to investigate or change. Prioritized
by impact.
