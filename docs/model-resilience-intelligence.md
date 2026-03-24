# Model Resilience & Intelligence Strategy
## From API Wrapper to Proprietary Intelligence

**Version:** 1.0
**Created:** March 2026
**Status:** Phase 1 = LLM abstraction layer. Phase 2+ = intelligence accumulation.

> Two existential risks: (1) complete dependency on a single LLM provider,
> and (2) no proprietary intelligence — we're a prompt wrapper. This document
> addresses both with a concrete, phased plan that doesn't delay MVP but
> builds the foundation for independence.

---

## THE CURRENT STATE (Honest Assessment)

### What's Hard-Coded

```python
# generator.py — direct Anthropic dependency
DEFAULT_MODEL = "claude-sonnet-4-6"
_client = client if client is not None else anthropic.AsyncAnthropic()
response = await _client.messages.create(
    model=model,
    max_tokens=max_tokens,
    system=prompt.system_prompt,
    messages=[{"role": "user", "content": _GENERATE_TRIGGER}],
)
content: str = response.content[0].text
```

This means:
- If Anthropic's API is down → zero messages for all users
- If model is deprecated → generator breaks completely
- If model quality shifts → personality drift, undetected
- If pricing changes → no alternative without code rewrite
- If a competitor offers better emotional tone → can't switch without refactoring
- No ability to A/B test across providers
- No ability to use local models for any workload

### What We're Not Learning

The effectiveness tracking (effectiveness.py) records scores but nothing
reads them back. The data flows into a dead end:

```
Generate message → Deliver → User reacts → Score recorded → [NOTHING]
                                                              ↑
                                                    No feedback loop
                                                    No model training
                                                    No pattern learning
                                                    No cost optimization
```

We know WHAT works but we don't USE that knowledge to get better.

---

## PART 1: LLM ABSTRACTION LAYER

### The Principle

The generator should not know or care which LLM provider it's using.
It should call a unified interface, and the interface handles provider
selection, fallback, and quality verification.

### The Architecture

```
MessageComposer.to_prompt()
        │
        ↓
LLMRouter (NEW)
  ├── Provider selection (based on message type, cost, availability)
  ├── Fallback chain (primary → secondary → cached → graceful degradation)
  ├── Response normalization (all providers return same format)
  ├── Quality verification (does output match expected personality?)
  └── Telemetry (cost, latency, quality per provider per model)
        │
        ↓ Routes to one of:
  ├── AnthropicProvider (Claude Haiku, Sonnet, Opus)
  ├── OpenAIProvider (GPT-4o-mini, GPT-4o)
  ├── LocalProvider (Mistral, Llama via Ollama — Phase 2+)
  └── CachedProvider (pre-generated fallback messages)
        │
        ↓
GeneratedMessage (same output regardless of provider)
```

### The Model

```python
class LLMProvider(str, Enum):
    """Supported LLM providers."""
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    LOCAL = "local"        # Phase 2: Ollama/vLLM
    CACHED = "cached"      # Fallback: pre-generated messages

class ModelConfig(BaseModel):
    """Configuration for one model endpoint."""
    provider: LLMProvider
    model_id: str          # "claude-haiku-4-5" | "gpt-4o-mini" | "mistral-7b"
    cost_per_1k_input: float
    cost_per_1k_output: float
    max_tokens: int
    supports_system_prompt: bool = True
    prompt_format: str = "standard"  # "standard" | "chatml" | "llama"
    quality_tier: str = "standard"   # "economy" | "standard" | "premium"

class RoutingDecision(BaseModel):
    """Why a specific model was chosen for this message."""
    selected_model: ModelConfig
    reason: str            # "primary" | "fallback_primary_down" | "cost_optimization" | "quality_test"
    fallback_chain: list[str]  # Models that were tried before this one
    routing_rule: str      # Which rule selected this model

class LLMResponse(BaseModel):
    """Normalized response from any provider."""
    content: str
    provider: LLMProvider
    model_id: str
    input_tokens: int
    output_tokens: int
    cost_usd: float        # Computed from ModelConfig rates
    latency_ms: int
    routing_decision: RoutingDecision
```

