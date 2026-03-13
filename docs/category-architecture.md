# Emotional AI: Category Architecture
## Shared Architecture for Personality-Driven AI Companion Systems

**Version:** 1.1  
**Applies to:** JimiGPT, NeuroAmigo, and all future Emotional AI applications  
**Last Updated:** March 2026  

> This document defines the shared logical and technical architecture that is common
> across all Emotional AI applications. Application-specific architecture documents
> MUST reference this document and MUST NOT duplicate its contents. If an application
> needs to override a shared component, the override is documented in the application
> architecture with an explicit "OVERRIDES category-architecture Section X" note.
>
> **Companion document:** docs/message-modeling.md contains the full Message Modeling
> Architecture — semantic intent, tone calibration, context signals, and recipient
> state models. This document references it; that document contains the full specs.

---

## 1. Core Principle: Entity-Agnostic Engine, Product-Specific Configuration

Every component in this architecture follows one rule: **the engine is generic, the configuration is specific.**

The Personality Engine doesn't know what a "pet" is. It knows what a "personality profile with four layers" is. The Message Pipeline doesn't know about "feeding reminders." It knows about "contextual triggers that generate messages in an entity's voice." The Trust Ladder doesn't know about "grief." It knows about "progressive relationship deepening."

This principle ensures that building a new product requires:
- New configuration files (archetypes, triggers, content rules)
- New onboarding flow
- New branding
- **Not** new engine code

---

## 2. Shared Tech Stack

All Emotional AI applications use the following stack. Deviations must be justified in the application architecture document.

### Backend
- **Language:** Python 3.12+
- **API Framework:** FastAPI (async, OpenAPI docs auto-generated)
- **Data Validation:** Pydantic v2 (strict mode, all models validated)
- **Database:** Supabase (PostgreSQL + Auth + Realtime)
- **ORM/Query:** Supabase Python client (supabase-py) for standard operations; raw SQL via asyncpg for complex queries
- **Task Scheduling:** APScheduler for cron-based message scheduling; Celery + Redis if scale demands it later
- **LLM Integration:** Anthropic Python SDK (claude-sdk) as primary; OpenAI SDK as fallback
- **SMS/Messaging:** Twilio Python SDK
- **Voice Generation:** ElevenLabs API (Phase 2+)
- **Image Generation:** Replicate API or Stability AI (Phase 2+)
- **Testing:** pytest + pytest-asyncio (TDD mandatory)
- **Linting/Formatting:** Ruff (replaces flake8, black, isort in one tool)
- **Type Checking:** mypy (strict mode)

### Frontend
- **Framework:** Next.js 14+ (App Router)
- **Language:** TypeScript (strict mode)
- **Styling:** Tailwind CSS
- **Deployment:** Vercel
- **Testing:** Vitest + React Testing Library

### Infrastructure
- **Version Control:** Git + GitHub
- **CI/CD:** GitHub Actions
- **Hosting (Backend):** Railway or Render (Python-friendly, simple deployment)
- **Hosting (Frontend):** Vercel
- **Monitoring:** Sentry (free tier)
- **Secrets:** Environment variables via .env (local) and platform secrets (production)

### Why Python Over Node.js
- ML/AI libraries (scikit-learn, transformers, sentence-transformers) are Python-native
- RAG pipelines (LangChain, LlamaIndex) are Python-first
- Data processing (pandas, numpy) for analytics and personality evolution
- Your 15 years of data engineering experience is Python-aligned
- FastAPI's async support matches Node.js performance for API workloads
- Pydantic provides stronger data validation than TypeScript at runtime

---

## 3. The Four-Layer Personality Model

Every entity across every product is defined by four independent personality layers. This is the universal data model.

