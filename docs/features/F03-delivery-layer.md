# F03: Delivery Layer — SMS, Scheduling & Queue

**Phase:** 1B  
**Priority:** 3  
**Architecture Reference:** Category Architecture Section 5, Stage 5  
**JimiGPT Reference:** JimiGPT Architecture Section 5  

## Feature Description

Build the message delivery infrastructure: Twilio SMS integration, timezone-aware
scheduling, delivery queue management, retry logic, and the scheduler that pulls
from the queue and sends messages at the right time.

## Dependencies
- F02 (Message Pipeline) must be complete

## What "Done" Looks Like
- SMS messages deliver via Twilio
- Messages send at scheduled times in user's timezone
- Failed deliveries retry with exponential backoff (3 attempts)
- Quiet hours enforced at delivery level (defense in depth)
- Twilio webhooks update delivery status
- All tests pass

---

## Micro-Tasks

### Task 1: Delivery Models
**Time:** 15 min  
**Context:** Read docs/category-architecture.md Section 5, Stage 5  
**What to do:**
- Create src/delivery/__init__.py
- Create src/delivery/models.py with:
  DeliveryChannel enum, DeliveryRequest model, DeliveryResult model
- Write tests/delivery/test_models.py  
**Done when:** Models validate, tests pass  
**Commit:** `feat(delivery): add delivery request and result models`

### Task 2: Twilio SMS Client
**Time:** 25 min  
**Context:** Twilio Python SDK docs (https://www.twilio.com/docs/sms/quickstart/python)  
**What to do:**
- Create src/delivery/sms.py with:
  send_sms(to: str, body: str) -> DeliveryResult
  Wraps Twilio client, handles errors, returns DeliveryResult
- Create src/shared/config.py with Settings class (reads env vars via pydantic-settings)
- Write tests (mock Twilio client):
  - Successful send returns success result with SID
  - Twilio error returns failure result with error message
  - Phone number validation  
**Done when:** SMS sending works with mocked Twilio  
**Commit:** `feat(delivery): add Twilio SMS integration`

### Task 3: Delivery Scheduler
**Time:** 25 min  
**Context:** Read docs/jimigpt-architecture.md Section 5 (Quiet Hours, Frequency Limits)  
**What to do:**
- Create src/delivery/scheduler.py with:
  schedule_delivery(message, channel, scheduled_time, timezone) -> DeliveryRequest
  get_pending_deliveries(current_time) -> list[DeliveryRequest]
- Enforces quiet hours at delivery level (22:00-07:00 default)
- Handles timezone conversion
- Write tests:
  - Delivery scheduled at correct UTC time for timezone
  - Delivery blocked during quiet hours
  - Pending deliveries retrieved correctly  
**Done when:** Scheduling logic works correctly across timezones  
**Commit:** `feat(delivery): add delivery scheduler with timezone support`

### Task 4: Retry Logic
**Time:** 20 min  
**Context:** Standard exponential backoff pattern  
**What to do:**
- Add retry logic to delivery: 3 attempts, exponential backoff (1min, 5min, 15min)
- Add to sms.py: deliver_with_retry(request) -> DeliveryResult
- Track attempts and last_attempt_at on delivery queue
- Write tests:
  - First attempt succeeds → no retry
  - First attempt fails, second succeeds → 1 retry
  - All 3 attempts fail → marked as permanently failed  
**Done when:** Retry logic works correctly  
**Commit:** `feat(delivery): add retry logic with exponential backoff`

### Task 5: Twilio Webhook Handler
**Time:** 20 min  
**Context:** Twilio status callback documentation  
**What to do:**
- Create src/api/webhooks.py with POST /api/v1/webhooks/twilio endpoint
- Handles delivery status updates (delivered, failed, undelivered)
- Updates delivery queue status
- Write tests:
  - Webhook updates delivery status correctly
  - Invalid webhook signature rejected
  - Unknown message ID handled gracefully  
**Done when:** Webhook updates delivery status  
**Commit:** `feat(delivery): add Twilio webhook handler`

### Task 6: Delivery Integration Test
**Time:** 20 min  
**Context:** All previous tasks  
**What to do:**
- Create tests/delivery/test_integration.py
- Test: GeneratedMessage → DeliveryRequest → SMS send (mocked) → status update
- Verify full delivery flow from queued message to confirmed delivery  
**Done when:** End-to-end delivery flow works  
**Commit:** `test(delivery): add delivery integration test`

---

## Task Summary

| # | Task | Time | Depends On |
|---|------|------|------------|
| 1 | Delivery models | 15 min | F02 complete |
| 2 | Twilio SMS client | 25 min | Task 1 |
| 3 | Delivery scheduler | 25 min | Task 1 |
| 4 | Retry logic | 20 min | Task 2 |
| 5 | Twilio webhook handler | 20 min | Task 2 |
| 6 | Integration test | 20 min | All above |

**Total estimated time:** ~2 hours (5 reps, 1-2 daily sessions)