### Routing Rules

```yaml
# config/llm_routing.yaml

# Default routing — cost-optimized for standard messages
default:
  primary: "anthropic:claude-haiku-4-5"
  fallback:
    - "openai:gpt-4o-mini"
    - "cached:personality_matched"
  max_cost_per_message_usd: 0.001

# High-stakes messages get better models
high_stakes:
  triggers:
    - trust_stage: "deep"
    - intent: "comfort"
    - intent: "defer"
    - life_context: "user_grieving"
    - life_context: "user_sick"
  primary: "anthropic:claude-sonnet-4-6"
  fallback:
    - "anthropic:claude-haiku-4-5"
    - "openai:gpt-4o-mini"
    - "cached:personality_matched"
  max_cost_per_message_usd: 0.005

# First message (birthing ceremony) — premium quality
first_impression:
  triggers:
    - trust_stage: "stranger"
    - message_category: "first_message"
  primary: "anthropic:claude-sonnet-4-6"
  fallback:
    - "anthropic:claude-haiku-4-5"

# Quality testing — random sample through alternative model
quality_test:
  sample_rate: 0.05  # 5% of messages
  model: "openai:gpt-4o-mini"
  compare_with: "primary"
  log_comparison: true
```

### The Fallback Chain

```
1. Try PRIMARY model
   ↓ If fails (timeout, error, quality gate fails)
2. Try SECONDARY model
   ↓ If fails
3. Try ECONOMY model (cheapest available)
   ↓ If fails
4. Use CACHED fallback (pre-generated personality-matched messages)
   ↓ If no suitable cache
5. SKIP this message, reschedule for next window
   (Never send a bad message. Silence > wrong message.)
```

### The Cached Fallback — Last Resort

Pre-generate a pool of 50 messages per archetype per message category.
These are generic enough to work in most contexts but personality-
specific enough to not feel robotic. Stored locally. Zero API dependency.

```python
class CachedMessagePool(BaseModel):
    """Pre-generated fallback messages per archetype × category."""
    archetype_id: str
    message_category: str
    messages: list[str]          # 50 pre-generated messages
    last_refreshed: datetime
    model_used: str              # Which model generated these

    def select(self, recent_messages: list[str]) -> str:
        """Select a message that hasn't been used recently."""
```

Generated during batch runs when API is healthy. Refreshed weekly.
Each message passes the quality gate before entering the pool.

### Prompt Adaptation Layer

Different providers have different prompt formats:

```python
class PromptAdapter:
    """Converts the 8-block system prompt to provider-specific format."""

    def adapt(
        self,
        composed_prompt: ComposedPrompt,
        target_provider: LLMProvider,
    ) -> dict:
        """Returns provider-specific API payload."""
        match target_provider:
            case LLMProvider.ANTHROPIC:
                return {
                    "system": composed_prompt.system_prompt,
                    "messages": [{"role": "user", "content": TRIGGER}],
                }
            case LLMProvider.OPENAI:
                return {
                    "messages": [
                        {"role": "system", "content": composed_prompt.system_prompt},
                        {"role": "user", "content": TRIGGER},
                    ]
                }
            case LLMProvider.LOCAL:
                # Ollama/vLLM format
                return self._adapt_for_local(composed_prompt)
```

### Phase 1 Implementation (Do This NOW — Before F03)

**This is a refactor of generator.py. One bounded container (3 reps).**

- Rep 1: Create `src/shared/llm.py` with LLMProvider enum, ModelConfig,
  LLMResponse. Create AnthropicProvider and a MockProvider for testing.
  Abstract the `anthropic.AsyncAnthropic()` call behind a provider interface.

- Rep 2: Update `generator.py` to use the provider abstraction instead
  of direct Anthropic calls. The function signature stays the same.
  Tests pass unchanged (they already inject a mock client).

- Rep 3: Add OpenAI provider stub (not implemented, raises NotConfigured).
  Add CachedProvider stub. Add routing config loading from YAML.