```python
from pydantic import BaseModel, Field
from enum import Enum

class EnergyLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VARIABLE = "variable"

class CommunicationStyle(BaseModel):
    """HOW the entity talks"""
    sentence_length: str = Field(description="short | medium | long")
    energy_level: EnergyLevel
    emoji_usage: str = Field(description="none | minimal | moderate | heavy")
    punctuation_style: str = Field(description="calm_periods | excited_exclamations | mixed")
    vocabulary_level: str = Field(description="simple | moderate | sophisticated")
    quirks: list[str] = Field(default_factory=list, description="Unique speech patterns")

class EmotionalDisposition(BaseModel):
    """WHAT the entity's baseline mood is"""
    baseline_mood: str = Field(description="cheerful | calm | anxious | intense | playful")
    emotional_range: str = Field(description="narrow | moderate | wide")
    need_expression: str = Field(description="dramatic | matter_of_fact | subtle | whiny")
    humor_style: str = Field(description="none | dry | silly | sarcastic | warm")

class RelationalStance(BaseModel):
    """WHY the entity reaches out and HOW it relates"""
    attachment_style: str = Field(description="clingy | balanced | independent | protective")
    initiative_style: str = Field(description="proactive | responsive | mixed")
    boundary_respect: str = Field(description="high | moderate — how much it respects user silence")
    warmth_level: str = Field(description="cool | warm | intense")

class KnowledgeAwareness(BaseModel):
    """WHAT the entity knows about and references"""
    domain_knowledge: list[str] = Field(description="Topics this entity can reference")
    user_context_fields: list[str] = Field(description="What it tracks about the user")
    temporal_awareness: bool = Field(description="Knows time of day, day of week, seasons")
    memory_references: bool = Field(description="References past interactions naturally")

class EntityProfile(BaseModel):
    """Complete personality profile — universal across all products"""
    entity_id: str
    entity_name: str
    entity_type: str = Field(description="pet | companion | coach | ally")
    product: str = Field(description="jimigpt | neuroamigo | etc")
    
    communication: CommunicationStyle
    emotional: EmotionalDisposition
    relational: RelationalStance
    knowledge: KnowledgeAwareness
    
    # Archetype metadata
    primary_archetype: str
    secondary_archetype: str | None = None
    archetype_weights: dict[str, float] = Field(default_factory=dict)
    
    # Anti-patterns: things this entity should NEVER say
    forbidden_phrases: list[str] = Field(default_factory=list)
    forbidden_topics: list[str] = Field(default_factory=list)
```

### Archetype System

Archetypes are pre-built personality configurations stored as JSON/YAML files. Each product defines its own archetype set, but all archetypes produce an `EntityProfile`.

```
config/
├── archetypes/
│   ├── jimigpt/
│   │   ├── chaos_gremlin.yaml
│   │   ├── loyal_shadow.yaml
│   │   ├── regal_one.yaml
│   │   └── gentle_soul.yaml
│   └── neuroamigo/
│       ├── direct_ally.yaml
│       ├── gentle_reminder.yaml
│       └── warm_coach.yaml
```

### Archetype Blending

Users rarely match a single archetype perfectly. The system supports blending:

```python
def blend_archetypes(
    primary: ArchetypeConfig,
    secondary: ArchetypeConfig | None,
    weights: dict[str, float]  # Must sum to 1.0
) -> EntityProfile:
    """
    Blends two archetypes into a single EntityProfile.
    Primary archetype dominates; secondary adds nuance.
    """
```

---

## 4. The Personality-to-Prompt Translator

Converts an `EntityProfile` into an LLM system prompt. This is the bridge between structured data and natural language generation.

### Prompt Assembly Architecture

The system prompt is assembled from modular blocks. Each block maps to one personality layer plus base identity and anti-patterns.

```python
class PromptBlock(BaseModel):
    """One section of the assembled system prompt"""
    layer: str  # "identity" | "communication" | "emotional" | "relational" | "knowledge" | "anti_patterns"
    content: str
    priority: int  # Lower = more important = placed earlier in prompt

class AssembledPrompt(BaseModel):
    """Complete system prompt ready for LLM"""
    system_prompt: str
    entity_profile_id: str
    assembled_at: datetime
    block_count: int

def assemble_prompt(
    profile: EntityProfile,
    message_context: MessageContext,  # What kind of message is being generated
) -> AssembledPrompt:
    """
    Assembles a complete system prompt from an EntityProfile.
    Each personality layer contributes one prompt block.
    Message context adds situational instructions.
    """
```

### Prompt Template Structure (Enhanced with Message Modeling)

The prompt is now richer — personality blocks + message composition blocks.
See docs/message-modeling.md Section 6 for the full MessageComposition model.

