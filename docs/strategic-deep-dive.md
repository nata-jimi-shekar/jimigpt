# Emotional AI: Strategic Deep Dive
## From Message Pipeline to Content Platform — The Logical Path

**Version:** 1.0
**Created:** March 2026
**Purpose:** Deep analysis of two strategic opportunities — B2B Pet Services Channel
and Digital Twin Content Platform (Reality Show) — with focus on the logical
objects, development foundations, market gradations, and measurable milestones
that connect today's F02 build to tomorrow's entertainment platform.

**Print this. Take notes. Revisit monthly.**

---

# PART I: THE LOGICAL OBJECT MAP

Everything that makes the B2B channel and reality show possible is built from
a finite set of logical objects. These objects are the atoms. Every feature,
every product extension, every revenue stream is a molecule assembled from
these atoms. If you understand the atoms, you understand what's possible.

---

## 1. The Seven Core Objects

These are the foundational entities in the Emotional AI system. Each one
exists independently but creates compound value when combined.

### Object 1: EntityProfile (The Character)

**What it is:** A complete personality definition — four layers of communication
style, emotional disposition, relational stance, and knowledge awareness, plus
archetype blend weights and anti-patterns.

**Why it matters for the Reality Show:**
The EntityProfile IS the character bible for every "actor" in the show. In
traditional TV, writers create character bibles over weeks. In this system,
the EntityProfile is created during the birthing ceremony and refined through
use. Every message the entity sends is an in-character performance. The
consistency of this performance is what makes audiences follow specific
Digital Twins.

**Quality bar for content readiness:**
- Voice distinctiveness score: If you read 5 messages without archetype labels,
  can you identify which archetype sent each one? Target: 80%+ correct
- Personality persistence: Does the entity sound the same on Day 1 and Day 30?
  Target: Same archetype identification accuracy after 30 days
- Cross-archetype contrast: Do Chaos Gremlin and Regal One feel like different
  characters, or variations of the same voice? Target: Any two archetypes
  distinguishable in blind testing

**What you're building now that creates this:**
F01 (complete) — the personality models, archetype YAML configs, blending
logic, and prompt builder. Every line of F01 code is a line in the
character creation system.

```
EntityProfile
  ├── Character voice (communication style, quirks)
  ├── Emotional register (baseline mood, humor style)
  ├── Relationship posture (attachment, initiative)
  ├── Knowledge domain (what they can reference)
  ├── Archetype blend (primary + secondary weights)
  └── Boundaries (forbidden phrases, topics)
        │
        ↓ Used by
  Message Pipeline (F02) — generates in-character dialogue
  Content Platform (future) — the dialogue becomes the script
  Reality Show (future) — the character performs on a stage
```

---

### Object 2: MessageComposition (The Scene Direction)

**What it is:** The complete specification for one message — entity voice +
intent + calibrated tone + context signals + recipient state + trust stage.
This is the "director's notes" for each line of dialogue.

**Why it matters for the Reality Show:**
A message without composition data is just text. A message WITH composition
data is a scene: you know the emotional intent (COMFORT vs. ENERGIZE), the
tone targets (warmth 0.85, humor 0.3), the context (rainy Monday, user
seems stressed), and the trust depth (deep relationship, can reference
shared history). This metadata is what turns a chat log into a narrative
with knowable emotional beats.

When the content platform presents an "episode," it doesn't just show the
messages — it understands the emotional structure. It knows that message #3
was meant to comfort, message #5 was a surprise, and message #7 was the
emotional resolution. The composition data IS the screenplay markup.

**Quality bar for content readiness:**
- Intent accuracy: Does the generated message actually accomplish its intended
  emotional purpose? If the intent is COMFORT, does the message comfort?
  Target: 85%+ intent-message alignment in parallel testing
- Tone fidelity: Does the message hit its tone targets? A message targeted
  at warmth=0.9 should feel warmer than one at warmth=0.4.
  Target: Blind testers can rank messages by warmth/humor/energy correctly
- Context integration: Does the message weave in context naturally?
  "Perfect nap weather" on a rainy day, not "Based on current weather data..."
  Target: Zero explicit context mentions; 80%+ natural integration

**What you're building now that creates this:**
F02 (starting tomorrow) — Tasks 5-10 build the entire composition system.
This is the most important feature for content readiness because it
determines whether messages are just personality-voiced text or emotionally
directed scenes.

```
MessageComposition
  ├── Entity voice ← from EntityProfile
  ├── Intent ← selected from trigger + signals + trust
  │     └── 14 intent types = 14 emotional purposes = 14 scene types
  ├── Tone calibration ← archetype defaults + signal adjustments
  │     └── 6 dimensions = the emotional "color grading" of each scene
  ├── Context signals ← time, interaction, seasonal (Phase 1)
  │     └── The "setting" of each scene
  ├── Recipient state ← inferred from signals
  │     └── What the "audience" (user) is likely feeling
  ├── Trust stage ← progressive relationship depth
  │     └── How intimate the scene can be
  ├── [Foundation] arc_id ← which narrative arc this belongs to
  ├── [Foundation] recipient_id ← who this scene is for
  └── [Foundation] life_contexts ← what life event frames this scene
```