**This adds ~1 hour to the schedule but removes the single-point-of-failure risk.**

### Phase 2 Implementation

- Add OpenAI provider implementation (GPT-4o-mini for fallback)
- Add routing rules engine (YAML config → routing decision)
- Add cached message pool generation (batch job)
- Add quality comparison logging (5% sample through alternative model)
- Add cost telemetry (track spend per provider per archetype)

---

## PART 2: MODEL QUALITY MONITORING

### The Personality Drift Problem

When a model updates, your pet might sound different. The quality gate
catches safety issues and length violations, but it can't detect "this
Chaos Gremlin sounds 10% less chaotic than last week."

### The Solution: Personality Fingerprinting

Generate a "personality fingerprint" for each archetype using a fixed
set of test prompts. Run these periodically (daily or on model change)
and compare fingerprints.

```python
class PersonalityFingerprint(BaseModel):
    """Measurable personality signature for drift detection."""
    archetype_id: str
    model_id: str
    generated_at: datetime

    # Measurable features extracted from test message set
    avg_message_length: float
    exclamation_rate: float       # Exclamations per message
    emoji_rate: float             # Emoji per message
    caps_word_rate: float         # ALL-CAPS words per message
    question_rate: float          # Questions per message
    avg_sentence_length: float
    vocabulary_diversity: float   # Unique words / total words

    # Tone proxy scores (computed from linguistic features)
    energy_proxy: float           # Derived from caps, exclamations, emoji
    warmth_proxy: float           # Derived from specific warm word presence
    humor_proxy: float            # Derived from specific humor markers

class DriftDetection(BaseModel):
    """Comparison between two fingerprints."""
    archetype_id: str
    model_a: str
    model_b: str
    drift_score: float            # 0.0 = identical, 1.0 = completely different
    dimensions_drifted: list[str] # Which features changed significantly
    alert_level: str              # "none" | "notice" | "warning" | "critical"
```

### Fingerprint Test Suite

```yaml
# config/fingerprint_tests.yaml
# Fixed prompts that produce comparable outputs across models/versions

tests:
  - name: "morning_greeting_high_energy"
    archetype: "chaos_gremlin"
    trigger: "morning_greeting"
    signals: {time_of_day: "morning", day_type: "weekday"}
    expected_tone: {energy: 0.9, humor: 0.8}

  - name: "comfort_message_low_energy"
    archetype: "loyal_shadow"
    trigger: "caring_checkin"
    signals: {last_sentiment: "negative", days_since_reply: 3}
    expected_tone: {warmth: 0.9, energy: 0.3}

  - name: "personality_moment_regal"
    archetype: "regal_one"
    trigger: "personality_moment"
    signals: {time_of_day: "afternoon"}
    expected_tone: {directness: 0.8, gravity: 0.5}

  # 10 more covering all archetypes and key scenarios
```

Run this suite:
- After every model version change (detect via API version headers)
- Weekly as a scheduled job
- Before promoting a new model to production
- When comparing two models (A/B quality testing)

### Alert Thresholds

| Drift Score | Alert Level | Action |
|------------|-------------|--------|
| 0.0 – 0.1 | None | Normal variation |
| 0.1 – 0.2 | Notice | Log it, monitor next run |
| 0.2 – 0.4 | Warning | Review sample messages, consider pinning model version |
| 0.4+ | Critical | Pin model version immediately, investigate, regenerate cache |

---

## PART 3: INTELLIGENCE ACCUMULATION STRATEGY

### The Vision

Move from "send prompt → get text" to "send prompt informed by learned
patterns → get text → learn from effectiveness → improve next prompt."

```
Phase 1 (NOW): Prompt-only. Zero learning. API wrapper.
     ↓
Phase 2: Effectiveness analytics. Know what works. Still prompt-only
         but prompts are informed by data.
     ↓
Phase 3: Classification models. Local models classify signals, sentiment,
         context. Frontier models only for generation.
     ↓
Phase 4: Fine-tuned generation. Local model fine-tuned on your best
         messages generates standard messages. Frontier model reserved
         for high-stakes and creative moments.
     ↓
Phase 5: Ambient Presence Intelligence. Your own model understands
         personality, tone, context, and recipient preference natively.
         Frontier models become optional enhancement, not dependency.
```