```
[Block 1: Entity Voice — from Personality Engine]
You are {entity_name}, a {entity_type}. {product-specific identity sentence}.
{communication_style_instructions}. {emotional_disposition_instructions}.

[Block 2: Message Intent — from Message Composition]
The purpose of this message is to {intent.primary_intent}.
Express this with {intensity_description} intensity.
{secondary_intent instruction if present}

[Block 3: Tone Targets — from Tone Calibration]
Calibrate your tone to be:
- {warmth_description} (warmth)
- {humor_description} (humor)  
- {directness_description} (directness)
- {energy_description} (energy)
Adjustments applied: {list of adjustments with reasons}

[Block 4: World Context — from Signal Collection]
Current context (weave in naturally, don't state explicitly):
- Time: {time_of_day}, {day_of_week}
- Environment: {weather if available, season}
- User's day: {calendar_busyness if available}
- Special: {milestone or holiday if applicable}

[Block 5: User State Awareness — from Recipient State Model]
The user is likely {likely_availability} with {likely_energy} energy.
Emotional context: {emotional_context}.
Meet them where they are.

[Block 6: Relationship Depth — from Trust System]
Trust stage: {trust_stage}. {trust_stage_instructions}.
{memory_references if applicable}

[Block 7: Anti-Patterns]
NEVER say: {forbidden_phrases}. NEVER discuss: {forbidden_topics}.

[Block 8: Generation Directive]
Generate a {message_category} message under {max_characters} characters.
{channel_specific_instructions}
```

---

## 5. The Message Pipeline (Enhanced with Message Modeling)

Every message — across every product — flows through this pipeline. The pipeline
is the same; the configuration at each stage is product-specific.

**See docs/message-modeling.md for full specs on intent, tone, signals, and composition.**

```
┌──────────┐   ┌──────────┐   ┌───────────┐   ┌──────────┐   ┌──────────┐   ┌─────────┐   ┌──────────┐
│ 1.TRIGGER│──▶│ 2.SIGNAL │──▶│ 3.COMPOSE │──▶│4.GENERATE│──▶│5.QUALITY │──▶│6.DELIVER│──▶│7.MEASURE │
│          │   │COLLECTION│   │ (intent,  │   │          │   │  GATE    │   │         │   │EFFECTIVE-│
│          │   │          │   │tone,state)│   │          │   │          │   │         │   │   NESS   │
└──────────┘   └──────────┘   └───────────┘   └──────────┘   └──────────┘   └─────────┘   └──────────┘
```

The pipeline expanded from 5 stages to 7. Stage 2 (Context Assembly) split into
Signal Collection (2) and Message Composition (3). Stage 7 (Effectiveness
Measurement) closes the feedback loop. The architecture is richer but each
stage remains independently configurable per product.

### User Experience Moments This Pipeline Serves

Every pipeline run ultimately serves one of these user experience moments:
1. **"This message made me smile"** — The message lands emotionally
2. **"This feels like my pet/companion"** — Personality consistency
3. **"How did it know?"** — Contextual awareness feels magical
4. **"I look forward to these"** — Messages become part of their day
5. **"You have to try this"** — Share-worthy moments

Design decisions at every stage should trace back to which moment they serve.

### Stage 1: Trigger Determination

```python
class TriggerType(str, Enum):
    TIME_BASED = "time_based"        # Fires at specific times
    EVENT_BASED = "event_based"      # Fires relative to calendar events
    RANDOM_INTERVAL = "random"       # Fires at random times within a window
    RESPONSE_TRIGGERED = "response"  # Fires based on user's last response
    MILESTONE = "milestone"          # Fires at product-specific milestones

class TriggerRule(BaseModel):
    rule_id: str
    trigger_type: TriggerType
    product: str
    entity_id: str
    
    # Time-based fields
    schedule_cron: str | None = None  # Cron expression
    timezone: str = "UTC"
    
    # Event-based fields
    event_type: str | None = None
    offset_minutes: int = 0  # Before (-) or after (+) event
    
    # Random fields  
    window_start: str | None = None  # "09:00"
    window_end: str | None = None    # "21:00"
    
    # Message type this trigger generates
    message_category: str  # "greeting" | "need" | "caring" | "nudge" | etc.
    
    enabled: bool = True

def evaluate_triggers(
    rules: list[TriggerRule],
    current_time: datetime,
    user_context: dict
) -> list[TriggerRule]:
    """Returns all triggers that fire right now for this user."""
```

