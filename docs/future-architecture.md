# Future Architecture: Foundation Concepts
## Designs for Phase 2+ Features — Foundation Laid in Phase 1

**Version:** 1.0
**Created:** March 2026
**Status:** Design only. Implementation phased per schedule below.

> These concepts were identified during a customer-lens architecture review.
> They represent the gap between "messages as independent units" and
> "messages as a living companion experience." Phase 1 builds the foundation
> fields and interfaces. Phase 2+ builds the full features.

---

## 1. Message Arcs (Emotional Sequences)

### The Problem
The current pipeline generates one message per trigger. Real emotional
experiences are arcs — a feeding anticipation sequence, a rainy day thread,
a sick day care pattern. A single message is a notification. A sequence
is a companion.

### The Model

```python
class MessageArc(BaseModel):
    """A coordinated sequence of messages around a theme or event."""

    arc_id: str
    arc_type: str  # "feeding_anticipation" | "weather_day" | "sick_day" | etc.
    entity_id: str
    recipient_id: str

    # What initiated this arc
    trigger_context: str  # Signal or event that started the arc

    # The sequence
    messages: list[ArcMessage]

    # Arc-level properties
    arc_tone: ToneSpectrum  # Overall emotional register
    can_interrupt: bool = True  # Can other triggers interrupt?
    max_duration_hours: int = 12
    adapt_on_response: bool = True  # Modify remaining messages if user responds

    # State
    status: str = "active"  # "active" | "completed" | "interrupted" | "cancelled"
    started_at: datetime
    completed_at: datetime | None = None


class ArcMessage(BaseModel):
    """One message within an arc sequence."""

    position: int  # 1, 2, 3... within the arc
    offset_minutes: int  # Minutes after arc starts
    intent: MessageIntent
    tone_modifier: dict[str, float] = Field(default_factory=dict)
    # e.g., {"energy": -0.2} to reduce energy for later messages in arc
    condition: str | None = None
    # e.g., "no_response_to_previous" | "user_replied_positive" | None (always send)
    generated_message_id: str | None = None  # Filled when generated
```

### Arc Templates (Product-Specific Config)

```yaml
# config/arcs/jimigpt/feeding_anticipation.yaml
arc_type: "feeding_anticipation"
description: "Building excitement before feeding time"
trigger_signal: "time:feeding_time"
trigger_offset_minutes: -30  # Start 30 min before feeding
messages:
  - position: 1
    offset_minutes: 0
    intent: "accompany"
    tone_modifier: {energy: -0.1, humor: +0.1}
    # "I can tell it's almost time..."
  - position: 2
    offset_minutes: 25
    intent: "remind"
    tone_modifier: {energy: +0.2, directness: +0.2}
    # "Five minutes. I'm counting."
  - position: 3
    offset_minutes: 30
    intent: "energize"
    tone_modifier: {energy: +0.3}
    # "IT'S TIME!"
  - position: 4
    offset_minutes: 45
    intent: "nudge"
    condition: "no_response_to_previous"
    tone_modifier: {vulnerability: +0.2}
    # "Hello?? Did you forget?"
max_duration_hours: 2
can_interrupt: true

# config/arcs/jimigpt/weather_day.yaml
arc_type: "weather_day"
description: "Weaving weather awareness through the day"
trigger_signal: "weather:rainy"
messages:
  - position: 1
    offset_minutes: 0
    intent: "accompany"
    tone_modifier: {warmth: +0.1, energy: -0.2}
  - position: 2
    offset_minutes: 120
    intent: "surprise"
    tone_modifier: {humor: +0.1}
  - position: 3
    offset_minutes: 300
    intent: "accompany"
    tone_modifier: {warmth: +0.2}
```

### How Arcs Use the Existing Pipeline

Each message in an arc flows through the FULL 7-stage pipeline individually.
The arc orchestrates *when* and *what intent/tone*, but the pipeline handles
personality voice, signal collection, generation, quality gate, and delivery
as usual. The arc is a conductor, not a replacement for the orchestra.

```
Arc Orchestrator
  ↓ (selects next arc message, sets intent + tone modifier)
  ↓
Stage 1: Trigger (arc provides the trigger)
Stage 2: Signal Collection (normal — collects current signals)
Stage 3: Composition (normal — but intent/tone influenced by arc)
Stage 4: Generate (normal — LLM generates with composed prompt)
Stage 5: Quality Gate (normal + arc coherence check)
Stage 6: Deliver (normal)
Stage 7: Effectiveness (normal — feedback can modify remaining arc)
```