### Phase 2: Effectiveness Analytics Engine

**What it does:** Consumes the effectiveness data that currently flows
into a dead end. Produces actionable intelligence.

```python
class EffectivenessAnalytics:
    """Consumes effectiveness data, produces intelligence."""

    def intent_report(self, entity_id: str, period_days: int) -> IntentReport:
        """Which intents work best for this entity?

        Returns:
            {ENERGIZE: 0.82, COMFORT: 0.45, SURPRISE: 0.91, ...}

        Usage: Feed into intent selection weights. If COMFORT scores
        low for this entity, reduce its selection probability and
        increase ACCOMPANY (which may serve the same emotional need
        with this personality's voice).
        """

    def tone_report(self, entity_id: str, period_days: int) -> ToneReport:
        """Which tone calibrations produce highest effectiveness?

        Returns:
            best_performing: ToneSpectrum(warmth=0.85, humor=0.7, ...)
            worst_performing: ToneSpectrum(warmth=0.4, humor=0.9, ...)

        Usage: Nudge tone defaults toward best_performing over time.
        This is personality REFINEMENT, not personality CHANGE.
        """

    def timing_report(self, entity_id: str, period_days: int) -> TimingReport:
        """When do messages land best?

        Returns:
            best_times: ["08:15", "12:30", "18:45"]
            worst_times: ["10:00", "15:00"]
            best_day_types: ["weekend"]

        Usage: Adjust trigger schedules toward best-performing windows.
        """

    def archetype_report(self, period_days: int) -> ArchetypeReport:
        """Cross-entity: which archetypes produce best engagement?

        Returns:
            {chaos_gremlin: 0.78, loyal_shadow: 0.71, regal_one: 0.65, ...}

        Usage: Content platform curation. Feature high-performing archetypes.
        B2B sales data. Product roadmap prioritization.
        """
```

**Implementation:** This is a batch analytics job that runs nightly.
Reads from the effectiveness table, aggregates, writes reports to a
new `intelligence` table. The intent selector and tone calibrator
read these reports to inform their decisions.

**This is where effectiveness data stops being a dead end and starts
being a feedback loop.**

### Phase 3: Local Classification Models

**The insight:** You don't need a frontier model for everything. Most
of the pipeline's intelligence work is CLASSIFICATION, not GENERATION:

| Task | Type | Can Run Locally? |
|------|------|-----------------|
| Intent selection | Classification | YES — rule-based today, model-based later |
| Tone calibration | Calculation | YES — pure math today |
| Recipient state inference | Classification | YES — rules today, model later |
| Context signal extraction | Classification | YES — time/date is code, sentiment is a small model |
| User reply sentiment | Classification | YES — small model (distilbert-base) |
| User reply context tags | Classification | YES — small model or rules |
| Quality gate checks | Classification + rules | YES — all local today |
| Life context detection | Classification | YES — keyword matching → small model |
| Message GENERATION | Generation | FRONTIER MODEL — this is the creative work |

**Only message generation requires a frontier model.** Everything else
can run on local classification models or rules. This means:

- 90% of the pipeline's "intelligence" can be local
- Only the final generation step calls an API
- API costs drop to just the generation call
- Latency drops for all classification steps
- No API dependency for signal processing

**Specific local models for Phase 3:**

