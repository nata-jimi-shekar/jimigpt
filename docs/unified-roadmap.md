# Unified Implementation Roadmap
## All Phases, All Workstreams, One Document

**Version:** 1.0
**Created:** March 2026
**Source consolidation:** This document replaces scattered phase definitions across
message-modeling.md, future-architecture.md, model-resilience-intelligence.md,
jimigpt-architecture.md, and ideas-parking-lot.md. Those documents retain their
detailed designs. This document is the SINGLE SOURCE for "what happens when."

> **Rule:** Check this document before starting any new phase. It tells you
> what to build, what must be true before you start, and what success looks like.

---

## Phase Overview

| Phase | Name | Duration | Revenue Target | Features |
|-------|------|----------|---------------|----------|
| **1A** | Personality Foundation | 1 week | $0 | F01 |
| **1B** | Message Engine + Resilience | 3 weeks | $0 | F02, R01, F03, F04 |
| **1C** | Product Infrastructure | 2 weeks | $0 | F05, F06, F07 |
| **1D** | Feedback, Operations & Dogfooding | 3 weeks | $0 | F08, F09, self-dogfood |
| **2A** | Alpha + First Revenue | 4-6 weeks | $599/mo (100 users) | Alpha testing, shareable cards |
| **2B** | Intelligence + Arcs | 4 weeks | $1,500/mo (250 users) | Effectiveness analytics, message arcs, multi-provider |
| **2C** | Life Events + Context | 3 weeks | $2,500/mo (400 users) | Life contexts, user context signals, weather/calendar |
| **3A** | Community + Multi-Recipient | 4 weeks | $4,000/mo (600 users) | Private social network, multi-recipient, multi-pet |
| **3B** | B2B Pilot + Local Intelligence | 4 weeks | $6,000/mo (800 users + B2B) | Vet pilot, local classifiers, fine-tuning prep |
| **4** | Content Platform | 6 weeks | $10,000/mo | Pet reality show (text), audio pilot |
| **5** | Participatory Narrative + Scale | Ongoing | $25,000+/mo | Cross-category, NeuroAmigo launch, syndication |

---

## PHASE 1A: PERSONALITY FOUNDATION
**Status: COMPLETE**

### What Was Built
- F01: Four-layer personality model, 8 archetypes, blending, prompt builder,
  ToneSpectrum, MessageIntent enum

### Entry Criteria
- None (starting point)

### Exit Criteria (all met)
- [x] All Pydantic models validate with mypy --strict
- [x] 8 archetype YAML files load and parse
- [x] Archetype blending produces valid EntityProfile
- [x] Prompt builder produces complete 7-block system prompt
- [x] All tests pass

---

## PHASE 1B: MESSAGE ENGINE + RESILIENCE
**Status: F02 COMPLETE, R01 NEXT**

### What to Build

| Feature | Tasks | Hours | Status |
|---------|-------|-------|--------|
| F02: Message Pipeline | 14 tasks | 6.5h | COMPLETE |
| R01: LLM Abstraction & Intelligence Foundation | 8 tasks | 3h | **NEXT** |
| F03: Delivery Layer | 6 tasks | 2h | Not started |
| F04: Trust & Safety | 4 tasks | 1.5h | Not started |

### Build Order
```
F02 (complete) → R01 (LLM abstraction) → F03 (delivery) → F04 (trust)
```

**Why R01 before F03:** F03's delivery layer sends messages through the
generator. If the generator still has hard Anthropic dependency when F03
wires it to the scheduler, the hard dependency propagates into operations.
Abstracting now means F03 builds on a provider-agnostic foundation.

### Entry Criteria
- F01 complete and merged

### Exit Criteria
- [ ] Full 7-stage pipeline generates messages from composed specifications
- [ ] **LLM provider abstraction in place — generator is provider-agnostic**
- [ ] **Generation logging captures every message as training data**
- [ ] **Personality fingerprint models defined and extractable**
- [ ] **Routing config exists with fallback chain defined**
- [ ] SMS delivery works with timezone awareness and retry logic
- [ ] Trust ladder evaluates and progresses based on interaction signals
- [ ] Escalation detects distress and vet deflection works
- [ ] All foundation fields (arc, recipient, life context) present and tested
- [ ] Quality gate includes consecutive coherence check
- [ ] All tests pass, CI green

