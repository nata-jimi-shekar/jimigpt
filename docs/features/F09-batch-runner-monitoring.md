# F09: Batch Runner, Scheduler & Monitoring

**Phase:** 1D  
**Priority:** 9  
**Architecture Reference:** Category Architecture Section 5 (Batch Pre-Generation)  
**JimiGPT Reference:** JimiGPT Architecture Section 5 (Trigger Configuration)  

## Feature Description

Wire the batch pre-generation pipeline to actually run on a schedule, connect
the delivery scheduler to the delivery queue, and add basic monitoring so you
know the system is working (or when it isn't).

This is the operational glue that makes JimiGPT a living, breathing product.

## Dependencies
- F01-F06 (all engine + database code)

## What "Done" Looks Like
- Nightly batch job generates next day's messages for all users
- Scheduler reads delivery queue and sends messages at correct times
- Basic monitoring: logs, error alerts, daily summary
- System runs unattended — you don't need to manually trigger anything
- All tests pass

---

## Micro-Tasks

### Task 1: Wire Batch Job to Database
**Time:** 25 min  
**Context:** F02 Task 10 (Batch skeleton), F05 (Database)  
**What to do:**
- Complete the batch.py skeleton with real database calls
- Load active users from user_profiles where product='jimigpt'
- Load entity profiles for each user
- Evaluate triggers for tomorrow
- Generate and quality-check messages
- Insert passing messages into delivery_queue
- Write integration test with test database  
**Done when:** Batch job generates messages and queues them  
**Commit:** `feat(messaging): wire batch generation to database`

### Task 2: APScheduler Setup
**Time:** 20 min  
**Context:** APScheduler documentation  
**What to do:**
- Add APScheduler to FastAPI app lifecycle
- Schedule nightly batch: 2:00 AM UTC daily
- Schedule delivery checker: every 5 minutes
- Schedule trust evaluation: daily at midnight
- Write startup/shutdown hooks for clean scheduler management  
**Done when:** Scheduler starts with app, jobs configured  
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
- Write tests:
  - Pending messages sent at correct time
  - Failed messages retry
  - Already-sent messages not re-sent  
**Done when:** Queue processor delivers messages reliably  
**Commit:** `feat(delivery): add delivery queue processor`

### Task 4: Basic Monitoring & Logging
**Time:** 20 min  
**Context:** Standard Python logging, Sentry SDK  
**What to do:**
- Configure structured logging (JSON format for production)
- Log: messages generated, delivered, failed, quality gate rejections
- Add Sentry SDK for error tracking (optional, configurable)
- Create daily summary function: messages sent today, failures, new users
- Log summary at end of each batch run  
**Done when:** System produces useful operational logs  
**Commit:** `feat(monitoring): add structured logging and daily summary`

### Task 5: Health & Status Endpoints
**Time:** 20 min  
**Context:** Standard API health check patterns  
**What to do:**
- Enhance GET /health with system status:
  - Database connectivity
  - Last batch run time and result
  - Messages queued for today
  - Active user count
- Add GET /api/v1/status (authenticated, admin only)
  with detailed operational metrics
- Write tests  
**Done when:** Health endpoints report system status accurately  
**Commit:** `feat(api): add system health and status endpoints`

---

## Task Summary

| # | Task | Time | Depends On |
|---|------|------|------------|
| 1 | Wire batch to database | 25 min | F02, F05 |
| 2 | APScheduler setup | 20 min | Task 1 |
| 3 | Delivery queue processor | 25 min | Task 2, F03 |
| 4 | Monitoring & logging | 20 min | Task 1 |
| 5 | Health & status endpoints | 20 min | Tasks 1-4 |

**Total estimated time:** ~2 hours (5 reps, 1-2 daily sessions)