---

### Object 3: MessageArc (The Episode)

**What it is:** A coordinated sequence of messages around a theme or event,
with timing, emotional progression, and adaptation to user response.

**Why it matters for the Reality Show:**
Individual messages are tweets. Arcs are stories. The feeding anticipation
arc (4 messages over 45 minutes building from anticipation to frenzy to
satisfaction) IS a complete mini-episode with setup, escalation, climax,
and resolution. A rainy day arc spanning the afternoon IS a mood piece.
A sick day arc IS a character study in empathy.

Without arcs, the "show" is a collection of one-liners. With arcs, it's
serialized narrative content with emotional structure that audiences return
for. "Did Max get his dinner?" is a cliffhanger. "Is Luna still judging
everyone from the windowsill?" is a running gag. These are the building
blocks of serialized entertainment.

**Quality bar for content readiness:**
- Arc completeness: Does every arc have a discernible beginning, middle, end?
  Target: 90%+ of arcs resolve (don't trail off or get interrupted randomly)
- Emotional progression: Does the emotional register shift meaningfully across
  the arc? (Anticipation → excitement → satisfaction is a progression.
  Three messages at the same energy level is not.)
  Target: At least 2 distinct emotional shifts per arc
- User response adaptation: When the user replies mid-arc, does the remaining
  arc adapt? (User says "feeding you now" → remaining escalation messages
  don't fire. User says "running late" → pet's response acknowledges the delay.)
  Target: 100% adaptation on direct arc-relevant replies

**What this depends on:**
F02 foundation fields (arc_id, arc_position on MessageComposition). The actual
arc orchestrator is Phase 2 development. But the quality of F02's individual
message generation directly determines the quality of each scene within
future arcs.

```
MessageArc
  ├── Arc type ← "feeding_anticipation", "weather_day", "sick_day"
  ├── Trigger context ← what started this arc
  ├── Message sequence
  │     ├── Message 1: position, offset, intent, tone_modifier
  │     ├── Message 2: position, offset, intent, tone_modifier, [condition]
  │     ├── Message 3: position, offset, intent, tone_modifier, [condition]
  │     └── ... (2-6 messages per arc)
  ├── Arc-level tone ← overall emotional register
  ├── Adaptation rules ← how arc changes on user response
  ├── State ← active | completed | interrupted
  └── Duration ← hours this arc spans
        │
        ↓ Each message flows through
  Full 7-stage pipeline (F02) — personality, composition, generation, quality
        │
        ↓ The sequence becomes
  Episode content — beginning, middle, end, emotional beats
```

---

### Object 4: LifeContext (The Plot Line)

**What it is:** A time-bounded life event that modifies the entire messaging
strategy — frequency, energy, intent distribution, tone adjustments.

**Why it matters for the Reality Show:**
Life contexts are the PLOTS. "User is sick" isn't a single message — it's a
multi-day story arc where the pet's behavior changes. The Chaos Gremlin gets
quieter. The Loyal Shadow gets more attentive. The Regal One drops its
facade briefly. These behavioral shifts across archetypes are character
development happening in real-time.

For the audience, life contexts create the dramatic stakes. "Max's human is
traveling for a week" is a setup. The pet's messages across that week —
missing their human, making friends at boarding, counting down to homecoming —
that's a complete narrative season. And critically, because it's real (the
user actually is traveling), the emotional beats are authentic in a way
that scripted content can never replicate.

**Quality bar for content readiness:**
- Strategy shift visibility: When a life context activates, can an outside
  observer notice the change in messaging? (Fewer messages, different tone,
  different intents.) Target: Blind testers can identify "something changed"
  in 80%+ of life context activations
- Personality preservation: During a life context, does the entity still
  sound like itself? A sick-day Chaos Gremlin should be quieter but still
  fundamentally chaotic. Target: Archetype identification accuracy stays
  above 70% even during life contexts
- Arc integration: Does the life context automatically trigger appropriate
  arcs? (user_sick → sick_day_care arc. pet_boarding → boarding_diary arc.)
  Target: 100% of predefined life contexts have associated arc templates

```
LifeContext
  ├── Context type ← "user_sick", "pet_boarding", "user_traveling"
  ├── Duration ← bounded time period
  ├── Source ← user-reported, inferred, calendar
  ├── Strategy overrides
  │     ├── Frequency modifier (0.6 = fewer messages)
  │     ├── Energy cap (0.4 = calmer overall)
  │     ├── Preferred intents (comfort, accompany, affirm)
  │     ├── Blocked intents (energize, remind)
  │     └── Tone adjustments (+warmth, -energy, -humor)
  ├── Arc template ← auto-activated arc
  └── Active flag
        │
        ↓ Creates
  Multi-day narrative arc — the "plot" of this period
        │
        ↓ Which becomes
  Season-level content — "Max's human was sick for 3 days. Here's the story."
```

---

### Object 5: EntityRecipient (The Relationship Web)

**What it is:** The many-to-many relationship between an entity and its
recipients, each with their own trust stage, tone calibration, message
categories, and content boundaries.

**Why it matters for the Reality Show:**
Multi-recipient turns a solo show into an ensemble. When the same pet sends
different messages to Mom (companion), Kid (playful nag), and Partner (co-
companion), the SAME event produces DIFFERENT scenes from the SAME character.
That's inherently dramatic. The pet navigating different relationships is
a character study that writes itself.

For the audience, seeing how the same Chaos Gremlin behaves differently
with different family members is endlessly entertaining. The pet that's
clingy with one partner and aloof with another. The pet that's gentle with
the child but demanding with the adult. These aren't programmed behaviors —
they emerge naturally from the tone overrides and relationship types
configured per recipient.

**Why it matters for B2B:**
The B2B vet channel is a specific recipient type. The vet practice becomes
a MessageSource that sends through the entity's voice to the owner. The
entity's personality wraps around the vet's clinical information to produce
appointment reminders and care tips that feel like they come from the pet.
The relationship is: Vet → Entity → Owner, with the entity as the voice layer.

```
EntityRecipient
  ├── Entity ← the Digital Twin (one)
  ├── Recipient ← a person (many)
  ├── Relationship type ← "primary_owner", "partner", "child", "caretaker"
  ├── Recipient role ← "companion", "playful_nag", "mediator", "monitor"
  ├── Per-recipient calibration
  │     ├── RecipientPreference (persistent, evolving)
  │     ├── TrustStage (per-recipient)
  │     ├── Trigger schedule (different times for different people)
  │     ├── Message categories enabled (not all people get all types)
  │     └── Tone overrides (more humor for kid, more warmth for elder)
  ├── Content boundaries
  │     ├── Age-appropriate filter
  │     └── Information barrier (cross-recipient privacy)
  └── Enabled flag
        │
        ↓ Enables
  Same character, different performances — ensemble dynamics
  B2B channel — professional messages through entity voice
  Content variety — multiple storylines from one household
```

---

### Object 6: MessageEffectiveness (The Ratings)

**What it is:** The feedback signal that tracks whether a message achieved
its intended emotional purpose — user reactions, replies, sentiment,
response time.

**Why it matters for the Reality Show:**
Effectiveness data is the "audience research" that traditional TV spends
millions on. You know, per message, per intent, per tone calibration,
per context, what WORKS. Over time, this data answers questions no
entertainment company has been able to answer empirically:
- Do audiences prefer high-humor or medium-humor morning messages?
- Does a COMFORT message on a rainy day land better than an ENERGIZE?
- Which archetype produces the most engaging content?
- Which arc types generate the most replies (interaction = engagement)?

This data isn't just product optimization — it's content strategy for the
platform. When you know that Chaos Gremlin feeding arcs get 3x the
engagement of Gentle Soul weather arcs, you know what to feature on the
content platform's front page.

**Why it matters for B2B:**
Vet practices want to know: did the pet-voiced appointment reminder
actually reduce no-shows? Effectiveness tracking provides that answer
directly. "Messages from Max the Chaos Gremlin produced a 73% appointment
confirmation rate vs. 45% for standard SMS reminders." That's a sales
pitch backed by data.

**Quality bar for content readiness:**
- Data density: Enough effectiveness data to identify patterns.
  Target: 50+ data points per archetype before drawing content conclusions
- Signal clarity: Can you distinguish between "user didn't respond because
  message was bad" vs. "user was busy"? Target: Time-based decay model
  that weights quick responses higher
- Intent correlation: Can you map which intents produce the most engagement
  per archetype? Target: Clear top-3 intents per archetype identified

```
MessageEffectiveness
  ├── Message ID ← which message
  ├── Intended intent ← what we tried to do
  ├── Intended tone ← what emotional register we targeted
  ├── User response
  │     ├── Reaction (positive/negative/none)
  │     ├── Replied (yes/no)
  │     ├── Reply sentiment (positive/neutral/negative)
  │     └── Time to reaction (seconds)
  ├── Effectiveness score ← computed 0.0-1.0
  └── Context at delivery ← what signals were active
        │
        ↓ Aggregated into
  IntentEffectivenessReport — which intents work for which archetypes
  ToneEffectivenessReport — which tone calibrations land best
  ArcEffectivenessReport — which arc types produce engagement
        │
        ↓ Feeds
  Content curation — feature the highest-performing content styles
  B2B sales data — "our messages produce X% engagement"
  Product optimization — adjust defaults for better message quality
```

---

### Object 7: ContentArtifact (The Published Work)

**What it is:** A packaged, presentable piece of content derived from the
message stream — a shareable card, an episode, a voiced segment, a video
clip. This object doesn't exist yet in the architecture. It's the bridge
between the product layer and the content/entertainment layer.

**Why it matters:** This is the object that turns private SMS messages into
public entertainment. Without it, messages live and die in one-to-one
threads. With it, messages become reusable, presentable, followable content.

```
ContentArtifact (FUTURE — Phase 2+)
  ├── Source
  │     ├── Message IDs ← which messages comprise this content
  │     ├── Arc ID ← which arc (if any)
  │     ├── Entity ID ← which Digital Twin
  │     └── Time period ← when this content was generated
  ├── Presentation
  │     ├── Format ← "shareable_card" | "text_episode" | "audio_episode" | "video_clip"
  │     ├── Title ← generated or curated episode title
  │     ├── Narrative frame ← how the messages are presented (chronological, highlights)
  │     └── Voice data ← (Phase B) generated voice for audio/video
  ├── Consent
  │     ├── User approval status ← approved | pending | rejected
  │     ├── Approved at ← timestamp (after cooling-off period)
  │     ├── Content hash ← verify content hasn't changed since approval
  │     └── Redaction list ← specific elements user asked to remove
  ├── Distribution
  │     ├── Platform visibility ← "private" | "followers" | "public"
  │     ├── External sharing ← "allowed" | "prohibited"
  │     └── Platform placement ← featured, category, search only
  ├── Engagement
  │     ├── Views, follows, reactions, comments
  │     ├── Audience retention ← did they finish the episode?
  │     └── Share count ← viral potential
  └── Revenue
        ├── Monetization tier ← free, premium, sponsored
        ├── Revenue attribution ← which revenue stream
        └── Creator share ← % to the entity owner (incentive)
```

---

# PART II: THE GRADATION PATH

How do you get from "F02 trigger models" to "syndicated reality show"?
Through measurable gradations where each step validates the next.

---

## Gradation 1: Message Quality Foundation
**Phase:** 1B (F02, current build)
**Duration:** 4-5 weeks
**You are here.**

### What You're Building
The 7-stage message pipeline. Triggers → Signals → Composition → Generation
→ Quality Gate → Delivery → Effectiveness.

### Objects Being Created
- MessageComposition (Object 2) — the scene direction system
- MessageEffectiveness (Object 6) — the ratings system
- Foundation fields for Objects 3, 4, 5 (arc_id, life_contexts, recipient_id)

### Measurable Milestone: "The Words Are Right"
Before moving to Gradation 2, these must be true:

| Metric | Target | How to Measure |
|--------|--------|---------------|
| Voice distinctiveness | 80%+ blind identification | Parallel testing: 5 archetypes, 10 messages each, can you tell who's who? |
| Intent accuracy | 85%+ alignment | For each message, does it accomplish its stated intent? |
| Tone fidelity | Ranked correctly in blind test | Given 3 messages at different warmth levels, can tester rank them? |
| Context integration | 0 explicit context references | No message says "Based on the weather" — all natural weaving |
| Quality gate pass rate | 90%+ first-attempt | Messages generated pass quality gate without regeneration |
| No P1 failures | Zero per test session | No message could cause emotional harm in any scenario tested |
| P2 average | 3.5+ / 5.0 | Parallel testing rubric average across all dimensions |

### What This Enables
If these metrics are met, the message stream is "script-quality" — meaning
each message could stand on its own as a line of dialogue in a character-
driven narrative. Without this quality bar, nothing downstream works.

---

## Gradation 2: Message Rhythm & Self-Dogfooding
**Phase:** 1B-1D (F03-F09)
**Duration:** 3-4 weeks after Gradation 1

### What You're Building
Delivery infrastructure, trust system, birthing ceremony, feedback loops,
batch runner. The product becomes usable end-to-end.

### Objects Being Refined
- MessageComposition gains real delivery timing
- EntityProfile gains trust-stage behavioral shifts
- MessageEffectiveness starts collecting real data from your own usage

### Measurable Milestone: "The Music Is Right"
You dogfood the product for 2 weeks. These must be true:

| Metric | Target | How to Measure |
|--------|--------|---------------|
| Daily engagement | You read every message | Self-dogfooding journal |
| Message variety | No two consecutive days feel the same | Journal: "messages felt fresh today" ≥ 10/14 days |
| Timing appropriateness | Zero messages at wrong times | No messages during quiet hours, no high-energy at 11pm |
| Personality consistency | Entity sounds the same across 14 days | Day 14 message is identifiably the same character as Day 1 |
| Emotional resonance | At least 1 "smile moment" per day | Journal: "this message made me feel something" ≥ 10/14 days |
| Willingness to pay | You would pay $5.99/month for this | Honest self-assessment |
| Share impulse | At least 3 messages you wanted to screenshot | Natural "someone needs to see this" impulse |

### What This Enables
The share impulse (last metric) is the early signal for Gradation 4
(shareable cards). If YOU don't want to share messages, nobody will.
The variety and rhythm metrics determine whether message arcs (Gradation 5)
are needed sooner or later.

---

## Gradation 3: Alpha Validation & First Revenue
**Phase:** Post-MVP launch
**Duration:** 4-8 weeks

### What You're Building
Nothing new technically. You're validating with 5-10 real users, then
expanding to your first 100 paying customers.

### Objects Being Validated
- EntityProfile in the hands of real users (do THEY think it sounds like
  their pet?)
- MessageEffectiveness with real behavioral data (not your own)
- RecipientPreference initialization from archetype selection (does it work?)

### Measurable Milestone: "Other People Feel It Too"

| Metric | Target | How to Measure |
|--------|--------|---------------|
| Personality accuracy | 4.0+ / 5.0 average | Alpha survey Q1: "Does it sound like your pet?" |
| Day 14 retention | 70%+ | Alpha testers still reading messages after 2 weeks |
| Willingness to pay | 40%+ yes or maybe | Alpha survey Q6 |
| Organic mentions | At least 2 testers tell someone unprompted | Closing interview: "Did you tell anyone about this?" |
| Message variety feedback | No tester says "messages got repetitive" | Alpha survey open text |
| First 100 paying | $599/month MRR | Stripe dashboard |

### What This Enables
If 70%+ retain at Day 14 and 40%+ would pay, the core product works.
If testers tell others unprompted, organic growth is possible.
If nobody says "repetitive," arcs may not be urgent.
If they DO say repetitive, arcs become the immediate priority.

### B2B Seed (Plant Now, Harvest Later)
During alpha testing, if any tester is connected to a vet practice, ask:
"Would your vet be interested in sending appointment reminders through
your pet's voice?" One warm introduction plants the B2B seed. You don't
need to build the B2B infrastructure yet — you need ONE vet who says
"that's interesting." That conversation shapes everything that follows.

---

## Gradation 4: Shareable Content & Viral Testing
**Phase:** 2A
**Duration:** 2-4 weeks development, then ongoing measurement

### What You're Building
Shareable Message Cards. When a user gets a great message, they tap "Share"
and get a beautifully designed card with the message, pet's name, archetype
illustration, and JimiGPT branding. Shared to Instagram, iMessage, WhatsApp.

### New Object Introduced
ContentArtifact (Object 7) — in its simplest form. A single message
packaged for external presentation. This is the smallest possible unit
of the content platform.

### Measurable Milestone: "People Want to See This"

| Metric | Target | How to Measure |
|--------|--------|---------------|
| Share rate | 5%+ of messages get shared | Shares / messages delivered |
| Share-to-signup conversion | 2%+ | New signups attributable to shared cards |
| External engagement | Shared cards get likes/comments | Track via UTM or embed analytics |
| Content diversity | All 8 archetypes represented in shares | No single archetype dominates shares |
| Organic virality | At least 1 card shared 50+ times | Social tracking |

### What This Validates
If people share message cards AND other people engage with them, two things
are proven:
1. People want to see pet Digital Twin content (content platform viable)
2. The content is engaging to people who DON'T have the product
   (audience exists beyond users)

If cards don't get shared or engagement is flat, the content platform
pivot should be delayed. Fix the message quality first.

### B2B Development (If Gradation 3 planted the seed)
If a vet expressed interest, build a minimal proof of concept:
- Create a Digital Twin for the vet's "office pet" or a sample pet
- Generate 5 appointment reminder messages in different archetype voices
- Show the vet: "This is what your clients would receive instead of
  a generic SMS"
- Measure their reaction. If they want it, you have your first B2B pilot.

The technical work: add a `source_type: "professional"` field to the
message pipeline. Route professional messages through the same quality
gate. The infrastructure is 90% built.

---

## Gradation 5: Message Arcs & Narrative Depth
**Phase:** 2B
**Duration:** 3-4 weeks development

### What You're Building
The arc orchestrator. Message arcs become real — feeding anticipation
sequences, weather day threads, life event narratives.

### Objects Being Created
- MessageArc (Object 3) — the episode structure
- ArcMessage — the scene within an episode
- Arc templates (YAML configs) — the episode formats

### Measurable Milestone: "The Stories Are Compelling"

| Metric | Target | How to Measure |
|--------|--------|---------------|
| Arc completion rate | 90%+ arcs reach resolution | Arc state tracking |
| Engagement lift | 20%+ increase in reply rate during arcs vs. single messages | Effectiveness comparison |
| Share rate during arcs | Higher share rate on arc messages than single messages | Content analytics |
| User awareness of arcs | 60%+ of users notice narrative continuity | Survey: "Do messages sometimes connect to each other?" |
| Content team curation | You can select 3 "great episodes" per week from user base | Manual review of arc narratives |

### What This Validates
If arcs produce measurably higher engagement than single messages, the
"episode" format works. If you can curate compelling episodes weekly,
the content platform has a content supply.

### Arc Types as Content Genres

Each arc type maps to a content genre. This is important for the
content platform's editorial structure:

| Arc Type | Content Genre | Entertainment Analog |
|----------|--------------|---------------------|
| Feeding anticipation | Comedy | Sitcom cold open |
| Weather day | Mood piece | Slice-of-life anime |
| Sick day care | Drama | Character-driven drama |
| Pet boarding | Adventure/diary | Travel show |
| Multi-pet interaction | Ensemble comedy | Buddy sitcom |
| Life milestone | Special episode | Holiday special |
| User celebration | Feel-good | Hallmark moment |
| User returning home | Reunion | Series finale energy |

---

## Gradation 6: Private Social Network
**Phase:** 3A
**Duration:** 4-6 weeks development

### What You're Building
The community tab. Digital Twins post in a shared space. Users interact
through their pets, not as themselves.

### Objects Being Created
- Social identity for entities (how they behave in group settings)
- Community moderation framework
- Entity-to-entity interaction (Chaos Gremlin commenting on Regal One's post)

### Measurable Milestone: "Digital Twins Have Social Dynamics"

| Metric | Target | How to Measure |
|--------|--------|---------------|
| Network density | 200+ active entities posting | Platform analytics |
| Interaction rate | 30%+ of posts receive entity comments | Engagement analytics |
| Return visits | Users check the community feed 3+ times/week | App analytics |
| Personality in social context | Entity comments match archetype voice | Quality review |
| User satisfaction | "The community makes me want to stay subscribed" | Survey |

### What This Validates
If Digital Twins create entertaining social dynamics, the content has
enough variety and interplay for a content platform. If the community
is dead or boring, the content platform needs more arc depth first.

---

## Gradation 7: Digital Twin Content Platform (JimiGPT)
**Phase:** 4
**Duration:** 6-8 weeks development

### What You're Building
The content platform. Public-facing (opted-in). Message streams and arcs
presented as episodic entertainment. Audience follows specific Digital
Twins. Curated featured content.

### All Seven Objects Working Together

```
EntityProfile (character) →
  MessageComposition (scene direction) →
    MessageArc (episode structure) →
      LifeContext (plot line) →
        EntityRecipient (ensemble dynamics) →
          MessageEffectiveness (ratings) →
            ContentArtifact (published episode)
```

### Measurable Milestone: "This Is Entertainment"

| Metric | Target | How to Measure |
|--------|--------|---------------|
| External audience | 1,000+ non-JimiGPT-users following Digital Twins | Platform registration |
| Audience retention | 40%+ return within 7 days | Cohort analysis |
| Content consumption | Average 5+ "episodes" viewed per visit | Session analytics |
| Audience-to-user conversion | 3%+ of audience signs up for JimiGPT | Funnel tracking |
| Revenue from content | Any non-zero revenue from ads or premium access | Stripe |
| Media interest | At least 1 journalist or blogger covers it | PR tracking |

### Modality Expansion Path

```
Phase A: Text episodes (web interface)
  Cost: Interface development only. Content is free (already generated).
  Revenue: Free with premium follows
  ↓
Phase B: Audio episodes (podcast)
  Cost: Voice generation per episode (ElevenLabs API costs)
  Revenue: Podcast ads, premium audio
  Technology: ElevenLabs voices matched to archetype personality
  Format: 5-min daily, 2-3 Digital Twins per episode
  ↓
Phase C: Video episodes (streaming)
  Cost: AI video generation per episode
  Revenue: Streaming subscription, syndication licensing
  Technology: Runway/Sora for visual scenes from message scripts
  Format: 3-5 min shorts, weekly compilation "episodes"
  ↓
Phase D: Syndication
  Revenue: Licensing deals with streaming platforms or networks
  Format: 22-min weekly episodes compiled from best content
  Target: Pet-focused channels, family entertainment
```

---

## Gradation 8: AI-Companion Participatory Narrative (Cross-Category)
**Phase:** 5+
**Duration:** Ongoing expansion

### What You're Building
The two-layer architecture applied to NeuroAmigo and other Emotional AI
products. Layer 1: Companion helps user. Layer 2: Audience watches and
encourages. Audience signal feeds back to companion.

### New Objects Required

**AudienceSignal:**
```
AudienceSignal
  ├── Source
  │     ├── Follower ID (anonymous)
  │     ├── Follower type ← "invested" (3+ weeks) | "casual"
  │     └── Follower history ← how long following this journey
  ├── Signal
  │     ├── Type ← "encouragement" | "celebration" | "solidarity"
  │     ├── Content ← reaction emoji, short message, or structured response
  │     └── Timestamp
  ├── Delivery
  │     ├── Eligible for delivery to user? ← filtered by companion
  │     ├── Personalized? ← "Sarah, who's been following for 3 weeks..."
  │     └── Delivered at ← when companion included this in a message
  └── Moderation
        ├── Auto-filtered? ← negative, dismissive, harmful
        ├── Contains advice? ← filtered unless user opts in
        └── Quality score ← signal-to-noise ratio
```

**ConsentArchitecture:**
```
ConsentArchitecture
  ├── User opt-in level
  │     ├── "share_nothing" ← Layer 2 doesn't exist for this user
  │     ├── "share_summaries" ← daily summary only, no individual messages
  │     ├── "share_arcs" ← completed arcs only, user reviews after cooling-off
  │     ├── "share_live" ← real-time sharing (highest engagement, highest risk)
  │     └── Custom ← per-arc-type granularity
  ├── Cooling-off period
  │     ├── Duration ← 24 hours default
  │     ├── Content locked during cooling-off ← visible to user, not audience
  │     └── Auto-approve after cooling-off? ← user choice
  ├── Redaction
  │     ├── User can remove any shared content at any time
  │     ├── Audience sees "This moment has been made private"
  │     └── No archive, no cache — truly removed
  ├── Never-share categories
  │     ├── Medical details
  │     ├── Crisis moments
  │     ├── Financial information
  │     ├── Identifying details (real names, locations, workplaces)
  │     └── Content involving third parties who haven't consented
  └── Departure protocol
        ├── User stops sharing → graceful closure message to audience
        ├── No guilt mechanism ← never "your followers will miss you"
        ├── Content remains or removed ← user's choice
        └── Audience redirected to other journeys
```

---

# PART III: THE B2B LOGICAL PATH

The B2B channel (vets, pet stores, pet services) has its own object
structure and gradation path.

---

## B2B Core Object: ProfessionalAccount

```
ProfessionalAccount
  ├── Business identity
  │     ├── Business ID, name, type ("vet_practice" | "pet_store" | "groomer")
  │     ├── Verified status ← must be verified to send through entities
  │     └── Content permissions ← what categories of messages they can send
  ├── Connected entities
  │     ├── Which Digital Twins are connected to this business
  │     ├── Connection type ← "patient" (vet), "customer" (store)
  │     └── Owner consent ← explicitly opted in per entity per business
  ├── Message templates
  │     ├── Appointment reminder template
  │     ├── Medication reminder template
  │     ├── Wellness check template
  │     ├── Product recommendation template (pet stores)
  │     └── Custom templates (business creates, system reviews)
  ├── Message flow
  │     ├── Business triggers message with context (appointment date, product name)
  │     ├── System generates message in entity's voice using business context
  │     ├── Quality gate applies (business content boundaries + entity personality)
  │     ├── Message appears to come from pet, not business
  │     └── Effectiveness tracked (did user confirm appointment? buy product?)
  └── Revenue
        ├── Per-message pricing (¢10-25 per message)
        ├── Monthly subscription ($29-99/month based on patient/customer count)
        └── Effectiveness premium (higher price for proven engagement rates)
```

## B2B Gradation Path

| Step | What | Validates | Target |
|------|------|-----------|--------|
| 1. Warm intro | Find 1 vet who's interested | Is there demand? | 1 conversation |
| 2. Manual pilot | Generate 10 messages manually for the vet's patients | Does the voice work for professional messages? | 5 patients respond positively |
| 3. Semi-automated | Build minimal professional message routing | Can the system generate professional messages at acceptable quality? | 20 patients, 60%+ confirmation rate |
| 4. Self-serve | Build professional dashboard for vets to manage their entity connections | Can vets use this without hand-holding? | 3 vet practices using independently |
| 5. Pet stores | Extend to pet supply stores with product recommendation templates | Does the model work beyond healthcare? | 2 pet stores piloting |
| 6. Scale | Sales playbook, pricing tiers, case studies with engagement data | Is this a repeatable B2B revenue channel? | $2,000+ MRR from B2B |

**The key B2B insight:** The effectiveness data (Object 6) is the B2B sales
weapon. When you can say "pet-personality-voiced appointment reminders have
73% confirmation rate vs. 45% for generic SMS," the ROI sells itself.
You need Gradation 3 (alpha validation) data before approaching any business.

---

# PART IV: WHAT F02 CREATES FOR ALL OF THIS

Every task in F02 is a brick in the foundation of everything described above.
Here's the direct connection:

| F02 Task | What It Builds | What It Enables Downstream |
|----------|---------------|---------------------------|
| T1: Trigger Models | When messages fire | Episode timing, arc triggers, B2B scheduled messages |
| T2-T4: Trigger Evaluation | Smart scheduling | Multi-pet coordination, arc orchestration |
| T5-T6: Signal Collection | Context awareness | Life event detection, user context injection |
| T7: Intent Selection | Emotional purpose per message | 14 "scene types" for content, editorial curation by intent |
| T8: Tone Calibration | Emotional color grading | Mood-based content curation, life context tone shifts |
| T9: Recipient State | Meeting users where they are | Multi-recipient tone adjustment, audience state awareness |
| T10: Message Composer | Full scene direction | Arc composition, ContentArtifact metadata, B2B message routing |
| T11: LLM Generator | The actual dialogue | Every line of the "show" comes from here |
| T12: Quality Gate | Trust protection | Content moderation foundation, B2B content boundary enforcement |
| T13: Effectiveness | The ratings | Content curation signals, B2B engagement proof, product optimization |
| T14: Integration Test | Everything works together | The end-to-end pipeline that generates every future piece of content |

**The bottom line:** F02 is not "building a message pipeline." F02 is building
the content generation engine for an entertainment platform, the delivery
infrastructure for a B2B communication channel, and the script writer for
a reality show — all in one pipeline. The same code serves all three purposes.
The only difference is the interface layer on top.

---

# PART V: MARKET GRADATION CHECKLIST

Development milestones have corresponding market milestones. Both must
advance together.

## Market Actions by Phase

### Phase 1 (During Build — NOW)
- [ ] Start Reddit observation: r/pets, r/dogs, r/cats — 15 min/day
- [ ] Note language patterns: how do pet owners talk about their pets?
- [ ] Identify 5 potential alpha testers in your network
- [ ] Follow 10 pet influencers on Instagram/TikTok — study what content gets engagement
- [ ] Create @JimiGPT social accounts (reserve the name even if you don't post)
- [ ] Document 10 "human situations" where pet Digital Twin messages would be valuable
  (you've already started this — formalize it)

### Phase 1D (Alpha Testing)
- [ ] Recruit 5-10 alpha testers with personal outreach
- [ ] Conduct onboarding calls — watch their reaction to personality reveal
- [ ] Collect Day 7 and Day 14 surveys
- [ ] Ask: "Would your vet be interested in this?" (B2B seed)
- [ ] Ask: "Did you screenshot or show anyone a message?" (content signal)
- [ ] Ask: "What would make you tell a friend?" (referral mechanic)

### Phase 2 (Post-MVP, 100+ Users)
- [ ] Launch shareable message cards
- [ ] Track sharing behavior organically (don't push it)
- [ ] Post 3 message card examples on JimiGPT social accounts (your own pet)
- [ ] Approach 1 vet practice with manual pilot proposal
- [ ] Monitor: which archetype produces the most shared content?
- [ ] Begin Reddit engagement: share your own message card in r/pets
  ("My dog's Digital Twin sent me this and I can't stop laughing")

### Phase 3 (500+ Users, Revenue Covering Costs)
- [ ] Launch private social network (community tab)
- [ ] Begin curating "best moments of the week" from community
- [ ] Approach pet bloggers/journalists: "Your pet could have a Digital Twin"
- [ ] B2B: 3 vet practices in pilot program
- [ ] B2B: approach 1 pet supply store
- [ ] Content: start a weekly "best pet moments" compilation on social media

### Phase 4 (Content Platform)
- [ ] Launch text-based content platform
- [ ] Feature 10 "star" Digital Twins with compelling ongoing narratives
- [ ] Begin audio pilot: voice 3 Digital Twins using ElevenLabs
- [ ] Pitch to pet podcasts: "Guest segment: what your pet is really thinking"
- [ ] B2B: publish case study with engagement data
- [ ] Media: pitch to local/pet media: "The first reality show starring AI pets"

### Phase 5 (Participatory Narrative)
- [ ] Launch NeuroAmigo with participatory content architecture
- [ ] Two-layer system: companion support + audience encouragement
- [ ] Pitch to mental health media: "AI companions as community support"
- [ ] Institutional outreach: universities, corporate wellness programs
- [ ] Syndication exploration: approach streaming platforms with pilot

---

*This document is a living reference. Print it. Take notes in the margins.
The logical objects won't change — they're the atoms. The gradation
targets will be adjusted based on reality. Review monthly against
actual progress.*

*Last updated: March 2026*