```yaml
local_models:
  sentiment_classifier:
    model: "distilbert-base-uncased-finetuned-sst-2-english"
    task: "Classify user reply sentiment (positive/negative/neutral)"
    size: "~260MB"
    latency: "<50ms"
    replaces: "Currently hardcoded rules in recipient state inference"

  context_tagger:
    model: "distilbert-base-uncased" # Fine-tuned on our tag taxonomy
    task: "Extract context tags from user replies (park, sick, celebration)"
    size: "~260MB"
    latency: "<50ms"
    replaces: "Phase 2 USER_CONTEXT signal extraction"

  intent_classifier:
    model: "Custom trained on effectiveness data"
    task: "Given signals + trust + archetype, predict best intent"
    size: "~100MB"
    training_data: "Effectiveness records: (signals, intent, score) tuples"
    replaces: "Rule-based intent selection in intent.py"
    note: "Train when you have 5,000+ effectiveness records"

  tone_predictor:
    model: "Small regression model (scikit-learn or small neural net)"
    task: "Given signals + archetype + recipient preference, predict optimal tone"
    size: "<50MB"
    training_data: "Effectiveness records: (tone_spectrum, score) tuples"
    replaces: "Rule-based tone calibration — becomes learned calibration"
    note: "Train when you have 10,000+ effectiveness records"
```

### Phase 4: Fine-Tuned Generation

**When you have 50,000+ messages with effectiveness scores**, you have
a dataset that no one else has: (personality + intent + tone + context
→ message + effectiveness_score). This dataset can fine-tune a local
generation model.

```
Training data structure:
  Input: 8-block system prompt + trigger
  Output: message text
  Score: effectiveness_score (used as reward signal)

Filter: only train on messages scoring 0.5+ (above median)
Result: a local model that generates personality-consistent messages
        without calling any API
```

**Model options for local generation:**

| Model | Size | Quality | Cost |
|-------|------|---------|------|
| Mistral 7B (fine-tuned) | 14GB | Good for standard messages | Free after hardware |
| Llama 3 8B (fine-tuned) | 16GB | Good personality consistency | Free after hardware |
| Phi-3 Mini (fine-tuned) | 7GB | Acceptable for simple messages | Free, runs on CPU |

**The hybrid approach:**
- Local fine-tuned model handles 80% of messages (standard, predictable)
- Frontier model handles 20% (high-stakes, creative, first impressions)
- Cost drops by ~80% while quality is maintained where it matters

### Phase 5: Ambient Presence Intelligence

This is the long-term vision. Your system develops its own understanding
of personality, emotional tone, and contextual appropriateness.

```
What the system learns over time:

1. PERSONALITY PATTERNS
   "Chaos Gremlins with low vulnerability perform better with ENERGIZE
   at mealtimes but SURPRISE works better midday"

2. RECIPIENT MODELS
   "Users who pick Loyal Shadow and reply frequently respond best to
   warmth=0.9 messages but disengage when vulnerability > 0.6"

3. TEMPORAL PATTERNS
   "Rainy Monday mornings need 15% less energy than rainy Saturday mornings"

4. ARC PATTERNS
   "Feeding arcs with 4 messages outperform 3-message arcs.
   Weather arcs work best with 2-hour spacing, not 1-hour."

5. CROSS-ENTITY PATTERNS
   "In multi-pet households, the second pet's morning message gets
   30% lower engagement if sent within 60 minutes of the first"

6. CONTENT PATTERNS
   "Messages under 80 characters outperform 120-160 character messages
   for ENERGIZE intent but not for COMFORT intent"
```

None of this intelligence exists in any frontier model. It's YOUR data
from YOUR users in YOUR product context. This is the moat.

---

## PART 4: DATA COLLECTION STRATEGY (START NOW)

Even in Phase 1, you can start collecting the data that powers Phase 3-5.
The collection infrastructure costs almost nothing to add.

### What to Collect Starting Now

```python
class MessageGenerationLog(BaseModel):
    """Full telemetry for every message generated. Written to DB."""

    # Input
    composition_snapshot: dict     # Full MessageComposition as JSON
    prompt_text: str               # The actual system prompt sent to LLM
    prompt_tokens: int

    # Output
    generated_content: str
    completion_tokens: int
    model_used: str
    provider: str
    generation_latency_ms: int
    cost_usd: float

    # Quality
    quality_gate_result: dict      # Full QualityResult as JSON
    quality_gate_passed: bool
    regeneration_count: int        # How many attempts before passing

    # Effectiveness (filled later)
    effectiveness_score: float | None = None  # Filled when user reacts
    user_reaction: str | None = None
    user_replied: bool | None = None
    reply_sentiment: str | None = None

    # Metadata
    generated_at: datetime
    entity_id: str
    archetype_id: str
    recipient_id: str | None = None
```

