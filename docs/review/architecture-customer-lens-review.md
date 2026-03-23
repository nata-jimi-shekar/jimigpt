# Architecture Review: Customer Lens
## What the Message System Needs to Serve Real Human Lives

**Reviewer:** Claude Opus (Desktop Planning Chat)
**Date:** March 2026
**Scope:** docs/message-modeling.md, docs/features/F02-message-pipeline.md,
docs/category-architecture.md, docs/jimigpt-architecture.md
**Lens:** Customer experience, emotional resonance, real-world use cases

> This review examines the architecture from the perspective of real people
> living real lives with their pets. The question is not "does the code work?"
> but "does this architecture serve the full range of human situations where
> a Digital Twin would be valuable?"

---

## Executive Summary

The message modeling architecture is strong on the *mechanics* of individual
message generation — personality voice, tone calibration, intent selection,
and quality gating are well-designed. What's missing is the *choreography*
layer: how messages relate to each other over time, how they serve multiple
people, and how they respond to life events rather than just clock time.

The architecture models messages as independent units. Real emotional
experiences are arcs. Fixing this doesn't require rebuilding — it requires
adding a composition layer above the existing pipeline.

**Six gaps identified, ranked by customer impact:**

1. Message Sequences & Emotional Arcs (HIGH — affects daily experience)
2. Multi-Recipient Architecture (HIGH — unlocks new customer segments)
3. Life Event Awareness (MEDIUM — differentiates from "novelty toy")
4. Multi-Pet Coordination (MEDIUM — affects household experience)
5. User-Initiated Context (MEDIUM — enables personalization)
6. Professional/B2B Channel (LOW priority now — HIGH future value)

---

## Gap 1: Message Sequences & Emotional Arcs

### What the Architecture Has
Each message is composed, generated, and delivered independently. The
pipeline runs once per trigger, produces one message, delivers it. The
`recent_messages` field in MessageComposition provides some history
awareness, but only for avoiding repetition — not for narrative continuity.

### What Real Life Needs

**Scenario: Feeding time**
A user sets feeding time at 6pm. The current architecture sends ONE message
at 6pm: "DINNER TIME!" But a real pet's relationship with food is a
*sequence*:

- 5:30pm: "I can tell it's almost time. I'm positioning myself near the
  kitchen. Casually."
- 5:55pm: "Five minutes. I'm counting. Don't think I can't tell time."
- 6:00pm: "IT'S TIME. IT'S TIME. IT'S TIME."
- 6:15pm (if no response): "Hello?? Did you forget about me?? I'm wasting
  away here."

This sequence IS the personality. A single message at 6pm is a notification.
A sequence is a living pet.

**Scenario: Bad weather day**
Rain starts at 2pm. The architecture (Phase 2) would detect weather:rainy
and adjust tone. But what's actually delightful is an *arc*:

- 2pm: "It's getting dark out there. Perfect nap weather."
- 4pm: "Still raining. I've claimed the blanket. Non-negotiable."
- 6pm: "Rainy evening = couch time. Get home. I have plans for us."

Three messages across an afternoon that weave a coherent emotional thread
around one context signal. This is what "How did it know?" feels like.

**Scenario: User is sick**
User tells the system (or it infers from silence + context) that they're
unwell. The response shouldn't be one "feel better!" message. It should be
a gentle arc across the day:

- Morning: Quieter than usual. "Hey. Still here. No demands today."
- Midday: "Just checking. You don't have to reply. I'm napping nearby."
- Evening: "You made it through another day. That counts."

The *restraint* in the sequence (fewer messages, lower energy, no demands)
IS the emotional payload. A single message can't communicate "I noticed
you're not okay and I'm adjusting my whole behavior."

### What Needs to Change in the Architecture

**New concept: MessageArc**
```
MessageArc:
  arc_id: str
  arc_type: str  # "feeding_anticipation" | "weather_day" | "sick_day" | etc.
  trigger_context: ContextSignalBundle  # What initiated this arc
  messages: list[ArcMessage]  # Ordered sequence with relative timing
  arc_tone: ToneSpectrum  # Overall emotional register for the arc
  escalation_rules: dict  # How the arc adapts if user responds/doesn't
  can_interrupt: bool  # Can other triggers interrupt this arc?
  max_duration_hours: int

ArcMessage:
  position: int  # 1, 2, 3... within the arc
  offset_minutes: int  # Minutes after arc starts
  intent: MessageIntent
  tone_modifier: dict  # How this message's tone differs from arc baseline
  condition: str | None  # "no_response_to_previous" | "user_replied_positive"
```

