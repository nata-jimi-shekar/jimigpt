# Codex Feature Review — F03: Delivery Layer (SMS, WhatsApp, Scheduling & Queue)
## Pre-Filled Brief — Ready to Paste to ChatGPT Codex

---

## Instructions for Codex

You are reviewing a completed feature for JimiGPT, an Emotional AI product
that creates Digital Twin companions for pets and sends contextual text
messages. This is a solo developer's codebase — your review is the "second
pair of eyes" that catches what the author missed.

**Your role:** Code quality reviewer. Focus on: correctness, test coverage,
integration risks, maintainability, and conformance to the documented
architecture. Be specific — cite files and functions. Don't nitpick style
(Ruff handles that) or type errors (mypy handles that).

**Important:** The architecture docs below are the source of truth. If code
deviates from docs, flag it as an issue. If you think the architecture is
wrong, note it separately — code should match docs as written.

---

## Project Overview

- **Product:** JimiGPT — sends personality-driven SMS and WhatsApp messages from
  a user's pet. Users create a Digital Twin of their living pet with a personality
  profile, and the system sends contextual messages throughout the day.
- **Stack:** Python 3.12+, FastAPI, Pydantic v2 (strict mode), pytest,
  Ruff, mypy --strict, Supabase, Twilio (SMS + WhatsApp), Anthropic Claude API
- **Key constraint:** All engine code must be entity-agnostic. Pet-specific
  logic lives in config/YAML only. The same engine must work for a future
  product (NeuroAmigo — neurodivergent social companion) with config changes.
- **Primary market:** Colombia (Pereira) — WhatsApp is the default messaging
  platform. SMS is secondary for US users.

## Feature Being Reviewed

- **Feature:** F03 — Delivery Layer (SMS, WhatsApp, Scheduling & Queue)
- **Tasks completed:** T1 through T7 (models, SMS client, scheduler, retry logic,
  webhook handler, WhatsApp channel + unified routing, integration test)
- **Architecture references:**
  - docs/category-architecture.md — Section 5, Stage 5 (Delivery)
  - docs/jimigpt-architecture.md — Section 5 (Quiet Hours, Frequency Limits)
  - docs/foundation-per-feature.md — F03 section (recipient_id, active_arcs)

## What This Feature Does

F03 builds the message delivery infrastructure that sits between the message
pipeline (F02) and the user's phone. It handles: scheduling messages at the
right time in the user's timezone, enforcing quiet hours (22:00-07:00 default),
sending messages via either SMS or WhatsApp through Twilio's API, retrying
failed deliveries with exponential backoff (3 attempts: 1min, 5min, 15min),
receiving delivery status callbacks from Twilio for both channels, and
providing a unified send interface that auto-selects the correct channel based
on the DeliveryRequest.

WhatsApp was added to Phase 1 because the developer's primary alpha testing
market (Colombia) uses WhatsApp as default. Both channels use the same Twilio
API surface — WhatsApp is SMS with a "whatsapp:" prefix on phone numbers.

The delivery layer is channel-agnostic by design. Adding a new channel means
adding one function to the router and one case to the match statement. The
scheduler, retry logic, and webhook handler work identically across channels.

## Files Created/Modified in This Feature

### Source Files
```
src/delivery/__init__.py
src/delivery/models.py           — DeliveryChannel enum, DeliveryRequest, DeliveryResult
src/delivery/sms.py              — send_sms(), send_whatsapp(), send_message() router,
                                   deliver_with_retry() with channel auto-selection
src/delivery/scheduler.py        — schedule_delivery(), get_pending_deliveries(),
                                   QuietHours model, DeliveryQueue (in-memory Phase 1)
src/api/webhooks.py              — POST /api/v1/webhooks/twilio endpoint,
                                   channel detection from From field, status store
src/shared/config.py             — Settings class with Twilio SMS + WhatsApp env vars
```

### Test Files
```
tests/delivery/__init__.py
tests/delivery/test_models.py         — Model validation, foundation fields
tests/delivery/test_sms.py            — SMS send, Twilio mocking, phone validation, Settings
tests/delivery/test_whatsapp.py       — WhatsApp send, prefix verification, channel routing,
                                        deliver_with_retry auto-selection, Settings
tests/delivery/test_scheduler.py      — Timezone conversion, quiet hours, pending retrieval,
                                        multi-recipient, foundation fields
tests/delivery/test_retry.py          — Exponential backoff, attempt tracking, all-fail,
                                        partial success, last_attempt_at
tests/delivery/test_integration.py    — Full flow for both SMS and WhatsApp:
                                        schedule → queue → deliver → webhook → status
```

## Specific Review Focus Areas

### 1. Correctness & Logic — Delivery Timing

This feature handles WHEN messages arrive on someone's phone. Timing bugs
are trust violations — a message at 3am or during a work meeting damages
the product's emotional value.

- **Quiet hours enforcement:** Can a message EVER be delivered during quiet
  hours? Trace all code paths through schedule_delivery(). Is the quiet-hours
  check done in local time (correct) or UTC (incorrect)?
- **Timezone handling:** Does the conversion from local naive datetime to UTC
  work correctly? Test with edge cases: UTC+14 (Line Islands), UTC-12 (Baker
  Island), DST transitions. Colombia is UTC-5 with no DST — is that handled?
- **Deferral logic:** When a message is deferred from 23:00 to 07:00 next day,
  is the date correctly advanced? What about month/year boundaries?