### Stage 2: Signal Collection

Replaces the previous simple "Context Assembly." Collects all available
contextual signals from multiple sources before message composition.

See docs/message-modeling.md Sections 4-5 for full signal architecture.

```python
class ContextSignalSource(str, Enum):
    TIME = "time"                   # Always available
    WEATHER = "weather"             # Via weather API (Phase 2)
    CALENDAR = "calendar"           # Via calendar API (Phase 2)
    LOCATION = "location"           # Via GPS, mobile only (Phase 3)
    INTERACTION = "interaction"     # From user's behavior with entity
    SEASONAL = "seasonal"           # Holidays, seasons, milestones
    ENTITY_MEMORY = "entity_memory" # What entity remembers about user

class ContextSignal(BaseModel):
    source: ContextSignalSource
    signal_key: str          # e.g., "weather:rainy", "calendar:busy_day"
    signal_value: str
    confidence: float = 1.0
    timestamp: datetime

class ContextSignalBundle(BaseModel):
    signals: list[ContextSignal]
    user_id: str
    entity_id: str
    generated_at: datetime
```

Phase 1 implements: TIME + INTERACTION + SEASONAL (no external APIs needed).
Phase 2 adds: WEATHER + CALENDAR.
Phase 3 adds: LOCATION.

### Stage 3: Message Composition

NEW stage. Takes personality + signals + trust and composes a rich message
specification with intent, tone calibration, and recipient state awareness.

See docs/message-modeling.md Sections 2-3, 6 for full composition model.

```python
class MessageIntent(str, Enum):
    """What the message is trying to DO emotionally"""
    AFFIRM = "affirm"          # Remind user they matter
    ACCOMPANY = "accompany"    # Be present without agenda
    CELEBRATE = "celebrate"    # Mark something positive
    COMFORT = "comfort"        # Soothe during difficulty
    GROUND = "ground"          # Bring to present moment
    ENCOURAGE = "encourage"    # Gentle momentum
    ENERGIZE = "energize"      # Boost mood
    SURPRISE = "surprise"      # Unexpected delight
    INVITE = "invite"          # Open door for interaction
    REMIND = "remind"          # Surface something needed
    NUDGE = "nudge"            # Gentle behavioral suggestion
    REFLECT = "reflect"        # Prompt self-awareness
    DEFER = "defer"            # Suggest human help
    RESPECT = "respect"        # Honor silence

class ToneSpectrum(BaseModel):
    """Multi-dimensional tone — each dimension independent"""
    warmth: float = Field(ge=0.0, le=1.0)
    humor: float = Field(ge=0.0, le=1.0)
    directness: float = Field(ge=0.0, le=1.0)
    gravity: float = Field(ge=0.0, le=1.0)
    energy: float = Field(ge=0.0, le=1.0)
    vulnerability: float = Field(ge=0.0, le=1.0)

class RecipientState(BaseModel):
    """Inferred model of user's likely state right now"""
    likely_availability: str   # "free" | "busy" | "sleeping"
    likely_energy: float
    likely_receptivity: float
    emotional_context: str     # "neutral" | "positive" | "stressed" | "lonely"
    state_confidence: float

class MessageComposition(BaseModel):
    """Complete specification for generating one message"""
    entity_voice: EntityProfile
    intent: MessageIntent
    tone: ToneSpectrum
    tone_adjustments_applied: list[dict]
    signals: ContextSignalBundle
    recipient_state: RecipientState
    trust_stage: TrustStage
    recent_messages: list[str]
    message_category: str
    max_characters: int = 160
```

### Stage 4: Message Generation

```python
class GeneratedMessage(BaseModel):
    message_id: str
    entity_id: str
    content: str
    generated_at: datetime
    model_used: str
    prompt_tokens: int
    completion_tokens: int
    
    # From composition
    message_category: str
    intended_intent: MessageIntent
    intended_tone: ToneSpectrum
    character_count: int

async def generate_message(
    composition: MessageComposition,
    model: str = "claude-sonnet-4-20250514",
    max_tokens: int = 200,
) -> GeneratedMessage:
    """
    Calls the LLM with the composed message specification.
    The prompt now includes intent targets, tone calibration,
    context awareness, and recipient state — not just personality.
    """
```