This sits ABOVE the existing pipeline. The trigger evaluator decides
whether to fire a single message OR initiate an arc. Each arc message
flows through the existing 7-stage pipeline individually — the arc just
orchestrates timing and narrative continuity.

### Implementation Note
This is NOT an F02 change. The current F02 scope is correct for Phase 1.
But the MessageComposition model should include an `arc_id: str | None`
field and `arc_position: int | None` field NOW, so that when arcs are
built (Phase 2), the foundation is there. Add these as optional fields
in F02-T10 (Message Composer).

---

## Gap 2: Multi-Recipient Architecture

### What the Architecture Has
One entity → one user. The database schema has `user_id` on entities and
messages. The entire pipeline assumes a single recipient.

### What Real Life Needs

**Scenario: Single mother with two teen kids**
Mom creates a Digital Twin of the family dog. She wants:
- Messages to HER phone: caring check-ins, emotional support, the full
  personality experience
- Messages to KID 1's phone: "Hey, your room looks like a tornado hit it.
  I can't find my favorite nap spot. Clean up please? 🐾"
- Messages to KID 2's phone: "Homework time! I believe in you. Also I
  want treats when you're done."

The pet's PERSONALITY stays the same. But the RELATIONSHIP and INTENT are
different per recipient. The dog is a companion to mom, a playful nag to
the kids. The tone calibration shifts. The trust stage is different per
person.

**Scenario: Couple with a pet**
Both partners receive messages from the same Digital Twin. But:
- Partner A gets "I miss you, come home soon" (emotional)
- Partner B gets "Don't forget to pick up my food on the way home" (practical)
- Both get "You two are my favorite humans" (shared)

The entity needs to understand that Partner A and Partner B have different
RecipientPreferences, different schedules, and different relationships
with the pet.

**Scenario: Indirect communication through the pet**
Couple had a minor argument. Neither wants to text first. But the pet
"notices" the tension and sends:
- To Partner A: "Hey, {partner_B_name} seemed a little quiet this morning.
  Just saying. Maybe a treat would help? Treats fix everything."
- To Partner B: "{partner_A_name} gave me extra belly rubs today. I think
  they're feeling things. You know what to do."

The pet becomes a *social mediator*. This is profound because the pet's
voice provides emotional distance that makes repair feel safe. Nobody is
being vulnerable — the DOG is being vulnerable.

**Scenario: Elderly parent lives alone**
Adult child sets up JimiGPT for their parent's cat. The parent gets
daily messages from "Whiskers." But the adult child also gets a
weekly summary: "Your mom and I had a good week. She responded to 4
messages. She seemed happiest on Tuesday when I sent her that message
about the sunny windowsill."

The entity serves both the primary user AND a caretaker/family member
with different message types and different purposes.

### What Needs to Change in the Architecture

**New concept: EntityRecipient (many-to-many)**
```
EntityRecipient:
  entity_id: str
  recipient_id: str  # References a user_profile
  relationship_type: str  # "primary_owner" | "family_member" | "partner" | "child"
  recipient_role: str  # "companion" | "playful_nag" | "mediator" | "monitor"
  recipient_preference: RecipientPreference  # Per-recipient preferences
  trust_stage: TrustStage  # Per-recipient trust
  trigger_schedule: list[TriggerRule]  # Different schedule per person
  message_categories_enabled: list[str]  # Which message types this person gets
  tone_overrides: dict  # Per-recipient tone adjustments
```

**Database impact:**
- `entities` table gains `is_shared: bool`
- New `entity_recipients` table replaces the assumption of entity.user_id
  being the sole recipient
- `messages` table already has `user_id` — this becomes the recipient_id
- `trust_events` and `recipient_preferences` are already per-user — this works

### Implementation Note
This is a Phase 2-3 feature. But the architectural decisions in F02 and
F05 should NOT make it harder to add later. Specifically:
- F02: The MessageComposer should take a `recipient_id` parameter, not
  assume it from the entity. Even if in Phase 1 there's always one
  recipient, the interface should be ready.
- F05: The database schema should not have a UNIQUE constraint on
  entity_id + user_id in the messages table. Multiple recipients means
  the same entity sends to different users.

---

## Gap 3: Life Event Awareness