### Review Checkpoints
- Codex review: after F02 (done), after R01, after F03, after F04
- Opus review: F02-T7,T8,T10,T11,T12 (done); R01-T3,T5; F03-T3; F04-T2,T3
- Gemini strategic: after F02+R01 (first complete pipeline + resilience)
- Parallel message testing: starts after F02-T11 (done), continues through phase

---

## PHASE 1C: PRODUCT INFRASTRUCTURE
**Status: NOT STARTED**

### What to Build

| Feature | Tasks | Hours | Status |
|---------|-------|-------|--------|
| F05: Database, Auth & Payments | 6 tasks | 2.5h | Not started |
| F06: Birthing Ceremony API | 5 tasks | 2h | Not started |
| F07: Frontend Birthing | 9 tasks | 3.5h | Not started |

### Build Order
```
F05 (database + gen log table) → F06 (birthing API) → F07 (frontend)
```

### Entry Criteria
- Phase 1B complete (pipeline + resilience + delivery + trust)

### Exit Criteria
- [ ] All database tables created including **message_generation_log**
- [ ] **Generation log writes to database (R01 local storage → DB wiring)**
- [ ] **Effectiveness flows back to generation_log rows when users react**
- [ ] Foundation columns on messages table (recipient_id, arc_id, life_context)
- [ ] Auth works end-to-end (signup, login, JWT middleware)
- [ ] Entity CRUD operations work with Supabase
- [ ] Stripe checkout and subscription webhooks work
- [ ] Birthing ceremony creates complete Digital Twin with RecipientPreference
- [ ] Frontend birthing flow works on mobile and desktop
- [ ] Birth certificate generates and is shareable
- [ ] All tests pass

### Review Checkpoints
- Codex review: after F05, after F06, after F07
- Opus review: F05-T2 (schema), F05-T4 (auth), F05-T5 (gen log wiring), F05-T6 (Stripe)
- Gemini strategic: after F06 ("Does this onboarding create the right first impression?")

---

## PHASE 1D: FEEDBACK, OPERATIONS & DOGFOODING
**Status: NOT STARTED**

### What to Build

| Feature | Tasks | Hours | Status |
|---------|-------|-------|--------|
| F08: Feedback & Refinement | 6 tasks | 2.5h | Not started |
| F09: Batch Runner & Monitoring | 6 tasks | 2.5h | Not started |
| Self-dogfooding | 14 days | — | Not started |

### Build Order
```
F08 (feedback) → F09 (operations + provider monitoring) → Self-dogfood 14 days
```

### Entry Criteria
- Phase 1C complete (full product buildable)

### Exit Criteria
- [ ] Debrief loop generates personality refinement questions
- [ ] Message reactions tracked and accumulated
- [ ] **Recipient preference evolves from reactions**
- [ ] Quiet mode works instantly
- [ ] Nightly batch generates messages through **provider factory**
- [ ] **Each generation logged to message_generation_log**
- [ ] Delivery queue processes messages reliably
- [ ] **Provider health monitored (latency, error rate, cost)**
- [ ] **Daily cost summary logged**
- [ ] **Personality fingerprint baselines established for all 8 archetypes**
- [ ] 14-day self-dogfooding journal complete
- [ ] Parallel testing P2 average ≥ 3.5/5.0
- [ ] Zero P1 failures in any test session
- [ ] You would pay $5.99/month for this (honest self-assessment)

### Review Checkpoints
- Codex review: after F08, after F09
- Opus review: F08-T6 (preference evolution)
- Gemini strategic: after F08 ("Is the feedback loop teaching us what we need?")
- Parallel message testing: throughout (target: weekly sessions)

---

## PHASE 2A: ALPHA + FIRST REVENUE
**Status: NOT STARTED**

### What to Build

| Work | Duration | Description |
|------|----------|-------------|
| Alpha recruitment | 1 week | Recruit 5-10 pet owners from network + Reddit |
| Alpha onboarding | 1 week | Personal calls, watch personality reveal reaction |
| Alpha running | 2 weeks | Users receive messages daily, surveys at Day 7 and Day 14 |
| Shareable message cards | 1 week dev | Beautifully designed share cards (Phase 2 stepping stone) |
| Launch to 100 users | 2-4 weeks | Expand from alpha to first paying customers |

### New Development
- Shareable message cards (frontend feature, ~2 tasks)
- Alpha feedback integration (process survey results, adjust)
- Payment flow live (Stripe connected to real accounts)

