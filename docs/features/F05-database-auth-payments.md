# F05: Database, Auth & Payments

**Phase:** 1C
**Priority:** 5
**Architecture Reference:** Category Architecture Sections 8, 9
**JimiGPT Reference:** JimiGPT Architecture Section 9
**Additional Reference:** docs/model-resilience-intelligence.md (generation log table),
docs/foundation-per-feature.md (schema foundation fields)

## Feature Description

Set up Supabase database with all shared tables, authentication via Supabase Auth,
and Stripe payment integration for subscriptions. This connects all the backend
engines to persistent storage and user management.

**Intelligence foundation included:** This feature adds the message_generation_log
table that captures every generation as a future training example. This is the
single most important table for long-term intelligence accumulation — every
message generated without this table is a training example lost forever.

## Dependencies
- F01, F02, R01, F03, F04 (all engine code — this wires them to the database)

## What "Done" Looks Like
- All database tables created in Supabase
- User signup/login works via Supabase Auth
- Entity CRUD operations work (create, read, update, delete)
- Message history persists to database
- **Generation log persists to database (intelligence collection)**
- Stripe subscription checkout works
- All tests pass

---

## Micro-Tasks

### Task 1: Supabase Client Setup
**Time:** 20 min
**Context:** Read docs/category-architecture.md Section 8 (Database Schema)
**What to do:**
- Create src/shared/database.py with:
  Supabase client initialization from env vars
  get_supabase_client() function
- Create src/shared/config.py (if not already from F03):
  Settings class with all env vars via pydantic-settings
- Create .env.example with all required env vars
- Write test that client initializes (mock)
**Done when:** Supabase client configurable from env vars
**Commit:** `feat(shared): add Supabase client setup`

### Task 2: Database Migration — Core Tables + Intelligence Tables
**Time:** 30 min (was 25 — added generation log and foundation columns)
**Context:** Read docs/category-architecture.md Section 8 (full SQL schema).
Read docs/model-resilience-intelligence.md Part 4 (generation log table).
Read docs/foundation-per-feature.md (F05 section).
**What to do:**
- Create scripts/migrate.sql with all shared tables:
  user_profiles, entities, messages, delivery_queue,
  trust_events, archetype_configs, recipient_preferences
- **FOUNDATION columns on messages table:**
  - `recipient_id UUID` (nullable, defaults to user_id — multi-recipient ready)
  - `arc_id UUID` (nullable — track which arc a message belongs to)
  - `life_context TEXT` (nullable — record active life context at generation)
  - NO unique constraint on (entity_id, user_id, scheduled_at)
- **INTELLIGENCE table — message_generation_log:**
  ```sql
  CREATE TABLE message_generation_log (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      entity_id UUID REFERENCES entities(id),
      archetype_id TEXT NOT NULL,
      recipient_id UUID,
      composition_json JSONB NOT NULL,
      prompt_text TEXT NOT NULL,
      prompt_tokens INT NOT NULL,
      generated_content TEXT NOT NULL,
      completion_tokens INT NOT NULL,
      model_used TEXT NOT NULL,
      provider TEXT NOT NULL,
      generation_latency_ms INT,
      cost_usd NUMERIC(10, 6),
      quality_passed BOOLEAN NOT NULL,
      quality_result_json JSONB,
      regeneration_count INT DEFAULT 0,
      effectiveness_score NUMERIC(3, 2),
      user_reaction TEXT,
      user_replied BOOLEAN,
      reply_sentiment TEXT,
      generated_at TIMESTAMPTZ DEFAULT NOW()
  );
  CREATE INDEX idx_gen_log_archetype ON message_generation_log(archetype_id);
  CREATE INDEX idx_gen_log_model ON message_generation_log(model_used);
  CREATE INDEX idx_gen_log_effectiveness ON message_generation_log(effectiveness_score)
      WHERE effectiveness_score IS NOT NULL;
  ```