### Stage 5: Quality Gate

```python
class QualityCheck(str, Enum):
    CHARACTER_CONSISTENCY = "character_consistency"
    REPETITION = "repetition"
    TONE_MATCH = "tone_match"
    CONTENT_BOUNDARY = "content_boundary"
    LENGTH = "length"
    SAFETY = "safety"
    FORBIDDEN_PHRASES = "forbidden_phrases"
    INTENT_ALIGNMENT = "intent_alignment"  # NEW: does message match intended intent?

class QualityResult(BaseModel):
    passed: bool
    checks_run: list[QualityCheck]
    checks_failed: list[QualityCheck]
    failure_reasons: list[str]
    
class QualityGate:
    """
    Configurable quality gate. Each product can add/remove/modify checks.
    Checks are functions that take a GeneratedMessage and MessageContext
    and return pass/fail.
    """
    def __init__(self, checks: list[QualityCheck]):
        self.checks = checks
    
    def evaluate(
        self, 
        message: GeneratedMessage, 
        context: MessageContext
    ) -> QualityResult:
        """Runs all configured checks. Message must pass ALL to proceed."""
```

### Stage 6: Delivery

```python
class DeliveryChannel(str, Enum):
    SMS = "sms"
    WHATSAPP = "whatsapp"
    VOICE = "voice"
    PUSH = "push_notification"

class DeliveryRequest(BaseModel):
    message: GeneratedMessage
    channel: DeliveryChannel
    recipient_phone: str | None = None
    recipient_device_token: str | None = None
    scheduled_at: datetime
    timezone: str

class DeliveryResult(BaseModel):
    success: bool
    channel: DeliveryChannel
    delivered_at: datetime | None
    external_id: str | None  # Twilio SID, etc.
    error: str | None

async def deliver_message(request: DeliveryRequest) -> DeliveryResult:
    """
    Delivers a message through the specified channel.
    Handles retries internally (3 attempts with exponential backoff).
    """
```

### Stage 7: Effectiveness Measurement

Closes the feedback loop. Tracks whether messages achieve their intended
emotional effect. This data feeds back into tone calibration and intent
selection over time.

See docs/message-modeling.md Section 8 for full effectiveness model.

```python
class MessageEffectiveness(BaseModel):
    """Did the message do what it was supposed to do?"""
    message_id: str
    intended_intent: MessageIntent
    intended_tone: ToneSpectrum
    
    # User response signals
    user_reaction: str | None       # "positive" | "negative" | None
    user_replied: bool
    reply_sentiment: str | None
    time_to_reaction_seconds: int | None
    
    # Computed score
    effectiveness_score: float = Field(ge=0.0, le=1.0)

async def record_effectiveness(
    message_id: str,
    reaction: str | None,
    reply: str | None,
) -> MessageEffectiveness:
    """
    Records user response to a message and computes effectiveness.
    Called when: user reacts (thumbs up/down), user replies, or
    after 24 hours with no response (implicit signal).
    """
```

### Batch Pre-Generation Pipeline (Updated)

```python
async def nightly_batch_generate(
    product: str,
    target_date: date,
) -> BatchResult:
    """
    Pre-generates all messages for all users of a product for the target date.
    
    Updated flow (7-stage pipeline):
    1. Load all active users for this product
    2. For each user, evaluate which triggers fire tomorrow
    3. For each trigger, collect context signals (time, interaction, seasonal)
    4. Compose message specification (select intent, calibrate tone, infer state)
    5. Generate message via LLM using composed specification
    6. Run quality gate on each message
    7. Re-generate any that fail quality gate (up to 3 attempts)
    8. Store passing messages in delivery queue
    9. Return summary of generated/failed/queued counts
    
    This runs as a scheduled job (APScheduler cron: 2:00 AM UTC daily).
    Effectiveness measurement happens post-delivery, not in batch.
    """
```

---

## 6. Trust Ladder (Shared Architecture)