### Entry Criteria (Gate: Phase 1D exit criteria met)
- 14-day self-dogfooding complete with positive journal
- P2 message quality average ≥ 3.5/5.0
- Zero P1 safety failures

### Exit Criteria & Measurements

| Metric | Target | How |
|--------|--------|-----|
| Personality accuracy | 4.0+ / 5.0 | Alpha survey Q1 |
| Day 14 retention | 70%+ | Alpha tester still reading messages |
| Willingness to pay | 40%+ yes/maybe | Alpha survey Q6 |
| Organic mentions | 2+ unprompted | Closing interview |
| First 100 paying users | $599/month MRR | Stripe dashboard |
| Share rate (if cards launched) | 5%+ of messages shared | Analytics |
| B2B seed planted | 1 vet conversation | "Would your vet be interested?" |

### Market Actions
- [ ] Reddit engagement: share message cards in r/pets, r/dogs, r/cats
- [ ] @JimiGPT social accounts active with sample content
- [ ] 1 warm intro to vet practice (B2B seed)
- [ ] Collect "Did you screenshot a message?" data (content signal)

---

## PHASE 2B: INTELLIGENCE + ARCS
**Status: NOT STARTED**

### What to Build

| Work | Duration | Description |
|------|----------|-------------|
| Effectiveness analytics engine | 1 week | Intent reports, tone reports, timing reports from generation_log |
| OpenAI provider implementation | 3 days | GPT-4o-mini as fallback provider |
| Multi-provider routing | 3 days | Active routing rules, fallback chain operational |
| 5% quality comparison | 3 days | Side-by-side model testing logged |
| Cached message pool | 3 days | Pre-generated fallback messages per archetype |
| Message arc orchestrator | 1 week | Arc templates, state management, scheduling |
| Arc templates (JimiGPT) | 3 days | feeding_anticipation, weather_day, sick_day, etc. |

### Entry Criteria (Gate: Phase 2A exit criteria met)
- 100+ paying users
- 5,000+ generation_log records (enough for meaningful analytics)
- Share cards validated (people engage with pet content)

### Exit Criteria & Measurements

| Metric | Target | How |
|--------|--------|-----|
| Provider fallback works | Zero message gaps in 30 days | Monitor: fallback events logged |
| Cost tracked per message | Dashboard shows daily spend | Provider health monitoring |
| Personality drift detected | Fingerprint runs weekly, alerts on drift > 0.2 | Automated fingerprint script |
| Intent effectiveness known | Top 3 intents identified per archetype | Analytics engine reports |
| Arc engagement lift | 20%+ higher reply rate during arcs | A/B: arc vs single message |
| Arc completion | 90%+ arcs resolve naturally | Arc state tracking |
| User count | 250+ paying | Stripe |
| MRR | $1,500+ | Stripe |

### Intelligence Milestones
- [ ] Effectiveness data consumed by intent selector (feedback loop closed)
- [ ] Tone calibration nudged by effectiveness data
- [ ] Model comparison data (Anthropic vs OpenAI) accumulating
- [ ] Personality fingerprint baselines updated weekly

---

## PHASE 2C: LIFE EVENTS + CONTEXT
**Status: NOT STARTED**

### What to Build

| Work | Duration | Description |
|------|----------|-------------|
| LifeContext model + templates | 3 days | YAML templates for sick_day, pet_vet, traveling, etc. |
| User reply classification | 1 week | Sentiment + context tag extraction from replies |
| Life context activation | 3 days | Reply keywords, in-app toggles |
| Weather signal collector | 3 days | OpenWeatherMap API integration |
| Calendar signal collector | 1 week | Google Calendar OAuth integration |
| Life context → arc integration | 3 days | Life events auto-trigger appropriate arcs |

### Entry Criteria (Gate: Phase 2B exit criteria met)
- Arcs working and producing engagement lift
- 250+ users generating enough life event signals to test

### Exit Criteria & Measurements

| Metric | Target | How |
|--------|--------|-----|
| Life context activation rate | 20%+ of users activate at least once | Analytics |
| Context-aware messages | Users notice weather/calendar awareness | Survey |
| Reply classification accuracy | 80%+ sentiment, 70%+ context tags | Manual validation sample |
| Life event arc quality | P2 score ≥ 4.0 during life contexts | Parallel testing |
| User count | 400+ paying | Stripe |
| MRR | $2,500+ | Stripe |

---