### Phase 1 Foundation (Built in F02)
- `arc_id: str | None` and `arc_position: int | None` fields on
  MessageComposition — always None in Phase 1
- Quality gate concept: consecutive message emotional coherence
- TriggerRule accepts `arc_template: str | None` — always None in Phase 1

### Phase 2 Implementation
- ArcMessage and MessageArc models
- Arc template YAML loading
- Arc orchestrator (sits above pipeline)
- Arc state management (track active arcs per user)
- Arc adaptation on user response

---

## 2. Multi-Recipient Architecture

### The Problem
One entity → one user. But real households have multiple people who
would benefit from the same pet's voice with different relationships,
tones, and schedules.

### The Model

```python
class EntityRecipient(BaseModel):
    """A relationship between an entity and one recipient."""

    entity_id: str
    recipient_id: str  # References user_profile
    relationship_type: str
    # "primary_owner" | "partner" | "child" | "family_member" | "caretaker"
    recipient_role: str
    # "companion" | "playful_nag" | "mediator" | "monitor" | "reminder"

    # Per-recipient calibration
    recipient_preference: RecipientPreference
    trust_stage: TrustStage
    trigger_schedule: list[TriggerRule]
    message_categories_enabled: list[str]
    tone_overrides: dict[str, float] = Field(default_factory=dict)
    # e.g., {"humor": +0.2} for a child recipient

    # Content boundaries per recipient
    content_age_appropriate: bool = False  # Extra filtering for children
    information_barrier: bool = True
    # If True, context from this recipient's replies is NOT shared
    # with other recipients of the same entity

    enabled: bool = True


class RecipientSummary(BaseModel):
    """Summary report sent to a monitoring recipient (e.g., adult child)."""

    entity_id: str
    primary_recipient_id: str
    monitor_recipient_id: str
    period: str  # "daily" | "weekly"
    messages_sent: int
    messages_responded_to: int
    sentiment_trend: str
    notable_moments: list[str]
```

### Use Cases Enabled

| Scenario | Primary Recipient | Additional Recipients |
|----------|------------------|----------------------|
| Single mom + 2 teens | Mom (companion) | Kid 1 (playful_nag), Kid 2 (playful_nag) |
| Couple with pet | Partner A (companion) | Partner B (companion, different schedule) |
| Elderly parent | Parent (companion) | Adult child (monitor — weekly summary) |
| Indirect mediation | Partner A (mediator) | Partner B (mediator) |
| Latchkey kid | Parent (companion) | Child (companion, age-appropriate) |

### Database Impact

```sql
-- New table (Phase 2)
CREATE TABLE entity_recipients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id UUID REFERENCES entities(id) ON DELETE CASCADE,
    recipient_id UUID REFERENCES user_profiles(id) ON DELETE CASCADE,
    relationship_type TEXT NOT NULL,
    recipient_role TEXT NOT NULL DEFAULT 'companion',
    trigger_schedule JSONB DEFAULT '[]',
    message_categories JSONB DEFAULT '[]',
    tone_overrides JSONB DEFAULT '{}',
    content_age_appropriate BOOLEAN DEFAULT FALSE,
    information_barrier BOOLEAN DEFAULT TRUE,
    enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(entity_id, recipient_id)
);
```

### Privacy: Information Barriers

Critical constraint: When Entity X sends messages to both Recipient A
and Recipient B, and Recipient A replies with sensitive information
(e.g., about a fight with Recipient B), that information MUST NOT leak
into messages sent to Recipient B.

Each recipient's reply context lives in their own signal collection.
Cross-recipient signals are blocked by default (`information_barrier: true`).
Only the entity's general personality and shared factual context (pet's
schedule, milestones) travel across recipients.

### Phase 1 Foundation (Built in F02)
- `recipient_id: str | None` field on MessageComposition — in Phase 1,
  populated from the entity's single owner; ready for multi-recipient
- MessageComposer.compose() takes explicit recipient_id parameter
- No hardcoded assumptions of one entity = one recipient in pipeline logic

### Phase 2 Implementation
- EntityRecipient model and database table
- Per-recipient trigger scheduling
- Per-recipient trust tracking
- Per-recipient tone overrides
- Information barriers in signal collection
- RecipientSummary for monitoring recipients