- **Pending retrieval:** Does get_pending_deliveries correctly compare
  timezone-aware and timezone-naive datetimes?

### 2. Correctness & Logic — Channel Routing

- **WhatsApp prefix:** Does send_whatsapp() correctly prefix BOTH the `to` and
  `from_` numbers with "whatsapp:"? What happens if the number already has
  the prefix?
- **deliver_with_retry channel auto-selection:** When _send_fn is None, does
  the lambda correctly capture request.channel? Is there a late-binding
  closure issue?
- **send_message router:** Does the match statement handle all DeliveryChannel
  values? What about VOICE and PUSH — do they raise ValueError as expected?
- **Backward compatibility:** Do all existing SMS tests pass unchanged after
  the WhatsApp refactor? The _send_fn parameter changed from default=send_sms
  to default=None — verify no existing test broke.

### 3. Correctness & Logic — Retry

- **Exponential backoff:** Are the delays correct (60s, 300s, 900s)?
  Is there a sleep after the LAST failed attempt (there shouldn't be)?
- **Attempt counting:** Does result.attempts accurately reflect the number
  of attempts made? Is last_attempt_at set on every attempt?
- **Permanent failure:** After 3 failed attempts, is the result correctly
  marked as failed? Does the error from the LAST attempt surface?

### 4. Correctness & Logic — Webhook

- **Channel detection:** Does _detect_channel correctly identify WhatsApp
  from the From field ("whatsapp:" prefix)? What about edge cases — empty
  From, None From, malformed From?
- **Signature verification:** Is the Twilio signature validation implemented
  correctly? Can it be bypassed by a malicious actor?
- **Status recording:** Does the in-memory store handle concurrent updates?
  (Phase 1 is single-process, but worth noting for F05 database migration.)
- **HTTP response:** Does the endpoint always return 200? (Twilio retries on
  non-200, which would cause duplicate status updates.)

### 5. Test Coverage

- Does every public function have at least one test?
- Are failure modes tested? (Twilio errors, network timeouts, invalid numbers)
- Are edge cases covered? (Empty phone, empty body, midnight deferral,
  month boundary, DST transition)
- Are both channels tested in integration? (SMS and WhatsApp full flows)
- Is the foundation field (active_arcs on scheduler) tested with None and
  with a non-None list?
- Is the foundation field (recipient_id) tested as required and different
  from entity_id?

### 6. Architecture Conformance

- Is entity-agnostic vs. pet-specific properly separated? (Delivery layer
  should have NO pet references — it's a generic message delivery system)
- Are Pydantic models used for all data? (DeliveryRequest, DeliveryResult,
  QuietHours — check for any raw dicts)
- Are functions under 30 lines?
- Is the DeliveryQueue an in-memory implementation that can be swapped for
  database-backed in F05 without changing the scheduler interface?
- Does the webhook handler follow FastAPI dependency injection patterns
  (verify_twilio_signature as a Depends)?

### 7. Integration Points

- **F02 → F03:** Does DeliveryRequest correctly wrap GeneratedMessage?
  Can F09 (batch runner) use schedule_delivery and deliver_with_retry
  without knowing about SMS/WhatsApp internals?
- **F03 → F05:** When the in-memory DeliveryQueue is replaced with a database
  table, what needs to change? Is the interface clean enough?
- **F03 → F04:** Trust stage doesn't directly affect delivery, but escalation
  (F04) might need to pause delivery. Is there a hook for that?
- **Config:** Is Settings properly centralized? Are all env vars documented
  in .env.example?

### 8. Security

- **Twilio webhook signature:** Is the validation using RequestValidator
  correctly? Is the URL reconstruction reliable (request.url)?
- **Phone number validation:** Is the E.164 regex robust enough? Could
  a malformed number crash Twilio or leak information?
- **Auth token exposure:** Is the Twilio auth token only read from env vars,
  never logged or included in error messages?

## Known Decisions (Don't Flag These)

- **In-memory DeliveryQueue:** This is deliberate for Phase 1. Supabase-backed
  queue comes in F05. The interface is designed for easy swap.
- **In-memory webhook status store:** Same — replaced by DB in F05.
- **sms.py contains WhatsApp code:** The file is named sms.py historically but
  now contains both send_sms() and send_whatsapp(). A rename to twilio_client.py
  was considered but deferred to avoid import changes across all test files.
  If you flag this, note it as "Fix Later" not "Fix Now."
- **No channel-default-by-country-code:** The scheduler doesn't automatically
  pick WhatsApp for Colombian numbers. Channel selection is explicit on
  DeliveryRequest. Automatic selection is a Phase 2 UX feature.
- **active_arcs parameter ignored:** Foundation field for Phase 2 arc-aware
  scheduling. Accepted but unused in Phase 1. This is intentional.
- **Functional style:** Minimal classes. Pydantic models for data, plain
  functions for logic. This is the project's style convention.

## Output Format

Structure your review as:

### Critical Issues (Fix Now)
Bugs, incorrect logic, missing validation, security issues, broken
integration points. Each with: file, function, issue, impact, suggested fix.

### Important Issues (Fix Later)
Test gaps, missing edge cases, suboptimal patterns, minor architecture drift.
Non-blocking but should be addressed before MVP.

### Observations
Things that aren't issues but worth noting — patterns forming, potential
future problems, suggestions for improvement.

### Strengths
What's working well. Good patterns to continue.

### Summary
2-3 sentence overall assessment of the feature's code quality.