- **RESERVED table names** (document in SQL comments, don't create):
  - entity_recipients (Phase 2 — multi-recipient)
  - life_contexts (Phase 2 — life event awareness)
  - model_comparisons (Phase 2 — A/B quality testing)
  - personality_fingerprints (Phase 2 — drift detection)
- Create scripts/seed.py that loads archetype configs
- Write test that verifies table schemas match expected structure
**Done when:** SQL script creates all tables including generation log
**Commit:** `feat(database): add core tables and intelligence generation log`

### Task 3: Entity CRUD Operations
**Time:** 25 min
**Context:** Read docs/category-architecture.md Section 9 (API Structure)
**What to do:**
- Create src/api/entities.py with FastAPI routes:
  POST / (create entity), GET /{id}, PATCH /{id}, DELETE /{id}
- Each route interacts with Supabase
- Create entity stores full EntityProfile as JSONB
- Write tests (mock Supabase):
  - Create entity returns entity with ID
  - Get entity returns correct data
  - Update entity modifies personality
  - Delete entity removes record
**Done when:** CRUD endpoints work
**Commit:** `feat(api): add entity CRUD endpoints`

### Task 4: Supabase Auth Integration
**Time:** 25 min
**Context:** Supabase Auth Python docs
**What to do:**
- Create src/api/auth.py with:
  POST /auth/signup, POST /auth/login, POST /auth/logout
- Create auth middleware: verify JWT token on protected routes
- Write tests:
  - Signup creates user in Supabase
  - Login returns JWT
  - Protected route rejects without token
  - Protected route accepts with valid token
**Done when:** Auth flow works end-to-end
**Commit:** `feat(auth): add Supabase Auth integration with JWT middleware`

### Task 5: Message Persistence + Generation Log Persistence
**Time:** 25 min (was 20 — added generation log wiring)
**Context:** Read docs/category-architecture.md Section 8 (messages table).
Read docs/model-resilience-intelligence.md Part 4.
**What to do:**
- Create src/api/messages.py with:
  GET /messages (list message history for entity)
  POST /messages/reaction (user reacts to message)
- Wire message generator output to persist in messages table
  - **Use explicit recipient_id** (from composition, not derived from entity)
  - **Store arc_id and life_context** if present on composition
- Wire delivery results to update message delivery_status
- **Wire R01's log_generation() to write to message_generation_log table**
  instead of local storage. Update the logging function to use Supabase.
- **Wire effectiveness back:** When user reacts (POST /messages/reaction),
  update BOTH the messages table AND the corresponding generation_log row
  with effectiveness_score, user_reaction, user_replied, reply_sentiment
- Write tests:
  - Messages persist after generation with foundation fields
  - Reaction updates BOTH message record AND generation log
  - History retrieves in correct order
  - Generation log row created for each generation
**Done when:** Messages AND generation logs persist, effectiveness flows back
**Commit:** `feat(api): add message persistence with intelligence logging`

### Task 6: Stripe Subscription Setup
**Time:** 25 min
**Context:** Stripe Python SDK docs, JimiGPT Architecture Section 9
**What to do:**
- Create src/api/payments.py with:
  POST /payments/checkout (creates Stripe Checkout session)
  POST /webhooks/stripe (handles subscription events)
- Handle events: checkout.session.completed, customer.subscription.updated,
  customer.subscription.deleted
- Update user_profiles.subscription_status on events
- Write tests (mock Stripe):
  - Checkout session creates correctly
  - Webhook updates subscription status
**Done when:** Subscription flow works with mocked Stripe
**Commit:** `feat(payments): add Stripe subscription integration`

---

## Task Summary

| # | Task | Time | Depends On |
|---|------|------|------------|
| 1 | Supabase client setup | 20 min | F01-F04, R01 |
| 2 | Database migration (+ generation log) | 30 min | Task 1 |
| 3 | Entity CRUD | 25 min | Task 2 |
| 4 | Supabase Auth | 25 min | Task 1 |
| 5 | Message persistence + gen log wiring | 25 min | Task 2 |
| 6 | Stripe subscriptions | 25 min | Task 4 |

**Total estimated time:** ~2.5 hours (6 reps, 2 daily sessions)

---

## Opus Review Tasks

- **T2: Database migration** — schema is expensive to change. Verify foundation
  columns, generation log table, and reserved table names.
- **T4: Supabase Auth** — security boundary.
- **T5: Message persistence + gen log** — the intelligence feedback loop. Verify
  effectiveness flows back to generation log correctly.
- **T6: Stripe webhooks** — financial correctness.