## PHASE 3A: COMMUNITY + MULTI-RECIPIENT
**Status: NOT STARTED**

### What to Build

| Work | Duration | Description |
|------|----------|-------------|
| Private social network (community tab) | 2 weeks | Entity-to-entity posting and interaction |
| EntityRecipient model + DB | 3 days | Many-to-many entity↔recipient |
| Per-recipient configuration | 1 week | Trust, schedule, tone per recipient |
| Multi-pet coordination | 3 days | Message spacing, sibling awareness |
| Information barriers | 3 days | Cross-recipient privacy enforcement |

### Entry Criteria (Gate: Phase 2C exit criteria met)
- 400+ users (enough for community density)
- Revenue covering operational costs
- Life events and arcs producing compelling narratives

### Exit Criteria & Measurements

| Metric | Target | How |
|--------|--------|-----|
| Community density | 200+ entities posting | Platform analytics |
| Interaction rate | 30%+ posts get comments | Engagement analytics |
| Return visits | 3+/week to community tab | App analytics |
| Multi-recipient adoption | 10%+ of users add a recipient | Feature analytics |
| User count | 600+ paying | Stripe |
| MRR | $4,000+ | Stripe |

---

## PHASE 3B: B2B PILOT + LOCAL INTELLIGENCE
**Status: NOT STARTED**

### What to Build

| Work | Duration | Description |
|------|----------|-------------|
| B2B: Professional message routing | 1 week | source_type: "professional", content boundaries |
| B2B: Vet pilot (3 practices) | 2 weeks | Manual onboarding, measure confirmation rates |
| B2B: Professional dashboard (minimal) | 1 week | Vet manages connected entities, sends messages |
| Local sentiment classifier | 3 days | DistilBERT for reply sentiment (replaces rules) |
| Local context tagger | 3 days | Reply context tag extraction (replaces empty list) |
| Intent classifier training | 1 week | Train on 5,000+ effectiveness records |
| Tone predictor training | 1 week | Train on 10,000+ effectiveness records |

### Entry Criteria (Gate: Phase 3A exit criteria met + data thresholds)
- 600+ users
- 30,000+ generation_log records with effectiveness scores
- At least 1 vet practice expressing concrete interest (from Phase 2A seed)

### Exit Criteria & Measurements

| Metric | Target | How |
|--------|--------|-----|
| B2B confirmation rate | 60%+ appointment confirmations | Vet pilot data |
| B2B vet satisfaction | 3+ practices want to continue | Pilot feedback |
| Local classifier accuracy | 80%+ sentiment, 70%+ context tags | Validation set |
| Intent classifier performance | Beats rule-based by 10%+ on effectiveness | A/B test |
| Cost reduction | 30%+ from local classification offload | Cost monitoring |
| User count | 800+ paying | Stripe |
| MRR (consumer) | $4,800+ | Stripe |
| MRR (B2B) | $1,200+ | Stripe |
| **Total MRR** | **$6,000+** | Stripe |

### Intelligence Milestones
- [ ] 90% of pipeline intelligence runs locally (classification)
- [ ] Only generation calls external API
- [ ] Intent selection learned from data, not just rules
- [ ] Tone calibration learned from data, not just rules
- [ ] Fine-tuning dataset preparation started (top 50% effectiveness messages)

---

## PHASE 4: CONTENT PLATFORM
**Status: NOT STARTED**

### What to Build

| Work | Duration | Description |
|------|----------|-------------|
| Content platform (text episodes) | 2 weeks | Web interface presenting message streams as episodes |
| Content curation system | 1 week | Select best narratives, feature "star" Digital Twins |
| Audience following system | 1 week | Follow specific Digital Twins, notifications |
| ContentArtifact model | 3 days | Consent, presentation format, distribution settings |
| Audio pilot (3 Digital Twins) | 1 week | ElevenLabs voices matched to archetype personality |
| Consent architecture | 1 week | Opt-in levels, cooling-off period, redaction |

### Entry Criteria (Gate: Phase 3A exit criteria met)
- Shareable cards shared 1,000+ times organically
- Private social network active and producing entertaining dynamics
- Message arcs producing curated "episodes" weekly
- Legal review of content rights framework complete

### Exit Criteria & Measurements