**This is ONE table.** Every row is a complete training example for
future intelligence: input context → output message → human score.
At 500 messages/day (100 users), you accumulate 15,000 rows/month.
In 6 months, 90,000 training examples. That's enough to train
meaningful local models.

### Database Table (Add to F05 Migration)

```sql
CREATE TABLE message_generation_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id UUID REFERENCES entities(id),
    archetype_id TEXT NOT NULL,
    recipient_id UUID,

    -- Input
    composition_json JSONB NOT NULL,
    prompt_text TEXT NOT NULL,
    prompt_tokens INT NOT NULL,

    -- Output
    generated_content TEXT NOT NULL,
    completion_tokens INT NOT NULL,
    model_used TEXT NOT NULL,
    provider TEXT NOT NULL,
    generation_latency_ms INT,
    cost_usd NUMERIC(10, 6),

    -- Quality
    quality_passed BOOLEAN NOT NULL,
    quality_result_json JSONB,
    regeneration_count INT DEFAULT 0,

    -- Effectiveness (updated later via trigger or batch)
    effectiveness_score NUMERIC(3, 2),
    user_reaction TEXT,
    user_replied BOOLEAN,
    reply_sentiment TEXT,

    -- Meta
    generated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for analytics queries
CREATE INDEX idx_gen_log_archetype ON message_generation_log(archetype_id);
CREATE INDEX idx_gen_log_model ON message_generation_log(model_used);
CREATE INDEX idx_gen_log_effectiveness ON message_generation_log(effectiveness_score)
    WHERE effectiveness_score IS NOT NULL;
```

### Phase 1 Action: Add Logging to Generator

After the LLM abstraction layer is in place, add a `log_generation()`
call at the end of `generate_message()`. This writes the full
MessageGenerationLog to the database. Zero impact on message delivery.
Pure data collection.

**This is the single most important thing you can do for long-term
independence.** Every message you generate from Day 1 without logging
is a training example you'll never get back.

---

## PART 5: COST OPTIMIZATION PATH

### Current Cost Model (Phase 1)

| Model | Input Cost/1M | Output Cost/1M | Per Message (~800 in / 100 out) | 100 Users (500 msg/day) | 5000 Users (25K msg/day) |
|-------|-------------|---------------|-------------------------------|----------------------|------------------------|
| Haiku 4.5 | $0.80 | $4.00 | $0.001 | $0.50/day | $25/day |
| Sonnet 4.6 | $3.00 | $15.00 | $0.004 | $2.00/day | $100/day |

### Optimized Cost Model (Phase 3 — Local + Frontier Hybrid)

| Workload | % of Messages | Model | Cost Per Message |
|----------|--------------|-------|-----------------|
| Standard messages | 70% | Local fine-tuned (free) | $0.00 |
| Context-rich messages | 15% | Haiku | $0.001 |
| High-stakes messages | 10% | Sonnet | $0.004 |
| First impressions | 5% | Sonnet | $0.004 |

**Blended cost per message: ~$0.00035** (vs. $0.001 all-Haiku)
**At 5,000 users: ~$4.40/day** (vs. $25/day all-Haiku)

### Cost Savings Reinvestment

The savings from local model usage should be reinvested into:
1. Higher-quality generation for high-stakes messages (use Sonnet instead of Haiku)
2. More frequent quality testing (A/B across providers)
3. Faster personality fingerprinting runs
4. More message arc experiments

---

## PART 6: SPOT TESTING — MULTI-MODEL QUALITY COMPARISON

### The Concept

Route 5% of messages through an alternative model alongside the
primary model. Generate both. Compare. Log the comparison. Over time,
this produces empirical data on which model produces better emotional
payloads for which scenarios.