### What the Architecture Has
Context signals: TIME (always), INTERACTION, SEASONAL (Phase 1).
WEATHER, CALENDAR, LOCATION (Phase 2-3). These are all *ambient* signals —
the system observes the world passively.

### What Real Life Needs

**Active life events that change the entire message strategy:**

| Life Event | Duration | Message Strategy Change |
|-----------|----------|----------------------|
| User is sick | Days | Fewer messages, lower energy, no demands, comfort-forward |
| Pet is at the vet | Hours-day | Reassurance messages, "I'm being brave" voice |
| Pet is boarding | Days | "Missing you" arc, daily check-in tone |
| User is traveling | Days-weeks | "The house is so quiet" arc, countdown to return |
| New pet in household | Weeks | Adjustment arc, jealousy/curiosity personality moments |
| User got a new job | Days | Celebration then "new routine" adjustment |
| Seasonal depression period | Weeks | Gentler, warmer, more consistent check-ins |
| User is grieving (human loss) | Weeks-months | Restraint, presence, no forced cheerfulness |
| Pet's birthday / adoption day | Day | Celebration arc, special messages |
| Breakup / relationship change | Weeks | Extra companionship, no references to the ex |

The current architecture has no concept of a "life event" that modifies
the *overall messaging strategy* for a period of time. Each trigger
evaluation is stateless — it doesn't know "we're in the middle of a
travel arc" or "the user told us yesterday they're sick."

### What Needs to Change

**New concept: LifeContext (persistent, user-set or inferred)**
```
LifeContext:
  user_id: str
  context_type: str  # "user_sick" | "pet_vet" | "user_traveling" | etc.
  started_at: datetime
  expected_end: datetime | None
  source: str  # "user_reported" | "inferred" | "calendar"
  active: bool
  strategy_overrides: dict  # How this changes message generation
    # frequency_modifier: 0.7  (fewer messages)
    # energy_cap: 0.4  (calmer)
    # preferred_intents: ["comfort", "accompany", "affirm"]
    # blocked_intents: ["energize", "remind"]
    # arc_template: "sick_day"  (use this message arc)
```

This slots into the pipeline at Stage 2 (Signal Collection). Active
LifeContexts are loaded alongside time/weather/interaction signals and
passed into the MessageComposer.

**How users set it:** Simple in-app controls or reply keywords.
- Reply "quiet mode" → system reduces messages
- Reply "I'm sick" → system activates sick_day LifeContext
- Reply "traveling" → system activates travel LifeContext
- In-app: toggle states like "My pet is at the vet today"

### Implementation Note
The LifeContext model should be designed in F02 even if the full
implementation waits. The MessageComposition model should include a
`life_contexts: list[LifeContext]` field. In Phase 1, this list is
always empty. But the field exists for Phase 2.

---

## Gap 4: Multi-Pet Coordination

### What the Architecture Has
docs/message-modeling.md Section 7 describes EntityRelationship and
EntityWorldModel — two pets aware of each other, with relationship
descriptions. This is good but it's Phase 3 and only covers *content*
awareness (Luna can reference Max). It doesn't cover *scheduling*
coordination.

### What Real Life Needs

**Scenario: Family has a Chaos Gremlin dog and a Regal One cat**

Without coordination:
- 8:00am: Dog sends high-energy morning message
- 8:05am: Cat sends dignified morning message
- Two messages in 5 minutes feels like spam, not two distinct personalities

With coordination:
- 8:00am: Dog sends morning chaos
- 10:30am: Cat sends morning judgment (deliberately spaced)
- 3:00pm: Dog references cat: "Luna just STARED at me for 10 minutes.
  I think she's plotting something."
- 5:00pm: Cat references dog: "Max is pacing near the door. Apparently
  you're 'almost home.' He's been saying that for an hour."

The coordination creates the feeling of a *household*, not two independent
chatbots. The personalities play OFF each other. This is where the magic
compounds — one entity is interesting, two entities with a relationship
are a world.

### What Needs to Change

**Entity scheduling coordination:**
The batch pre-generation pipeline (category-architecture.md Section 5)
needs to be aware of other entities belonging to the same user. When
generating messages for User A who has Entity 1 and Entity 2:

1. Generate triggers for both entities
2. Space them out (minimum 90 minutes between entities)
3. Optionally allow cross-references (Entity 1 mentions Entity 2)
4. Maintain distinct personality voices — coordination is about timing
   and awareness, not homogenization