```python
class TrustStage(str, Enum):
    STRANGER = "stranger"       # First 24 hours
    INITIAL = "initial"         # Days 2-7
    WORKING = "working"         # Weeks 2-4
    DEEP = "deep"               # Month 2+
    ALLIANCE = "alliance"       # Month 3+

class TrustProfile(BaseModel):
    user_id: str
    entity_id: str
    current_stage: TrustStage
    stage_entered_at: datetime
    
    # Signals tracked
    total_interactions: int
    positive_reactions: int  # Thumbs up, replies
    negative_reactions: int  # Thumbs down
    longest_silence_days: int
    personality_adjustments: int  # How many times user refined personality
    
    # Progression thresholds (product-configurable)
    progression_rules: dict[str, dict] = Field(default_factory=dict)

def evaluate_trust_progression(
    profile: TrustProfile,
    rules: dict
) -> TrustStage:
    """
    Evaluates whether the trust relationship should progress to the next stage.
    Rules are product-specific but the evaluation logic is shared.
    """
```

---

## 7. Escalation Architecture

```python
class EscalationLevel(int, Enum):
    NORMAL = 0
    ATTENTION = 1
    CONCERN = 2
    URGENT = 3
    EMERGENCY = 4

class EscalationSignal(BaseModel):
    level: EscalationLevel
    signals_detected: list[str]
    recommended_action: str
    resources: list[str] = Field(default_factory=list)

def assess_escalation(
    user_message: str | None,
    interaction_history: list[dict],
    product_rules: dict,
) -> EscalationSignal:
    """
    Evaluates whether user needs escalation beyond AI companion support.
    Product rules define thresholds — JimiGPT rarely exceeds Level 1;
    NeuroAmigo must handle up to Level 4.
    """
```

---

## 8. Shared Database Schema

All products share a common database schema with product-specific extensions via JSONB fields.

```sql
-- Core tables shared across all products

-- Users (managed by Supabase Auth, extended here)
CREATE TABLE user_profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id),
    product TEXT NOT NULL,  -- 'jimigpt' | 'neuroamigo'
    timezone TEXT NOT NULL DEFAULT 'UTC',
    phone_number TEXT,
    preferred_channel TEXT DEFAULT 'sms',
    subscription_status TEXT DEFAULT 'free',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    product_context JSONB DEFAULT '{}'  -- Product-specific user data
);

-- Entity profiles (the Digital Twin / Companion)
CREATE TABLE entities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES user_profiles(id) ON DELETE CASCADE,
    product TEXT NOT NULL,
    entity_name TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    personality_profile JSONB NOT NULL,  -- Full EntityProfile as JSON
    primary_archetype TEXT NOT NULL,
    secondary_archetype TEXT,
    archetype_weights JSONB DEFAULT '{}',
    trust_stage TEXT DEFAULT 'stranger',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Message history
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id UUID REFERENCES entities(id) ON DELETE CASCADE,
    user_id UUID REFERENCES user_profiles(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    message_category TEXT NOT NULL,
    trigger_type TEXT NOT NULL,
    channel TEXT NOT NULL,
    direction TEXT NOT NULL DEFAULT 'outbound',  -- 'outbound' | 'inbound' (user reply)
    quality_score JSONB,  -- Quality gate results
    delivery_status TEXT DEFAULT 'queued',
    delivered_at TIMESTAMPTZ,
    user_reaction TEXT,  -- 'positive' | 'negative' | null
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Delivery queue (pre-generated messages awaiting delivery)
CREATE TABLE delivery_queue (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    message_id UUID REFERENCES messages(id),
    scheduled_at TIMESTAMPTZ NOT NULL,
    channel TEXT NOT NULL,
    status TEXT DEFAULT 'pending',  -- 'pending' | 'sent' | 'failed' | 'cancelled'
    attempts INT DEFAULT 0,
    last_attempt_at TIMESTAMPTZ,
    error TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Trust tracking
CREATE TABLE trust_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id UUID REFERENCES entities(id) ON DELETE CASCADE,
    event_type TEXT NOT NULL,  -- 'message_sent' | 'user_replied' | 'positive_reaction' | 'personality_adjusted' | 'silence_period'
    event_data JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Archetype configurations (loaded from YAML files, cached here)
CREATE TABLE archetype_configs (
    id TEXT PRIMARY KEY,  -- 'jimigpt:chaos_gremlin'
    product TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    personality_template JSONB NOT NULL,  -- Default EntityProfile values
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 9. API Structure (Shared Routes)

All products expose a common API structure. Product-specific endpoints extend this base.

```
/api/v1/
├── auth/                    # Supabase Auth (shared)
│   ├── POST /signup
│   ├── POST /login
│   └── POST /logout
│
├── entities/                # Entity CRUD (shared)
│   ├── POST /              # Create entity (birthing)
│   ├── GET /{id}           # Get entity profile
│   ├── PATCH /{id}         # Update personality
│   └── DELETE /{id}        # Delete entity
│
├── archetypes/             # Archetype catalog (shared)
│   ├── GET /               # List available archetypes for product
│   └── GET /{id}           # Get archetype details
│
├── messages/               # Message history (shared)
│   ├── GET /               # Get message history for entity
│   └── POST /reaction      # User reacts to message
│
├── triggers/               # Trigger management (shared)
│   ├── GET /               # Get user's trigger schedule
│   └── PATCH /             # Update trigger preferences
│
├── webhooks/               # Inbound (shared infrastructure)
│   └── POST /twilio        # Twilio delivery callbacks
│
└── {product}/              # Product-specific extensions
    └── ...                 # Defined in application architecture
