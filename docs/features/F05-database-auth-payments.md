# F05: Database, Auth & Payments

**Phase:** 1C  
**Priority:** 5  
**Architecture Reference:** Category Architecture Sections 8, 9  
**JimiGPT Reference:** JimiGPT Architecture Section 9  

## Feature Description

Set up Supabase database with all shared tables, authentication via Supabase Auth,
and Stripe payment integration for subscriptions. This connects all the backend
engines to persistent storage and user management.

## Dependencies
- F01, F02, F03, F04 (all engine code — this wires them to the database)

## What "Done" Looks Like
- All database tables created in Supabase
- User signup/login works via Supabase Auth
- Entity CRUD operations work (create, read, update, delete)
- Message history persists to database
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

### Task 2: Database Migration — Core Tables
**Time:** 25 min  
**Context:** Read docs/category-architecture.md Section 8 (full SQL schema)  
**What to do:**
- Create scripts/migrate.sql with all shared tables:
  user_profiles, entities, messages, delivery_queue,
  trust_events, archetype_configs, recipient_preferences
- Create scripts/seed.py that loads archetype configs into archetype_configs table
- Document: run migration via Supabase dashboard SQL editor (for now)
- Write a simple test that verifies table schemas match expected structure  
**Done when:** SQL script creates all tables  
**Commit:** `feat(database): add core database migration script`

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

### Task 5: Message Persistence
**Time:** 20 min  
**Context:** Read docs/category-architecture.md Section 8 (messages table)  
**What to do:**
- Create src/api/messages.py with:
  GET /messages (list message history for entity)
  POST /messages/reaction (user reacts to message)
- Wire message generator output to persist in messages table
- Wire delivery results to update message delivery_status
- Write tests:
  - Messages persist after generation
  - Reaction updates message record
  - History retrieves in correct order  
**Done when:** Messages persist and retrieve correctly  
**Commit:** `feat(api): add message persistence and history`

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
| 1 | Supabase client setup | 20 min | F01-F04 |
| 2 | Database migration | 25 min | Task 1 |
| 3 | Entity CRUD | 25 min | Task 2 |
| 4 | Supabase Auth | 25 min | Task 1 |
| 5 | Message persistence | 20 min | Task 2 |
| 6 | Stripe subscriptions | 25 min | Task 4 |

**Total estimated time:** ~2.5 hours (6 reps, 2 daily sessions)