| Metric | Target | How |
|--------|--------|-----|
| External audience | 1,000+ non-users following | Platform registration |
| Audience retention | 40%+ return within 7 days | Cohort analysis |
| Audience-to-user conversion | 3%+ sign up for JimiGPT | Funnel tracking |
| Media interest | 1+ journalist/blogger covers it | PR tracking |
| Audio pilot engagement | Listeners complete 80%+ of episodes | Audio analytics |
| MRR (consumer) | $6,000+ | Stripe |
| MRR (B2B) | $2,000+ | Stripe |
| MRR (content/ads) | $2,000+ | Platform revenue |
| **Total MRR** | **$10,000+** | Combined |

---

## PHASE 5: PARTICIPATORY NARRATIVE + SCALE
**Status: NOT STARTED**

### What to Build

| Work | Duration | Description |
|------|----------|-------------|
| NeuroAmigo launch | 6-8 weeks | Second Emotional AI product using shared engine |
| Two-layer participatory architecture | 4 weeks | Companion support + audience encouragement loop |
| Audience feedback → companion signal | 2 weeks | Encouragement filtered and delivered to user |
| Fine-tuned local generation model | 4 weeks | Trained on 50,000+ scored messages |
| Video pilot (AI-generated scenes) | 4 weeks | Runway/Sora for visual content from scripts |
| Syndication exploration | Ongoing | Pitch curated content to streaming/media |

### Entry Criteria (Gate: Phase 4 exit criteria met + data thresholds)
- Content platform live with 1,000+ external audience
- 50,000+ generation_log records with effectiveness scores
- NeuroAmigo architecture designed (separate product, shared engine)
- Revenue covering full development costs ($10K+/month)

### Exit Criteria & Measurements

| Metric | Target | How |
|--------|--------|-----|
| NeuroAmigo active users | 200+ | Product analytics |
| Participatory narrative engagement | Users report feeling supported | Survey |
| Fine-tuned model quality | Matches frontier on 80% of standard messages | A/B test |
| Cost per message (blended) | <$0.0004 | Cost monitoring |
| Revenue (total across products) | $25,000+/month | Combined Stripe |
| Syndication interest | 1+ streaming platform conversation | Business development |

---

## FEATURE EXECUTION ORDER (COMPLETE)

```
PHASE 1A:  F01 ✓
PHASE 1B:  F02 ✓ → R01 → F03 → F04
PHASE 1C:  F05 → F06 → F07
PHASE 1D:  F08 → F09 → Self-dogfood (14 days)
PHASE 2A:  Alpha (5-10 users) → Shareable cards → First 100 paying
PHASE 2B:  Effectiveness analytics → Multi-provider → Arcs
PHASE 2C:  Life events → Weather/calendar signals → Reply classification
PHASE 3A:  Private social network → Multi-recipient → Multi-pet
PHASE 3B:  B2B vet pilot → Local classifiers → Intent/tone training
PHASE 4:   Text content platform → Audio pilot → Consent architecture
PHASE 5:   NeuroAmigo → Participatory narrative → Fine-tuned models → Video
```

---

## CUMULATIVE HOURS (Phase 1 Development Only)

| Feature | Tasks | Hours |
|---------|-------|-------|
| F01: Personality Engine | 10 | 4.0h |
| F02: Message Pipeline | 14 | 6.5h |
| R01: LLM Abstraction | 8 | 3.0h |
| F03: Delivery Layer | 6 | 2.0h |
| F04: Trust & Safety | 4 | 1.5h |
| F05: Database, Auth & Payments | 6 | 2.5h |
| F06: Birthing Ceremony API | 5 | 2.0h |
| F07: Frontend Birthing | 9 | 3.5h |
| F08: Feedback & Refinement | 6 | 2.5h |
| F09: Batch Runner & Monitoring | 6 | 2.5h |
| **Total** | **74** | **~30h** |

Plus 14 days self-dogfooding, alpha testing, and ongoing parallel
message testing throughout.

---

## REVIEW CADENCE ACROSS ALL PHASES

| Review Type | When | Phase 1 Count |
|-------------|------|---------------|
| Sonnet + TDD (every task) | After every task | 74 |
| Opus (high-blast tasks) | F02, R01, F03, F04, F05 | ~15 tasks |
| Codex (every feature) | After F01-F09 + R01 | 10 reviews |
| Gemini (strategic) | After F02+R01, F04, F06, F08 | 4 reviews |
| Parallel message testing | Ongoing from F02-T11 | Weekly |

---

*This is the single source of truth for implementation phases.
All other documents reference this. Updated as phases complete.*

*Last updated: March 2026*