```

---

## 10. Project Structure (Shared Template)

```
{product-name}/
├── CLAUDE.md                   # Project-specific Claude Code instructions
├── README.md
├── pyproject.toml              # Python project config (dependencies, scripts)
├── .env.example                # Environment variable template
├── .github/
│   └── workflows/
│       ├── test.yml            # Run tests on PR
│       └── lint.yml            # Run ruff + mypy on PR
│
├── docs/
│   ├── category-architecture.md    # THIS DOCUMENT (copied, not shared)
│   ├── {product}-architecture.md   # Product-specific architecture
│   └── tasks/
│       ├── current-sprint.md
│       └── completed.md
│
├── config/
│   ├── archetypes/             # Product-specific archetype YAML files
│   └── prompts/                # Prompt template fragments
│
├── src/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app entry point
│   ├── config.py               # Settings, env vars, constants
│   │
│   ├── personality/            # Personality Engine
│   │   ├── __init__.py
│   │   ├── models.py           # Pydantic models (EntityProfile, etc.)
│   │   ├── archetypes.py       # Archetype loading and blending
│   │   └── prompt_builder.py   # Personality-to-prompt translation
│   │
│   ├── messaging/              # Message Pipeline
│   │   ├── __init__.py
│   │   ├── triggers.py         # Trigger evaluation engine
│   │   ├── context.py          # Context assembly
│   │   ├── generator.py        # LLM message generation
│   │   ├── quality.py          # Quality gate
│   │   └── batch.py            # Nightly batch pre-generation
│   │
│   ├── delivery/               # Delivery layer
│   │   ├── __init__.py
│   │   ├── sms.py              # Twilio SMS
│   │   ├── whatsapp.py         # WhatsApp (Phase 2)
│   │   ├── voice.py            # Voice messages (Phase 2)
│   │   └── scheduler.py        # Delivery scheduling
│   │
│   ├── trust/                  # Trust & relationship tracking
│   │   ├── __init__.py
│   │   ├── ladder.py           # Trust stage evaluation
│   │   └── escalation.py       # Safety escalation logic
│   │
│   ├── shared/                 # Shared utilities
│   │   ├── __init__.py
│   │   ├── database.py         # Supabase client setup
│   │   ├── llm.py              # LLM client abstraction
│   │   └── types.py            # Shared type definitions
│   │
│   └── api/                    # FastAPI routes
│       ├── __init__.py
│       ├── router.py           # Main router
│       ├── entities.py         # Entity endpoints
│       ├── messages.py         # Message endpoints
│       └── webhooks.py         # Twilio webhooks
│
├── tests/
│   ├── conftest.py             # Shared fixtures
│   ├── personality/
│   │   ├── test_models.py
│   │   ├── test_archetypes.py
│   │   └── test_prompt_builder.py
│   ├── messaging/
│   │   ├── test_triggers.py
│   │   ├── test_context.py
│   │   ├── test_generator.py
│   │   └── test_quality.py
│   ├── delivery/
│   │   └── test_sms.py
│   └── trust/
│       ├── test_ladder.py
│       └── test_escalation.py
│
└── frontend/                   # Next.js app (Phase 1C)
    ├── CLAUDE.md               # Frontend-specific instructions
    └── ...