---

## 3. Life Event Awareness

### The Problem
Each trigger evaluation is stateless. The pipeline doesn't know "we're
in sick-day mode" or "the pet is at the vet today." Life events change
the entire messaging strategy for a period — frequency, energy, intent
distribution — not just one message's tone.

### The Model

```python
class LifeContextType(str, Enum):
    """Categories of life events that modify messaging strategy."""

    # User states
    USER_SICK = "user_sick"
    USER_TRAVELING = "user_traveling"
    USER_CELEBRATING = "user_celebrating"
    USER_GRIEVING = "user_grieving"
    USER_STRESSED = "user_stressed"

    # Pet states
    PET_VET = "pet_vet"
    PET_BOARDING = "pet_boarding"
    PET_SICK = "pet_sick"
    PET_NEW_IN_HOUSEHOLD = "pet_new_in_household"

    # Relationship states
    NEW_JOB = "new_job"
    BREAKUP = "breakup"
    NEW_RELATIONSHIP = "new_relationship"

    # Custom
    CUSTOM = "custom"


class LifeContext(BaseModel):
    """A time-bounded life event that modifies messaging strategy."""

    context_id: str
    user_id: str
    context_type: LifeContextType
    started_at: datetime
    expected_end: datetime | None = None  # None = indefinite until user deactivates
    source: str  # "user_reported" | "inferred" | "calendar"
    active: bool = True

    # Strategy overrides
    frequency_modifier: float = 1.0  # 0.5 = half as many messages, 1.5 = more
    energy_cap: float | None = None  # Max energy for any message during this context
    preferred_intents: list[str] = Field(default_factory=list)
    blocked_intents: list[str] = Field(default_factory=list)
    arc_template: str | None = None  # Auto-activate an arc for this context

    # Tone adjustments applied ON TOP of normal calibration
    tone_adjustments: dict[str, float] = Field(default_factory=dict)
    # e.g., {"warmth": +0.2, "energy": -0.3, "gravity": +0.1}
```

### Predefined Life Context Templates

```yaml
# config/life_contexts/user_sick.yaml
context_type: "user_sick"
frequency_modifier: 0.6
energy_cap: 0.4
preferred_intents: ["comfort", "accompany", "affirm"]
blocked_intents: ["energize", "remind", "nudge"]
tone_adjustments:
  warmth: +0.2
  energy: -0.3
  humor: -0.2
  gravity: +0.1
arc_template: "sick_day_care"

# config/life_contexts/pet_boarding.yaml
context_type: "pet_boarding"
frequency_modifier: 0.8
preferred_intents: ["accompany", "surprise", "affirm"]
tone_adjustments:
  warmth: +0.1
  vulnerability: +0.2
arc_template: "boarding_diary"

# config/life_contexts/user_celebrating.yaml
context_type: "user_celebrating"
frequency_modifier: 1.3
preferred_intents: ["celebrate", "energize", "surprise"]
blocked_intents: ["comfort", "ground"]
tone_adjustments:
  energy: +0.2
  humor: +0.1
```

### How Users Activate Life Contexts

Phase 2 options (simplest first):
1. **Reply keywords:** User replies "I'm sick" → system classifies and
   activates context. Reply "feeling better" → deactivates.
2. **In-app toggles:** Simple UI with common life events as toggles.
3. **Calendar inference:** Google Calendar shows "Vet appointment" →
   system activates pet_vet context automatically.

### Phase 1 Foundation (Built in F02)
- `life_contexts: list[str]` field on MessageComposition — always empty
  list in Phase 1
- LifeContextType enum defined (used as reference, not implemented)
- Intent selection interface accepts life_contexts parameter (ignores
  it in Phase 1 logic)
- Tone calibration interface accepts life_contexts parameter (ignores
  it in Phase 1 logic)

### Phase 2 Implementation
- LifeContext model and database table
- Life context templates (YAML config)
- Reply classification for context activation
- In-app toggle UI
- Pipeline integration: load active life contexts during signal collection
- Calendar-based automatic activation

---

## 4. User-Initiated Context Signals

### The Problem
Users want to TELL the pet things — "We're going to the park!" or "Bad
day at work." These aren't conversations. They're context injections that
should change the next few messages.

### The Model

Extends the existing ContextSignalSource with a new source:

```python
# Added to ContextSignalSource enum
USER_CONTEXT = "user_context"
```