```python
class ModelComparison(BaseModel):
    """Side-by-side comparison of two models on the same prompt."""

    comparison_id: str
    composition_id: str  # Same composition for both

    model_a: str
    model_a_output: str
    model_a_latency_ms: int
    model_a_cost: float

    model_b: str
    model_b_output: str
    model_b_latency_ms: int
    model_b_cost: float

    # Quality gate results for both
    model_a_quality_passed: bool
    model_b_quality_passed: bool

    # Personality fingerprint comparison
    personality_match_a: float  # How well does A match the archetype fingerprint?
    personality_match_b: float

    # Human evaluation (filled manually during parallel testing)
    human_preferred: str | None = None  # "a" | "b" | "equal"
    human_notes: str | None = None
```

### How It Works

```yaml
# config/llm_routing.yaml
quality_test:
  sample_rate: 0.05          # 5% of all messages
  comparison_model: "openai:gpt-4o-mini"  # Compare against
  log_both_outputs: true
  deliver_primary_only: true  # User always gets the primary model output
  human_review_queue: true    # Flag for manual review during parallel testing
```

During parallel testing sessions, you review the comparison queue:
"For this COMFORT message to a Loyal Shadow, Haiku produced X and
GPT-4o-mini produced Y. Which feels more authentic?"

Over 100 comparisons, you get empirical data:
"Haiku is better for high-energy archetypes. GPT-4o-mini is better
for COMFORT intent. Neither is consistently better for tone fidelity."

This data informs routing rules. It's also data no one else has.

---

## IMPLEMENTATION TIMELINE

### Immediate (Before F03 — One Container)

**LLM Abstraction Layer — the critical refactor.**

| Rep | What | Time |
|-----|------|------|
| 1 | Create `src/shared/llm.py`: LLMProvider enum, ModelConfig, LLMResponse, BaseProvider interface, AnthropicProvider implementation | 20 min |
| 2 | Refactor `generator.py` to use provider abstraction. All existing tests must pass unchanged. | 20 min |
| 3 | Add OpenAI provider stub (NotConfigured), CachedProvider stub, routing config YAML skeleton | 20 min |

**Commit:** `refactor(shared): add LLM provider abstraction layer`

This removes the hard Anthropic dependency at the code level.
Actual multi-provider support follows in Phase 2.

### During F05 (Database)

Add `message_generation_log` table to the migration script.
Add `log_generation()` call to generator. Start collecting data from Day 1.

### Phase 2 (Post-MVP)

- OpenAI provider implementation
- Routing rules engine
- Cached message pool generation
- 5% quality comparison logging
- Personality fingerprinting suite
- Effectiveness analytics engine

### Phase 3 (Post-Traction, ~6 months of data)

- Local sentiment classifier deployment
- Intent classifier training (from effectiveness data)
- Tone predictor training (from effectiveness data)
- Hybrid routing (local classification + frontier generation)

### Phase 4 (Post-Scale, ~12 months of data)

- Fine-tuned local generation model
- 70% local / 30% frontier split
- Full Ambient Presence Intelligence

---

## WHAT THIS MEANS FOR THE MOAT

```
Today (Phase 1):
  Moat = Architecture design + Archetype quality
  Replicable by: Anyone with prompt engineering skills
  Moat depth: SHALLOW

Post-Phase 2 (6 months):
  Moat += Effectiveness data + Routing intelligence + Quality comparisons
  Replicable by: Someone who also has 100+ users generating daily data
  Moat depth: MODERATE

Post-Phase 3 (12 months):
  Moat += Trained classification models + Personality fingerprints + Learned patterns
  Replicable by: Someone who ALSO has 50,000+ scored messages AND classification models
  Moat depth: SIGNIFICANT

Post-Phase 4 (18 months):
  Moat += Fine-tuned generation model + 80% cost reduction + Proprietary voice
  Replicable by: Practically no one — the model IS the product
  Moat depth: DEEP
```

The path from wrapper to platform is: collect data → analyze data →
learn from data → embody the learning in models → become independent
of the data source. You're building an intelligence flywheel, not
just a message pipeline.
```