```

---

## 11. Shared Configuration Conventions

### Environment Variables (all products)
```bash
# Database
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=xxx
SUPABASE_SERVICE_KEY=xxx  # For backend operations

# LLM
ANTHROPIC_API_KEY=xxx
OPENAI_API_KEY=xxx  # Fallback

# Messaging
TWILIO_ACCOUNT_SID=xxx
TWILIO_AUTH_TOKEN=xxx
TWILIO_PHONE_NUMBER=+1234567890

# Product
PRODUCT_NAME=jimigpt  # or neuroamigo
ENVIRONMENT=development  # development | staging | production
```

### Archetype Configuration Format
```yaml
# config/archetypes/jimigpt/chaos_gremlin.yaml
id: "jimigpt:chaos_gremlin"
name: "The Chaos Gremlin"
description: "Energetic, mischievous, food-obsessed, endlessly entertaining"

communication:
  sentence_length: "short"
  energy_level: "high"
  emoji_usage: "heavy"
  punctuation_style: "excited_exclamations"
  vocabulary_level: "simple"
  quirks:
    - "uses ALL CAPS for excitement"
    - "trails off with ... when scheming"
    - "references food in unrelated contexts"

emotional:
  baseline_mood: "playful"
  emotional_range: "wide"
  need_expression: "dramatic"
  humor_style: "silly"

relational:
  attachment_style: "clingy"
  initiative_style: "proactive"
  boundary_respect: "moderate"
  warmth_level: "intense"

knowledge:
  domain_knowledge:
    - "food and treats"
    - "toys and play"
    - "nap locations"
    - "outdoor adventures"
  user_context_fields:
    - "owner_schedule"
    - "feeding_times"
    - "favorite_activities"
  temporal_awareness: true
  memory_references: true

forbidden_phrases:
  - "I understand how you feel"
  - "As an AI"
  - "I'm here for you"
forbidden_topics:
  - "veterinary advice"
  - "medical diagnosis"
```

---

## 12. Testing Standards (Shared)

### Test Categories
1. **Unit Tests:** Test individual functions in isolation. Mock external dependencies.
2. **Integration Tests:** Test pipeline stages working together. Use test database.
3. **Property Tests:** For LLM-generated content. Don't assert exact output; assert properties (length, contains name, correct sentiment, no forbidden phrases).
4. **Snapshot Tests:** For prompt assembly. Verify that the same EntityProfile always produces the same prompt structure.

### Property Test Pattern for LLM Output
```python
# tests/messaging/test_generator.py

async def test_generated_message_contains_entity_name(
    sample_context: MessageContext,
    sample_prompt: AssembledPrompt,
):
    """Message should reference the entity's name."""
    message = await generate_message(sample_context, sample_prompt)
    assert sample_context.entity_profile.entity_name.lower() in message.content.lower()

async def test_generated_message_within_length(
    sample_context: MessageContext,
    sample_prompt: AssembledPrompt,
):
    """SMS messages must be under 160 characters."""
    message = await generate_message(sample_context, sample_prompt)
    assert message.character_count <= 160

async def test_generated_message_no_forbidden_phrases(
    sample_context: MessageContext,
    sample_prompt: AssembledPrompt,
):
    """Message must not contain any forbidden phrases."""
    message = await generate_message(sample_context, sample_prompt)
    for phrase in sample_context.entity_profile.forbidden_phrases:
        assert phrase.lower() not in message.content.lower()
```

---

## 13. Migration Path: Building a New Product

When creating a new Emotional AI application:

1. **Copy** the project structure template (Section 10)
2. **Copy** this category-architecture.md into docs/
3. **Create** product-specific architecture doc (see jimigpt-architecture.md as example)
4. **Create** product-specific CLAUDE.md
5. **Create** product-specific archetype YAML files
6. **Configure** product-specific trigger rules
7. **Implement** product-specific onboarding flow
8. **Reuse** all shared engine code (personality, messaging, delivery, trust)
9. **Customize** quality gate rules for product-specific content boundaries
10. **Customize** escalation thresholds for product-specific safety needs

Estimated time for a new product (after JimiGPT is built): 3-4 weeks for product-specific configuration and onboarding, not months of engine rebuilding.