When a user replies to a message, the signal collector:
1. Records sentiment (already planned in INTERACTION)
2. Extracts context tags (NEW): keywords or categories
3. Creates short-lived ContextSignals from the tags
4. These signals influence the next 1-3 messages, then decay

```python
class UserContextExtraction(BaseModel):
    """Extracted context from a user's reply."""

    reply_text: str
    sentiment: str  # "positive" | "neutral" | "negative"
    context_tags: list[str]  # ["park", "outdoor", "excited"]
    inferred_life_event: LifeContextType | None = None
    decay_messages: int = 3  # How many messages this context influences
    extracted_at: datetime
```

### Phase 1 Foundation (Built in F02)
- USER_CONTEXT in ContextSignalSource enum
- INTERACTION signal collector captures `last_reply_context_tags: list[str]`
  (empty list in Phase 1 — extraction logic comes Phase 2)

### Phase 2 Implementation
- Reply text classification (LLM-based or rule-based)
- Context tag extraction
- Short-lived signal creation with decay
- Life event inference from replies

---

## 5. Multi-Pet Coordination

### The Problem
A household with two pets should feel like a household, not two
independent chatbots. Messages need to be spaced, and pets should
occasionally reference each other.

### The Model

The trigger evaluation orchestrator needs awareness of other entities
belonging to the same user:

```python
class EntityScheduleContext(BaseModel):
    """Schedule awareness for multi-entity coordination."""

    entity_id: str
    entity_name: str
    scheduled_messages: list[datetime]  # Already-scheduled delivery times
    last_message_at: datetime | None
```

Coordination rules:
- Minimum 90 minutes between messages from different entities
- Cross-reference probability: 20% chance an entity mentions a sibling
- Personality voices remain distinct — coordination is timing, not blending

### Phase 1 Foundation (Built in F02)
- Trigger orchestrator accepts `sibling_entity_schedules: list[dict]`
  parameter (empty list in Phase 1 for single-pet users)
- No hardcoded single-entity assumptions in scheduling logic

### Phase 2 Implementation
- Load sibling entities during trigger evaluation
- Scheduling coordination algorithm
- Cross-reference content in prompt builder (EntityWorldModel from
  message-modeling.md Section 7)

---

## 6. Professional/B2B Message Channel

### The Problem
Vets, pet stores, and pet services could communicate through the pet's
voice — appointment reminders, medication reminders, care tips. This is
a revenue channel and distribution strategy.

### The Model

```python
class MessageSource(BaseModel):
    """Who is initiating/paying for a message."""

    source_type: str  # "organic" | "professional" | "scheduled_external"
    source_id: str | None = None  # Business account ID
    source_context: dict = Field(default_factory=dict)
    # e.g., {"appointment_date": "2026-04-15", "vet_name": "Dr. Chen"}
    content_boundary: str = "general"
    # What the source CAN communicate — defined by business type
    owner_approved: bool = True
    # Pet owner must opt-in to professional messages
```

### Critical Constraint
The pet's voice is the owner's emotional relationship. Businesses are
guests in that space. The owner ALWAYS has veto power. No professional
message sends without explicit opt-in. The owner can disable any
professional source at any time.

### Phase 1 Foundation
- None. This is entirely Phase 3.
- The only thing to preserve is: no assumptions in the pipeline that
  messages are always "organic." The GeneratedMessage model should not
  hardcode source_type.

### Phase 3 Implementation
- MessageSource model
- Professional account system
- Owner opt-in/opt-out flow
- Professional message templates
- Billing (B2B subscription or per-message)

---

## Phase Integration Schedule

| Concept | Foundation (Phase 1) | MVP Feature (Phase 2) | Full Feature (Phase 3) |
|---------|---------------------|----------------------|----------------------|
| Message Arcs | Optional fields on models | Arc orchestrator, templates, state | Adaptive arcs, user-created arcs |
| Multi-Recipient | recipient_id parameter | EntityRecipient, per-recipient config | Mediation, summaries, age filtering |
| Life Events | Empty fields, enum defined | User-reported contexts, templates | Calendar inference, auto-detection |
| User Context | Signal source enum value | Reply classification, tag extraction | Full context injection with decay |
| Multi-Pet | Orchestrator parameter | Scheduling coordination | Cross-reference content |
| B2B Channel | No hardcoded source_type | — | Full professional system |
