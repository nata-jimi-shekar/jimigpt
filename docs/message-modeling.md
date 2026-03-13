# Message Modeling Architecture
## Semantic Framework for Contextual Emotional Messages

**Version:** 1.0  
**Extends:** Category Architecture Section 5 (Message Pipeline)  
**Applies to:** All Emotional AI products  

> This document elevates message modeling to a first-class architectural concern.
> The Personality Engine defines WHO speaks. This document defines WHAT is said,
> HOW it adapts to reality, and WHY it matters to the recipient.

---

## 1. The Core Reframe: Messages Are the Product

Users never interact with a personality profile. They never see an archetype config.
They see a message on their phone. That message IS the product.

A message is not "personality output." A message is a composed experience with
multiple independent dimensions that must all align for the message to land
emotionally. Personality is one input. Context is another. The user's likely
emotional state is another. The intent of the message is another.

**The composition equation:**

```
Delivered Experience = f(
    Personality Voice,     ← WHO is speaking (from Personality Engine)
    Message Intent,        ← WHY this message exists
    Tone Calibration,      ← HOW it should feel
    Context Signals,       ← WHAT is happening in the user's world
    Recipient State Model, ← WHERE the user likely is emotionally
    Delivery Moment        ← WHEN and through WHAT channel
)
```

Each of these is modeled independently, then composed at generation time.

---

## 2. Message Intent Model

Every message has a primary intent — what it is trying to accomplish emotionally
for the recipient. Intent is NOT the same as message category (those are
product-specific labels like "pet needs" or "pre-date nudge"). Intent is the
universal emotional function.

```python
class MessageIntent(str, Enum):
    """Universal emotional intentions — what the message is trying to DO"""
    
    # Connection intents
    AFFIRM = "affirm"              # Remind user they matter, they're seen
    ACCOMPANY = "accompany"        # Be present without agenda ("I'm here")
    CELEBRATE = "celebrate"        # Mark something positive
    
    # Support intents
    COMFORT = "comfort"            # Soothe during difficult moments
    GROUND = "ground"              # Bring user back to present moment
    ENCOURAGE = "encourage"        # Provide gentle momentum
    
    # Engagement intents
    ENERGIZE = "energize"          # Boost mood, inject playfulness
    SURPRISE = "surprise"          # Unexpected delight, break routine
    INVITE = "invite"              # Open a door for interaction
    
    # Practical intents
    REMIND = "remind"              # Surface something the user needs to do
    NUDGE = "nudge"                # Gentle behavioral suggestion
    REFLECT = "reflect"            # Prompt self-awareness
    
    # Boundary intents
    DEFER = "defer"                # Acknowledge limits, suggest human help
    RESPECT = "respect"            # Honor silence or withdrawal


class IntentProfile(BaseModel):
    """How intents map to a product and context"""
    primary_intent: MessageIntent
    secondary_intent: MessageIntent | None = None
    intensity: float = Field(ge=0.0, le=1.0, description="How strongly to express the intent. 0.3 = subtle, 0.7 = clear, 1.0 = emphatic")
    urgency: float = Field(ge=0.0, le=1.0, description="Time sensitivity. 0.0 = can arrive anytime, 1.0 = must arrive NOW")
```

### Intent Mapping Per Product

Different products weight intents differently:

| Intent | JimiGPT Weight | NeuroAmigo Weight | Sobriety Companion |
|--------|---------------|-------------------|-------------------|
| AFFIRM | Medium | High | Very High |
| ENERGIZE | High | Low-Medium | Medium |
| GROUND | Low | Very High | High |
| NUDGE | Medium | Very High | High |
| COMFORT | Medium | High | Very High |
| SURPRISE | High | Low | Low |
| CELEBRATE | High | Medium | Very High |
| REFLECT | Low | High | High |

JimiGPT skews toward ENERGIZE, SURPRISE, CELEBRATE (playful pet).
NeuroAmigo skews toward GROUND, NUDGE, REFLECT (supportive ally).
Sobriety skews toward AFFIRM, COMFORT, CELEBRATE (steady presence).

---

## 3. Tone Calibration Model

Tone is multi-dimensional. A message can be warm AND humorous. It can be
gentle AND direct. Current architecture treats tone as a single value.
This model decomposes it into independent spectrums.