### Implementation Note
F02-T4 (Trigger Evaluation Orchestrator) should accept an
`other_entity_schedules: list[dict]` parameter. In Phase 1 with single-pet
users, this is always empty. But the interface is ready for multi-pet.

---

## Gap 5: User-Initiated Context

### What the Architecture Has
Messages are outbound-only in terms of design. The user can react
(thumbs up/down) and reply, but the system treats replies primarily
as effectiveness signals, not as context input.

### What Real Life Needs

**Users want to TELL the pet things.** Not in a chatbot conversation
(that's a different product), but as quick context drops:

- "We're going to the park!" → Pet responds with excitement AND the
  next few messages reference the park outing
- "Bad day at work" → Pet shifts to comfort mode for the rest of the day
- "Guess what? I got promoted!" → Celebration arc activates
- "Max learned to shake today!" → Pet references the new trick with pride

These aren't conversations. They're *context injections* — the user gives
the pet information that changes the messaging strategy for a period.

### What Needs to Change

**User context replies are a signal source, not a chat feature:**
Add to ContextSignalSource:
```
USER_CONTEXT = "user_context"  # User-initiated context injection
```

When a user replies to a pet message, the system:
1. Classifies the reply (sentiment already exists)
2. Extracts context signals if present (park, bad day, promotion, etc.)
3. Creates a short-lived ContextSignal or LifeContext based on the content
4. Next triggered message incorporates this context

This is NOT a chatbot. The pet doesn't respond immediately to every reply.
The pet *absorbs* the information and weaves it into the next natural
message. This is more like how a real pet "knows" — they don't respond
with words, but their behavior changes.

### Implementation Note
F02-T6 (INTERACTION signal collector) already captures
`last_response_sentiment`. Extend the design to also capture
`last_response_context_tags: list[str]` — extracted keywords or
classified categories from the user's most recent reply. This feeds
into the signal bundle naturally.

---

## Gap 6: Professional/B2B Channel

### What the Architecture Has
Nothing. This isn't in any document.

### What Real Life Needs

**Scenario: Veterinary practice**
A vet clinic wants to improve client engagement and appointment adherence.
Instead of generic reminder texts ("Your appointment is tomorrow at 2pm"),
the reminder comes from the pet:

- "Hey! I have a checkup tomorrow. I'm nervous but I know it's important.
  Can we go to the park after? Please?"
- (Day of): "On my way to see the vet people. If I'm extra good, I get
  treats. Wish me luck!"
- (After visit): "I was VERY brave. Dr. Chen said I'm healthy. I think
  I deserve a new toy."

**Scenario: Pet supply store**
Monthly heartworm medication reminder: "It's that time of the month.
The tiny treat that apparently keeps bugs away. I'll take it but I won't
be happy about it."

**Scenario: Dog walker / pet sitter**
While owner is traveling: "Your walker Sarah took me to the big park
today! We met a poodle named Chester. I was not impressed."

### Architectural Implications

This requires a concept the current architecture doesn't have:
**MessageSource** — who is initiating/paying for the message.

```
MessageSource:
  source_type: str  # "organic" | "professional" | "scheduled_external"
  source_id: str | None  # Business account ID
  source_context: dict  # Appointment details, product info, etc.
  content_boundary: str  # What the source CAN and CANNOT communicate
  approval_required: bool  # Does the pet owner approve these messages?
```

The critical constraint: the pet owner ALWAYS has veto power. A vet can
send messages through the pet's voice only with the owner's opt-in, and
the owner can disable it anytime. The pet's voice is sacred — it's the
owner's emotional relationship. Businesses are guests in that space.

### Implementation Note
This is Phase 3 or later. Park it. But the trust framework principle
is important to document now: **no entity speaks without the primary
owner's consent.** This should be added to the Trust & Authenticity
Framework and referenced in F04 (Trust & Safety).

---

## Additional Human Situations the Architecture Should Serve

Beyond what Nata identified, here are situations where a pet Digital Twin
is natively valuable and the architecture should eventually support:

### 1. Latchkey Kids
Child comes home from school to an empty house. Pet messages:
"I HEARD THE DOOR! YOU'RE HOME! Did you have a good day? I saved you a
spot on the couch."

The pet provides a sense of "someone is home" for the child. This is
the multi-recipient architecture (Gap 2) — parent sets this up, child
receives age-appropriate messages.

**Architecture need:** Age-appropriate content filtering per recipient.
A child recipient should never receive messages about alcohol, dating,
work stress, etc. Content boundaries become per-recipient, not just
per-entity.

### 2. Remote Worker Isolation
Person works from home alone all day. The pet's messages become the
"coworker check-ins" they're missing:

- 10am: "Productivity check! You've been at that desk for 2 hours.
  Time for a stretch. I'll supervise."
- 12pm: "Lunch break. I'm already at my bowl. Race you."
- 3pm: "Afternoon slump? Same. I'm going to nap. Join me."

**Architecture need:** Calendar integration (Phase 2) makes these
contextually aware. But even without calendar, the time-based triggers
can serve this well. The key is the *framing* — the pet isn't nagging,
it's being a companion through the workday.

### 3. Pet at Boarding/Daycare
Owner leaves pet at boarding for a trip. The Digital Twin keeps "sending
messages" but the voice shifts:

- "Day 1 at the hotel. My roommate snores. I miss your pillow."
- "Day 3. I made a friend named Biscuit. Don't be jealous."
- "Coming home tomorrow!! I have SO much to tell you."

**Architecture need:** This is a LifeContext (Gap 3) — "pet_boarding"
activates a specific message arc that simulates the pet's boarding
experience. Delightful because it fills the silence while owner and
pet are apart.

### 4. Anticipation Before Coming Home
The daily moment when the owner is about to leave work and head home.
If the architecture has calendar or location signals:

- "I can SENSE it. You're almost done. Are you leaving soon? I'm
  already at the door."
- (GPS detects leaving work): "You're on your way!! I'll be waiting.
  WAITING. WAITINGGGGG."

**Architecture need:** Location signals (Phase 3) make this magical.
But even without GPS, a time-based trigger at the user's usual
commute time serves 80% of the value.

### 5. Anniversary and Milestone Moments
The SEASONAL signal source covers holidays and entity anniversary. But
there are more personal milestones:

- "1 month since you created my Digital Twin" — meta-milestone
- "Happy 3rd gotcha day!" — adoption anniversary (user-provided date)
- "Your birthday is tomorrow! I don't know what to get you. How about
  extra cuddles?" — owner birthday
- "100 messages together. You've replied to 73 of them. I'm keeping
  count." — interaction milestone

**Architecture need:** These are mostly in the SEASONAL signal source
already. The key missing piece is *user-provided dates* (pet birthday,
adoption day, owner birthday) collected during birthing or settings.
These should be stored on PetProfile or UserProfile and surfaced as
seasonal signals.

### 6. Supporting the Owner Through Pet's Health Journey
When a pet gets a serious diagnosis, the Digital Twin becomes a source
of strength rather than a reminder of mortality:

- "Dr. Chen says I need medicine every day now. That's okay. More
  treats, right?"
- "I'm having a good day today. Let's not waste it on worrying."
- "You look at me differently now. I'm still me. Still here. Still
  want belly rubs."

This is the most emotionally powerful use case and the most dangerous.
The architecture must handle it with extreme care. The celebration-first
positioning doesn't mean avoiding illness — it means the pet faces
illness with the same personality it always had. The Chaos Gremlin is
still chaotic at the vet. The Loyal Shadow is still devoted during
treatment.

**Architecture need:** This is a LifeContext (Gap 3) — "pet_health_journey"
with very specific tone constraints. Gravity increases. Energy may
decrease. But humor and warmth remain personality-led, not illness-led.
The quality gate needs special rules: no toxic positivity ("Everything
will be fine!"), no forced sadness, no medical claims.

### 7. Pet Passing and Memorial Transition
Listed in the roadmap (Phase 3) but worth emphasizing from the customer
lens: the transition from living pet messaging to memorial mode should
be gradual, not a switch. The pet doesn't "die" in the digital world —
it transitions to memory:

- Last few messages: "I had the best life with you. You know that, right?"
- After: Messages shift to memory voice. "Remember that time at the
  beach? Best day ever." Less frequent. More reflective. Still in
  the pet's voice.

**Architecture need:** A TrustStage transition beyond ALLIANCE —
perhaps MEMORIAL. The personality stays the same but the intent
distribution shifts heavily toward REFLECT, CELEBRATE, ACCOMPANY.
Energy drops. Gravity and vulnerability increase. Frequency decreases
to maybe 1-2 per week.

---

## F02 Specific Recommendations

Given the above gaps, here's what should change in F02's *design* (not
necessarily its implementation scope — some of these are field additions,
not feature additions):

### Add to MessageComposition (F02-T10):
```python
# Future-proofing fields — optional, None in Phase 1
arc_id: str | None = None           # Which message arc this belongs to
arc_position: int | None = None     # Position within arc
recipient_id: str | None = None     # Explicit recipient (not just entity owner)
life_contexts: list[str] = []       # Active life contexts
entity_coordination_id: str | None = None  # For multi-pet scheduling
```

### Add to ContextSignalBundle (F02-T5):
```python
# Add USER_CONTEXT to ContextSignalSource enum
USER_CONTEXT = "user_context"

# In the signal collection, extract from last user reply:
# - sentiment (already planned)
# - context_tags: list[str]  e.g. ["park", "celebration", "bad_day"]
```

### Add to TriggerRule (F02-T1):
```python
# Future-proofing fields
arc_template: str | None = None     # If this trigger starts an arc
sibling_entity_ids: list[str] = []  # Other entities for same user
```

### Verify in Quality Gate (F02-T12):
- Add a check for "emotional arc coherence" — even if arcs aren't
  built yet, the quality gate should verify that consecutive messages
  to the same user don't contradict each other emotionally (e.g.,
  high-energy message 30 minutes after a comfort message)

### Verify in Intent Selection (F02-T7):
- The intent selection should weight CELEBRATE and SURPRISE higher
  on milestones and special dates — currently the architecture
  mentions this in SEASONAL signals but the F02 task description
  doesn't explicitly call it out

---

## What I Might Be Missing (Self-Reflection)

1. **Cultural context:** The archetype descriptions and message examples
   are very Western/American. A user in Colombia, Japan, or Saudi Arabia
   has different cultural relationships with pets. The architecture has
   no concept of cultural calibration. This matters for international
   expansion but probably not for MVP.

2. **Accessibility:** No mention of how messages serve users with
   disabilities. A visually impaired user receiving SMS is fine, but
   the emoji-heavy style of some archetypes may not translate well to
   screen readers. Consider an accessibility mode that adjusts
   communication style.

3. **Pet species beyond dogs and cats:** The archetypes are heavily
   dog/cat oriented. A bird, rabbit, hamster, or fish owner exists.
   The four-layer personality model should work for any species, but
   the archetype YAML files are mammal-biased. Phase 2 could add
   species-specific archetype packs.

4. **The "novelty cliff":** The architecture is good at first-week
   delight but I'm not sure it has enough variety to sustain Month 3
   engagement. The 14 intent types and 4 message categories might
   feel repetitive. The message arc concept (Gap 1) would help
   significantly — each arc is a mini-narrative that breaks the
   "another cute message" fatigue.

5. **Privacy model for multi-recipient:** If the pet sends messages
   to both partners, and one partner replies "I had a terrible fight
   with {partner}," the system now has sensitive information that
   could leak into messages to the other partner. The multi-recipient
   architecture needs information barriers between recipients.

6. **Message fatigue calibration:** The architecture caps at 5 messages/day.
   But optimal frequency varies by person AND by life context. During a
   sick day, 2 gentle messages > 5 normal ones. During a celebration,
   5 might not be enough. RecipientPreference has
   `message_frequency_preference` but it's static. It should be
   dynamic based on LifeContext.

---

## Priority Recommendation for F02 Build

**Build as-is in F02:** The current F02 task list is correct. Don't
expand the scope. These are design observations, not implementation
requirements for Phase 1.

**Add these optional fields during F02:** The future-proofing fields
listed above (arc_id, recipient_id, life_contexts on MessageComposition;
USER_CONTEXT signal source; arc_template on TriggerRule). These are
5-minute additions that save weeks of refactoring later.

**Document these gaps:** Add a "Future Architecture Considerations"
section to message-modeling.md or create a separate doc. The gaps are
valuable design thinking that should be captured, not lost.

**Feed to Gemini after F02:** These customer scenarios are exactly the
kind of strategic input the Gemini review (after F02) should evaluate.
The Gemini brief template already asks "What are we missing?" — this
document provides concrete answers to react to.

---

## Summary: The Emotional Math

The current architecture gets the *words* right. What it doesn't yet
model is the *music* — the rhythm, the pacing, the way messages relate
to each other and to the user's actual life.

A single well-crafted message is a greeting card.
A sequence of messages that weave through your day is a companion.
A companion that notices your life events is family.

The architecture needs to evolve from generating greeting cards to
composing a daily soundtrack. The building blocks are all there.
The composition layer is what's missing.
