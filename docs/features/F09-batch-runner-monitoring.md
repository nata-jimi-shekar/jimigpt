# F09: Batch Runner, Scheduler & Monitoring

**Phase:** 1D
**Priority:** 9
**Architecture Reference:** Category Architecture Section 5 (Batch Pre-Generation)
**JimiGPT Reference:** JimiGPT Architecture Section 5 (Trigger Configuration)
**Additional Reference:** docs/model-resilience-intelligence.md (provider telemetry, fingerprinting)

## Feature Description

Wire the batch pre-generation pipeline to actually run on a schedule, connect
the delivery scheduler to the delivery queue, and add monitoring including
LLM provider health, cost tracking, and personality drift detection.

This is the operational glue that makes JimiGPT a living, breathing product.

## Dependencies
- F01-F06, R01 (all engine + database + LLM abstraction code)

## What "Done" Looks Like
- Nightly batch job generates next day's messages for all users
- Scheduler reads delivery queue and sends messages at correct times
- **LLM provider health monitored (latency, error rate, cost)**
- **Daily cost summary logged**
- **Personality fingerprint baseline established for all 8 archetypes**
- Basic monitoring: logs, error alerts, daily summary
- System runs unattended
- All tests pass

---

## Micro-Tasks

### Task 1: Wire Batch Job to Database
**Time:** 25 min
**Context:** F02 (pipeline), F05 (database), R01 (provider abstraction)
**What to do:**
- Complete the batch.py with real database calls
- Load active users from user_profiles where product='jimigpt'
- Load entity profiles for each user
- Evaluate triggers for tomorrow
- Generate and quality-check messages **using provider factory from R01**
  (not direct Anthropic calls)
- **Each generation creates a generation_log record via log_generation()**
- Insert passing messages into delivery_queue
- Write integration test with test database
**Done when:** Batch job generates messages through provider abstraction and logs them
**Commit:** `feat(messaging): wire batch generation to database with provider abstraction`

### Task 2: APScheduler Setup
**Time:** 20 min
**Context:** APScheduler documentation
**What to do:**
- Add APScheduler to FastAPI app lifecycle
- Schedule nightly batch: 2:00 AM UTC daily
- Schedule delivery checker: every 5 minutes
- Schedule trust evaluation: daily at midnight
- **Schedule daily cost summary: 23:00 UTC**
- Write startup/shutdown hooks for clean scheduler management
**Done when:** Scheduler starts with app, all jobs configured
**Commit:** `feat(scheduler): add APScheduler with job configuration`

### Task 3: Delivery Queue Processor
**Time:** 25 min
**Context:** F03 (Delivery Layer), Category Architecture Section 5
**What to do:**
- Create process_delivery_queue() function
- Runs every 5 minutes via scheduler
- Queries delivery_queue for pending messages where scheduled_at <= now
- Sends each via appropriate channel (SMS for now)
- Updates status to 'sent' or 'failed'
- Handles retry logic for failures
- Write tests
**Done when:** Queue processor delivers messages reliably
**Commit:** `feat(delivery): add delivery queue processor`

### Task 4: Provider Health & Cost Monitoring
**Time:** 25 min
**Context:** docs/model-resilience-intelligence.md Part 1 (telemetry)
**What to do:**
- Create src/shared/provider_health.py with:
  - daily_cost_summary(): query generation_log for today's costs grouped
    by provider and model. Log as structured JSON.
  - provider_health_check(): for each configured provider, make a minimal
    test call (generate one short message). Record latency and success.
  - ProviderHealthReport model: provider, status, latency_ms, error_rate_24h,
    cost_24h, messages_generated_24h
- Wire daily_cost_summary to the 23:00 UTC scheduled job
- Add provider health to GET /health endpoint (from existing health check)
- Write tests:
  - Cost summary aggregates correctly from mock log data
  - Health check detects down provider
  - Health report model validates
**Done when:** Cost and health monitoring operational
**Commit:** `feat(monitoring): add provider health and cost monitoring`

### Task 5: Personality Fingerprint Baseline
**Time:** 25 min
**Context:** R01-T8 (fingerprint models), docs/model-resilience-intelligence.md Part 2
**What to do:**
- Create scripts/run_fingerprint.py:
  - Loads all 8 archetype configs
  - For each, generates 5 test messages using the current primary model
    (via provider factory)
  - Extracts PersonalityFingerprint for each archetype
  - Stores as JSON baseline: config/fingerprint_baselines.json
  - Compares with previous baseline if it exists → DriftDetection
  - Prints drift report
- This script is run manually after initial deployment, and can be
  scheduled weekly in Phase 2
- Write test: script produces valid fingerprints for all 8 archetypes
**Done when:** Baseline fingerprints established for all archetypes
**Commit:** `feat(monitoring): add personality fingerprint baseline generation`

### Task 6: Health & Status Endpoints
**Time:** 20 min
**Context:** Standard API health check patterns
**What to do:**
- Enhance GET /health with system status:
  - Database connectivity
  - Last batch run time and result
  - Messages queued for today
  - Active user count
  - **Primary LLM provider status (from provider health)**
  - **Today's generation cost**
- Add GET /api/v1/status (authenticated, admin only)
  with detailed operational metrics
- Write tests
**Done when:** Health endpoints report full system status including provider health
**Commit:** `feat(api): add system health and status endpoints with provider telemetry`

---

## Task Summary

| # | Task | Time | Depends On |
|---|------|------|------------|
| 1 | Wire batch to database | 25 min | F02, F05, R01 |
| 2 | APScheduler setup | 20 min | Task 1 |
| 3 | Delivery queue processor | 25 min | Task 2, F03 |
| 4 | Provider health & cost monitoring | 25 min | Task 1, R01 |
| 5 | Personality fingerprint baseline | 25 min | R01-T8 |
| 6 | Health & status endpoints | 20 min | Tasks 1-5 |

**Total estimated time:** ~2.5 hours (6 reps, 2 daily sessions)