```python
class ToneSpectrum(BaseModel):
    """Multi-dimensional tone calibration for a single message"""
    
    warmth: float = Field(ge=0.0, le=1.0, description="0.0 = cool/detached, 1.0 = deeply warm")
    humor: float = Field(ge=0.0, le=1.0, description="0.0 = completely serious, 1.0 = highly playful")
    directness: float = Field(ge=0.0, le=1.0, description="0.0 = very indirect/subtle, 1.0 = blunt and clear")
    gravity: float = Field(ge=0.0, le=1.0, description="0.0 = light/casual, 1.0 = deeply serious/weighty")
    energy: float = Field(ge=0.0, le=1.0, description="0.0 = calm/still, 1.0 = highly energetic")
    vulnerability: float = Field(ge=0.0, le=1.0, description="0.0 = guarded, 1.0 = emotionally open")


class ToneRule(BaseModel):
    """Rules for how tone adjusts based on context"""
    signal: str              # What triggers this adjustment
    dimension: str           # Which tone dimension to adjust
    adjustment: float        # How much to shift (-0.5 to +0.5)
    reason: str              # Why this adjustment exists
```

### Tone Defaults Per Archetype (JimiGPT Examples)

| Archetype | Warmth | Humor | Directness | Gravity | Energy | Vulnerability |
|-----------|--------|-------|------------|---------|--------|---------------|
| Chaos Gremlin | 0.8 | 0.9 | 0.7 | 0.1 | 0.95 | 0.3 |
| Loyal Shadow | 0.95 | 0.3 | 0.5 | 0.4 | 0.4 | 0.8 |
| Regal One | 0.4 | 0.6 | 0.8 | 0.5 | 0.3 | 0.1 |
| Anxious Sweetheart | 0.9 | 0.2 | 0.2 | 0.3 | 0.5 | 0.95 |

### Tone Adjustment Rules (Examples)

```yaml
# These rules modify the archetype's default tone based on context signals
tone_rules:
  - signal: "time_of_day:morning"
    dimension: "energy"
    adjustment: +0.1
    reason: "Mornings are naturally higher energy"

  - signal: "time_of_day:night"
    dimension: "energy"
    adjustment: -0.3
    reason: "Nighttime messages should be calmer"
    
  - signal: "time_of_day:night"
    dimension: "gravity"
    adjustment: +0.1
    reason: "Night messages can be slightly more reflective"

  - signal: "weather:rainy"
    dimension: "warmth"
    adjustment: +0.1
    reason: "Rainy days invite cozier tone"

  - signal: "weather:rainy"
    dimension: "energy"
    adjustment: -0.1
    reason: "Rain naturally lowers energy"

  - signal: "user_sentiment:negative"
    dimension: "humor"
    adjustment: -0.3
    reason: "Don't be funny when user is struggling"

  - signal: "user_sentiment:negative"
    dimension: "warmth"
    adjustment: +0.2
    reason: "Increase warmth when user needs support"

  - signal: "trust_stage:stranger"
    dimension: "vulnerability"
    adjustment: -0.3
    reason: "Don't be emotionally open with new users"

  - signal: "trust_stage:deep"
    dimension: "vulnerability"
    adjustment: +0.2
    reason: "Can be more emotionally open with established relationships"

  - signal: "calendar:busy_day"
    dimension: "directness"
    adjustment: +0.2
    reason: "Be more concise on busy days"

  - signal: "calendar:busy_day"
    dimension: "gravity"
    adjustment: -0.1
    reason: "Keep it lighter when user is stressed with work"
```

---

## 4. Context Signal Architecture

The current architecture only uses time as a context signal. Real emotional
relevance requires awareness of the user's actual world. Each signal source
feeds into both message intent selection and tone calibration.

### Signal Sources

```python
class ContextSignalSource(str, Enum):
    """Where context signals come from"""
    TIME = "time"                   # Always available
    WEATHER = "weather"             # Via weather API based on user location
    CALENDAR = "calendar"           # Via calendar integration (Google/Apple)
    LOCATION = "location"           # Via GPS (opt-in, mobile only)
    INTERACTION = "interaction"     # From user's recent behavior with the entity
    SEASONAL = "seasonal"           # Holidays, seasons, special dates
    ENTITY_MEMORY = "entity_memory" # What the entity remembers about the user
    DEVICE = "device"               # Phone activity patterns (future, opt-in)


class ContextSignal(BaseModel):
    """A single contextual signal that influences message composition"""
    source: ContextSignalSource
    signal_key: str          # e.g., "weather:rainy", "calendar:busy_day"
    signal_value: str        # e.g., "heavy_rain", "4_meetings"
    confidence: float = 1.0  # How confident we are in this signal
    timestamp: datetime
    
    
class ContextSignalBundle(BaseModel):
    """All active signals for a message generation moment"""
    signals: list[ContextSignal]
    user_id: str
    entity_id: str
    generated_at: datetime
    
    def get_signal(self, key: str) -> ContextSignal | None:
        """Retrieve a specific signal by key"""
        return next((s for s in self.signals if s.signal_key == key), None)
    
    def has_signal(self, source: ContextSignalSource) -> bool:
        """Check if any signal from a source is present"""
        return any(s.source == source for s in self.signals)
```

### Signal Definitions by Source

**TIME (always available):**
```yaml
time_signals:
  - key: "time_of_day"
    values: ["early_morning", "morning", "midday", "afternoon", "evening", "night", "late_night"]
  - key: "day_of_week"
    values: ["monday", "tuesday", ..., "weekend"]
  - key: "day_type"
    values: ["workday", "weekend", "holiday"]
```

**WEATHER (via API, based on user's stored location):**
```yaml
weather_signals:
  - key: "weather:condition"
    values: ["sunny", "cloudy", "rainy", "stormy", "snowy", "foggy", "hot", "cold"]
  - key: "weather:severity"
    values: ["mild", "moderate", "severe"]
    description: "Severe weather may warrant a caring message"
  - key: "weather:outdoor_suitable"
    values: ["yes", "no"]
    description: "JimiGPT: affects walk-related messages. NeuroAmigo: affects outdoor event prep"
```

**CALENDAR (via Google Calendar / Apple Calendar API, opt-in):**
```yaml
calendar_signals:
  - key: "calendar:busyness"
    values: ["free", "light", "moderate", "packed"]
    description: "Number of events today"
  - key: "calendar:next_event"
    value_type: "object"
    fields: ["event_name", "event_time", "event_type", "hours_until"]
    description: "The next upcoming calendar event"
  - key: "calendar:special_date"
    values: ["pet_birthday", "adoption_anniversary", "owner_birthday", "holiday"]
    description: "Product-specific special dates"
```

**LOCATION (via GPS, opt-in, mobile only):**
```yaml
location_signals:
  - key: "location:place_type"
    values: ["home", "work", "outdoors", "vet", "travel", "unknown"]
    description: "Derived from GPS + known locations"
  - key: "location:transition"
    values: ["leaving_home", "arriving_home", "leaving_work", "arriving_work"]
    description: "Movement events. JimiGPT: 'You're coming home!!!' NeuroAmigo: 'Leaving for the date?'"
  - key: "location:distance_from_home"
    value_type: "float"
    description: "Kilometers from home. Relevant for travel detection"
```

**INTERACTION (from user's behavior with the entity):**
```yaml
interaction_signals:
  - key: "interaction:last_response_sentiment"
    values: ["positive", "neutral", "negative", "none"]
  - key: "interaction:days_since_last_reply"
    value_type: "int"
  - key: "interaction:reply_pattern"
    values: ["frequent", "occasional", "rare", "silent"]
  - key: "interaction:recent_reaction"
    values: ["thumbs_up", "thumbs_down", "none"]
```

**SEASONAL (derived from date + configuration):**
```yaml
seasonal_signals:
  - key: "seasonal:season"
    values: ["spring", "summer", "fall", "winter"]
  - key: "seasonal:holiday"
    value_type: "string"
    description: "Name of holiday if today is one (configurable per locale)"
  - key: "seasonal:entity_anniversary"
    value_type: "int"
    description: "Days since entity creation. Enables milestone messages."
```

### Signal Collection Pipeline

```python
class SignalCollector:
    """
    Collects context signals from all available sources.
    Sources are registered per product. Not all sources are always available.
    Missing sources produce no signals (graceful degradation, not errors).
    """
    
    def __init__(self, sources: list[ContextSignalSource]):
        self.sources = sources
        self.collectors: dict[ContextSignalSource, Callable] = {}
    
    async def collect(
        self, 
        user_id: str, 
        entity_id: str
    ) -> ContextSignalBundle:
        """
        Collects all available signals for this user/entity pair.
        Each source collector runs independently.
        If a source fails, it's skipped (logged, not raised).
        """
    
    def register_collector(
        self, 
        source: ContextSignalSource, 
        collector: Callable
    ) -> None:
        """Register a signal collector for a source."""
```

### Signal Collection by Phase

Not all signals are available from day one. Build incrementally:

| Signal Source | Phase | Complexity | Dependencies |
|--------------|-------|------------|-------------|
| TIME | Phase 1A | Trivial | None — always available |
| INTERACTION | Phase 1B | Low | Message history in database |
| SEASONAL | Phase 1B | Low | Date math + configuration |
| WEATHER | Phase 2 | Medium | Weather API (OpenWeatherMap), user location |
| CALENDAR | Phase 2 | Medium | Google Calendar API (OAuth), user consent |
| LOCATION | Phase 3 | High | Mobile app with GPS permission, geofencing |
| DEVICE | Future | High | Mobile app with activity APIs |

**Phase 1 approach:** Start with TIME + INTERACTION + SEASONAL. These require
no external APIs and no user permissions. They still produce meaningfully
contextual messages. Add richer signals as the product matures.

---

## 5. Recipient State Model

The entity doesn't just need to know about the world — it needs a model of
where the user LIKELY is emotionally right now. This isn't mind-reading.
It's inference from available signals.

```python
class RecipientState(BaseModel):
    """Inferred model of the user's likely emotional/situational state"""
    
    # Inferred from signals
    likely_availability: str = Field(
        description="free | busy | sleeping | commuting | social"
    )
    likely_energy: float = Field(
        ge=0.0, le=1.0,
        description="Inferred energy level. Morning + workday = medium. Friday evening = higher."
    )
    likely_receptivity: float = Field(
        ge=0.0, le=1.0,
        description="How receptive to a message right now. Busy meeting = low. Relaxing at home = high."
    )
    emotional_context: str = Field(
        description="neutral | positive | stressed | lonely | celebratory | grieving"
    )
    
    # Confidence in our inference
    state_confidence: float = Field(
        ge=0.0, le=1.0,
        description="How confident are we in this state model. More signals = higher confidence."
    )

def infer_recipient_state(
    signals: ContextSignalBundle,
    trust_profile: TrustProfile,
    interaction_history: list[dict],
) -> RecipientState:
    """
    Infers the user's likely state from all available signals.
    
    Examples:
    - Monday 9am + calendar:packed → busy, low receptivity, neutral
    - Friday 6pm + no calendar events → free, high receptivity, positive  
    - Rainy Sunday + no recent replies → home, medium energy, potentially lonely
    - Just arrived home (GPS) + workday ending → transitioning, high receptivity
    """
```

---

## 6. Message Composition Model

This is where everything comes together. The Message Composition Model takes
all inputs and produces the instructions for the LLM to generate the actual message.

```python
class MessageComposition(BaseModel):
    """
    The complete specification for generating one message.
    This is what gets translated into the LLM prompt.
    """
    
    # From Personality Engine
    entity_voice: EntityProfile
    
    # From Intent System
    intent: IntentProfile
    
    # From Tone System
    tone: ToneSpectrum
    tone_adjustments_applied: list[ToneRule]
    
    # From Context System
    signals: ContextSignalBundle
    recipient_state: RecipientState
    
    # From Trust System
    trust_stage: TrustStage
    relationship_depth: int  # Number of interactions
    
    # From Message History
    recent_messages: list[str]
    last_user_reply: str | None
    
    # Product-specific
    message_category: str  # Product-level category ("pet_needs", "pre_event_nudge")
    product_context: dict  # Product-specific data
    
    # Generation constraints
    max_characters: int = 160
    channel: DeliveryChannel = DeliveryChannel.SMS


class MessageComposer:
    """
    Composes all inputs into a MessageComposition,
    then translates it into an LLM prompt.
    """
    
    def compose(
        self,
        entity: EntityProfile,
        trigger: TriggerRule,
        signals: ContextSignalBundle,
        trust: TrustProfile,
        message_history: list[str],
    ) -> MessageComposition:
        """
        1. Determine intent from trigger + signals + trust stage
        2. Calculate tone from entity personality + signal-based adjustments
        3. Infer recipient state from signals + history
        4. Package everything into a MessageComposition
        """
    
    def to_prompt(
        self, 
        composition: MessageComposition
    ) -> AssembledPrompt:
        """
        Translates a MessageComposition into the actual LLM prompt.
        
        The prompt now includes not just personality instructions but:
        - Explicit intent: "This message should ENERGIZE the user"
        - Tone targets: "Warmth: 0.8, Humor: 0.9, Energy: 0.6"
        - Context awareness: "It's a rainy Monday morning"
        - Recipient state: "User is likely at work, moderate energy"
        - Constraints: "Under 160 characters, SMS delivery"
        """
```

### Prompt Structure (Updated with Message Model)

```
[Block 1: Entity Voice — from Personality Engine]
You are {name}, a {type}. {personality description}.

[Block 2: Message Intent — NEW]
The purpose of this message is to {intent.primary_intent}.
Express this with {intent.intensity} intensity.
{secondary_intent instruction if present}

[Block 3: Tone Targets — NEW]
Calibrate your tone:
- Warmth: {tone.warmth}/1.0 ({warmth_description})
- Humor: {tone.humor}/1.0 ({humor_description})
- Directness: {tone.directness}/1.0 ({directness_description})
- Energy: {tone.energy}/1.0 ({energy_description})
These tone targets have been adjusted for current context:
{list of applied tone_adjustments with reasons}

[Block 4: World Context — NEW, much richer than before]
Current context the message should be aware of:
- Time: {time_of_day}, {day_of_week}
- Weather: {weather_condition} (reference naturally if relevant, don't force it)
- Calendar: {calendar_context} (user has {busyness_level} day)
- Location: {location if available}
- Special: {holiday or milestone if applicable}
DO NOT mention these contexts explicitly. Weave them in naturally.
A pet doesn't say "Based on the weather..." — it says "Perfect nap weather..."

[Block 5: User State Awareness — NEW]
The user is likely: {recipient_state.likely_availability}
Their energy level is probably: {recipient_state.likely_energy}
Emotional context: {recipient_state.emotional_context}
Adjust your message to meet them where they are, not where you are.

[Block 6: Relationship Depth — from Trust System]
Trust stage: {trust_stage}. {trust_stage_instructions}
You have had {relationship_depth} interactions.
{memory references if applicable}

[Block 7: Anti-Patterns]
NEVER: {forbidden_phrases}. {forbidden_topics}.
{product_specific_anti_patterns}

[Block 8: Generation Directive]
Generate a {message_category} message under {max_characters} characters.
{channel-specific instructions}
```

---

## 7. Entity Semantic Relationships

Entities don't exist in isolation. In JimiGPT, a user might have two pets.
In NeuroAmigo, the companion knows about recurring people in the user's life.
This section models how entities relate to each other and to the user's world.

```python
class EntityRelationship(BaseModel):
    """A semantic relationship between an entity and another entity or concept"""
    entity_id: str
    related_to: str             # Another entity_id or a concept identifier
    relationship_type: str      # "sibling" | "companion" | "knows_about" | "recurring_person"
    relationship_context: str   # Natural language description
    can_reference: bool = True  # Whether this entity can mention the related entity

class EntityWorldModel(BaseModel):
    """What the entity knows about the user's world beyond the user themselves"""
    
    entity_id: str
    
    # Other entities this entity is aware of
    relationships: list[EntityRelationship] = Field(default_factory=list)
    
    # Recurring elements in the user's life this entity can reference
    known_places: list[str] = Field(default_factory=list)    # "the office", "the park", "grandma's house"
    known_people: list[str] = Field(default_factory=list)    # "your roommate", "your mom" (no real names stored)
    known_routines: list[str] = Field(default_factory=list)  # "morning run", "Wednesday meetings"
    known_preferences: list[str] = Field(default_factory=list) # "you hate Mondays", "you love rainy days"
    
    # Learned over time from interactions
    discovered_at: dict[str, datetime] = Field(default_factory=dict)
```

### JimiGPT Entity Relationships

```yaml
# Example: User has two pets - Luna (cat) and Max (dog)
entities:
  luna:
    relationships:
      - related_to: "max"
        relationship_type: "sibling"
        relationship_context: "Luna tolerates Max. Mostly."
        can_reference: true
    known_places: ["the sunny windowsill", "the kitchen counter"]
    known_routines: ["3am zoomies", "judging you from across the room"]
    
  max:
    relationships:
      - related_to: "luna"
        relationship_type: "sibling"
        relationship_context: "Max loves Luna. Luna does not reciprocate."
        can_reference: true
    known_places: ["the park", "the couch", "wherever you are"]
    known_routines: ["morning walk", "evening treat negotiation"]

# This enables messages like:
# Luna: "Max is being loud again. I'm going to the windowsill. Don't follow me."
# Max: "Luna won't play with me AGAIN. Can we go to the park instead??"
```

### NeuroAmigo Entity Relationships

```yaml
# Example: User's companion knows about recurring social contexts
entities:
  companion:
    known_people:
      - "the person you've been dating"  # Never uses real names
      - "your work friend who invites you to things"
    known_places:
      - "that bar where it always gets loud"
      - "your quiet coffee spot"
    known_routines:
      - "Thursday evening dates"
      - "weekend social events you say yes to then dread"
    known_preferences:
      - "you do better one-on-one than groups"
      - "you overshare when you're tired, not just when drinking"

# This enables messages like:
# "Thursday again. Date night. Remember: you don't have to fill every silence."
# "You mentioned that bar gets loud. That's when your masking goes up. Be gentle with yourself."
```

---

## 8. Message Effectiveness Tracking

The message model isn't complete without knowing if messages actually land.
This closes the feedback loop.

```python
class MessageEffectiveness(BaseModel):
    """Tracks how well a message performed its intended function"""
    message_id: str
    
    # What was intended
    intended_intent: MessageIntent
    intended_tone: ToneSpectrum
    
    # What happened
    user_reaction: str | None          # "positive" | "negative" | None
    user_replied: bool
    reply_sentiment: str | None        # "positive" | "neutral" | "negative"
    time_to_reaction_seconds: int | None
    
    # Derived effectiveness score
    effectiveness_score: float = Field(
        ge=0.0, le=1.0,
        description="Computed from reaction + reply + sentiment"
    )

class IntentEffectivenessReport(BaseModel):
    """Aggregate: how well does this entity perform each intent?"""
    entity_id: str
    period_days: int
    
    intent_scores: dict[MessageIntent, float]
    # e.g., {ENERGIZE: 0.8, COMFORT: 0.6, NUDGE: 0.4}
    # Low scores suggest the personality or tone calibration
    # needs adjustment for that intent type
    
    tone_effectiveness: dict[str, float]
    # e.g., {"high_humor": 0.9, "high_gravity": 0.3}
    # This entity's humor lands, but serious messages don't
    
    signal_correlations: dict[str, float]
    # e.g., {"weather:rainy + COMFORT": 0.85, "calendar:busy + ENERGIZE": 0.2}
    # Comfort messages on rainy days work great; 
    # energizing messages on busy days don't land
```

This data feeds back into the personality refinement system. If the
Chaos Gremlin's COMFORT messages consistently score low, the system
learns: this personality voice isn't suited for comfort. Either adjust
the tone calibration for comfort messages, or shift comfort messages to
a gentler sub-voice.

---

## 9. Implementation Priority

This message modeling architecture is rich. Don't build it all at once.
Implement in layers that match your phase plan.

### Phase 1A-1B (Build Now)
- MessageIntent enum and IntentProfile model
- ToneSpectrum model with per-archetype defaults
- Tone adjustment rules (time-based only — the signals you already have)
- Updated prompt structure with intent and tone blocks
- Basic RecipientState inference from time + interaction history

### Phase 2 (After MVP)
- Weather signal collector (OpenWeatherMap API)
- Calendar signal collector (Google Calendar OAuth)
- Full ContextSignalBundle with multiple sources
- EntityWorldModel (known places, routines, preferences)
- Entity relationships (multi-pet support)
- Message effectiveness tracking

### Phase 3 (After Traction)
- Location signal collector (mobile GPS)
- Device activity signals
- Intent effectiveness optimization (auto-adjust tone per intent)
- Cross-entity messaging (pets referencing each other)
- Full feedback loop: effectiveness → personality refinement → better messages

---

## 10. How This Changes the Pipeline

The Five-Stage Pipeline from the Category Architecture is preserved,
but Stage 2 (Context Assembly) and Stage 3 (Generation) become richer:

```
BEFORE:
  Trigger → Context(personality + time) → Generate(simple prompt) → Quality → Deliver

AFTER:
  Trigger → Signal Collection → Intent Selection → Tone Calibration 
  → Recipient State Inference → Message Composition → Generate(rich prompt) 
  → Quality Gate → Effectiveness Tracking → Deliver
```

The pipeline gains three new sub-stages within what was previously just
"Context Assembly":
1. Signal Collection (gather all available context)
2. Intent Selection (determine WHY this message exists)
3. Tone Calibration (adjust HOW the message should feel)

And one new sub-stage after delivery:
4. Effectiveness Tracking (did the message work?)
```
