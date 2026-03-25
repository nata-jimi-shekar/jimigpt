# F03: Delivery Layer — SMS, WhatsApp, Scheduling & Queue

**Phase:** 1B
**Priority:** 3
**Architecture Reference:** Category Architecture Section 5, Stage 5
**JimiGPT Reference:** JimiGPT Architecture Section 5
**Foundation Reference:** docs/foundation-per-feature.md (F03 section)

## Feature Description

Build the message delivery infrastructure: Twilio SMS and WhatsApp integration,
timezone-aware scheduling, delivery queue management, retry logic, and the
scheduler that pulls from the queue and sends messages at the right time.

**WhatsApp included in Phase 1** because the primary alpha testing market
(Pereira, Colombia) uses WhatsApp as the default messaging platform. SMS-only
would exclude most potential local testers. Both channels use the same Twilio
API surface — WhatsApp is essentially SMS with a different `from_` prefix.

## Dependencies
- F02 (Message Pipeline) must be complete
- R01 (LLM Abstraction) should be complete (not blocking, but preferred)

## What "Done" Looks Like
- SMS messages deliver via Twilio
- **WhatsApp messages deliver via Twilio WhatsApp API**
- Messages send at scheduled times in user's timezone
- Failed deliveries retry with exponential backoff (3 attempts)
- Quiet hours enforced at delivery level (defense in depth)
- Twilio webhooks update delivery status (both SMS and WhatsApp)
- **Channel selection based on user preference (stored on user profile)**
- All tests pass

---

## Micro-Tasks

### Task 1: Delivery Models ✅
**Time:** 20 min
**Status:** COMPLETE
**Commit:** `feat(delivery): add delivery models with SMS and WhatsApp channels`

### Task 2: Twilio SMS Client ✅
**Time:** 25 min
**Status:** COMPLETE — Built as sms.py with send_sms() and injectable _send_fn on deliver_with_retry()
**Commit:** `feat(delivery): add Twilio SMS integration`

### Task 3: Delivery Scheduler ✅
**Time:** 30 min
**Status:** COMPLETE — Includes quiet hours, timezone support, active_arcs foundation, recipient_id
**Commit:** `feat(delivery): add delivery scheduler with timezone and channel support`

### Task 4: Retry Logic ✅
**Time:** 20 min
**Status:** COMPLETE — deliver_with_retry() with injectable _send_fn and _sleep_fn
**Commit:** `feat(delivery): add retry logic with exponential backoff`

### Task 5: Twilio Webhook Handler
**Time:** 25 min
**Context:** Twilio status callback documentation
**What to do:**
- Create src/api/webhooks.py with POST /api/v1/webhooks/twilio endpoint
- Handles delivery status updates (delivered, failed, undelivered)
- Works for BOTH SMS and WhatsApp status callbacks (same Twilio webhook format)
- Updates delivery queue status
- Detects channel from the `From` field in webhook payload
  (WhatsApp callbacks include "whatsapp:" prefix)
- Write tests:
  - SMS webhook updates delivery status correctly
  - WhatsApp webhook updates delivery status correctly
  - Invalid webhook signature rejected
  - Unknown message ID handled gracefully
**Done when:** Webhook handles both SMS and WhatsApp status updates
**Commit:** `feat(delivery): add Twilio webhook handler for SMS and WhatsApp`

### Task 6: WhatsApp Channel + Unified Send Interface
**Time:** 20 min
**Context:** Read the existing src/delivery/sms.py. This task extends it
with WhatsApp support and a channel-routing function. The existing code
already has the right abstractions (injectable _send_fn on deliver_with_retry),
so this is a small additive change, not a rewrite.

**What to do:**

**Step 1: Add TWILIO_WHATSAPP_FROM to Settings (src/shared/config.py)**
- Add one new field to the Settings class:
  ```python
  twilio_whatsapp_from: str = ""  # e.g. "+14155238886"
  ```
- Add to .env.example:
  ```
  TWILIO_WHATSAPP_FROM=+14155238886
  ```

**Step 2: Add send_whatsapp() to sms.py**
- Add a new function directly below send_sms(). It follows the SAME pattern —
  same validation, same try/except, same DeliveryResult return. The only
  differences are:
  - `to` gets prefixed: `f"whatsapp:{to}"`
  - `from_` uses `_settings.twilio_whatsapp_from` prefixed: `f"whatsapp:{_settings.twilio_whatsapp_from}"`
  - Returns `channel=DeliveryChannel.WHATSAPP` instead of SMS
  ```python
  def send_whatsapp(to: str, body: str) -> DeliveryResult:
      """Send a WhatsApp message via Twilio.

      Same Twilio API as SMS — only the 'whatsapp:' prefix on
      to/from numbers differs.
      """
      if not to or not _E164_RE.match(to):
          raise ValueError(f"Invalid phone number: {to!r}. Must be E.164 format.")
      if not body:
          raise ValueError("Message body must not be empty.")

      try:
          client = _twilio_client()
          message = client.messages.create(
              to=f"whatsapp:{to}",
              from_=f"whatsapp:{_settings.twilio_whatsapp_from}",
              body=body,
          )
          return DeliveryResult(
              success=True,
              channel=DeliveryChannel.WHATSAPP,
              delivered_at=datetime.now(tz=UTC),
              external_id=message.sid,
              error=None,
          )
      except TwilioRestException as exc:
          return DeliveryResult(
              success=False,
              channel=DeliveryChannel.WHATSAPP,
              delivered_at=None,
              external_id=None,
              error=str(exc),
          )
      except Exception as exc:  # noqa: BLE001
          return DeliveryResult(
              success=False,
              channel=DeliveryChannel.WHATSAPP,
              delivered_at=None,
              external_id=None,
              error=f"Unexpected error: {exc}",
          )
  ```

**Step 3: Add send_message() channel router to sms.py**
- Add a unified entry point that routes by channel:
  ```python
  def send_message(to: str, body: str, channel: DeliveryChannel) -> DeliveryResult:
      """Route a message to the correct channel sender."""
      match channel:
          case DeliveryChannel.SMS:
              return send_sms(to, body)
          case DeliveryChannel.WHATSAPP:
              return send_whatsapp(to, body)
          case _:
              raise ValueError(f"Unsupported delivery channel: {channel}")
  ```

**Step 4: Update deliver_with_retry() default _send_fn**
- Change the default `_send_fn` to be channel-aware. The current signature is:
  ```python
  def deliver_with_retry(
      request: DeliveryRequest,
      *,
      _send_fn: _SendFn = send_sms,  # ← currently hardcoded to SMS
      _sleep_fn: _SleepFn = _time.sleep,
  ) -> DeliveryResult:
  ```
- Update to use the request's channel:
  ```python
  def deliver_with_retry(
      request: DeliveryRequest,
      *,
      _send_fn: _SendFn | None = None,  # None = auto-select by channel
      _sleep_fn: _SleepFn = _time.sleep,
  ) -> DeliveryResult:
      phone = request.recipient_phone
      if not phone:
          raise ValueError("DeliveryRequest.recipient_phone is required.")

      # Auto-select sender by channel if no override provided
      if _send_fn is None:
          _send_fn = lambda to, body: send_message(to, body, request.channel)

      # ... rest of function unchanged ...
  ```
- **CRITICAL:** Existing tests that inject `_send_fn=mock_fn` continue to
  work unchanged because they explicitly provide the parameter. Only the
  DEFAULT behavior changes (from always-SMS to channel-aware).

**Step 5: Write tests**
- Add to tests/delivery/test_sms.py (or create test_whatsapp.py):
  - `test_send_whatsapp_success`: mock Twilio, verify "whatsapp:" prefix
    on both `to` and `from_`, verify DeliveryResult.channel == WHATSAPP
  - `test_send_whatsapp_prefixes_numbers`: verify the actual strings
    passed to `client.messages.create()` have the "whatsapp:" prefix
  - `test_send_whatsapp_twilio_error`: same as SMS error test but for WhatsApp
  - `test_send_whatsapp_invalid_phone`: same validation as SMS
  - `test_send_message_routes_sms`: send_message(channel=SMS) calls send_sms
  - `test_send_message_routes_whatsapp`: send_message(channel=WHATSAPP) calls send_whatsapp
  - `test_send_message_unsupported_channel`: raises ValueError for VOICE/PUSH
  - `test_deliver_with_retry_uses_channel`: create request with channel=WHATSAPP,
    call deliver_with_retry() with NO explicit _send_fn, verify WhatsApp was used
  - **Verify ALL existing SMS tests still pass unchanged**

**Done when:**
- send_whatsapp() works with mocked Twilio
- send_message() routes correctly by channel
- deliver_with_retry() auto-selects channel when _send_fn not provided
- All existing SMS tests pass without modification
- New WhatsApp tests pass

**Commit:** `feat(delivery): add WhatsApp support and unified channel routing`

### Task 7: Delivery Integration Test
**Time:** 25 min
**Context:** All previous tasks
**What to do:**
- Create tests/delivery/test_integration.py
- Test full flow for BOTH channels:
  - GeneratedMessage → DeliveryRequest(channel=SMS) → deliver_with_retry (mocked) → status update
  - GeneratedMessage → DeliveryRequest(channel=WHATSAPP) → deliver_with_retry (mocked) → status update
- Verify channel routing: deliver_with_retry picks correct sender based on request.channel
- Verify full delivery flow from queued message to confirmed delivery
**Done when:** End-to-end delivery flow works for both SMS and WhatsApp
**Commit:** `test(delivery): add delivery integration test for SMS and WhatsApp`

---

## Task Summary

| # | Task | Time | Depends On | Status |
|---|------|------|------------|--------|
| 1 | Delivery models | 20 min | F02 complete | ✅ Done |
| 2 | Twilio SMS client | 25 min | Task 1 | ✅ Done |
| 3 | Delivery scheduler | 30 min | Task 1 | ✅ Done |
| 4 | Retry logic | 20 min | Task 2 | ✅ Done |
| 5 | Twilio webhook handler | 25 min | Task 2 | Next |
| 6 | WhatsApp channel + unified send | 20 min | Tasks 2, 4 | After T5 |
| 7 | Integration test | 25 min | All above | Last |

**Total estimated time:** ~2.75 hours (7 reps, 2-3 daily sessions)

---

## Notes

**Why WhatsApp is a small addition, not a separate feature:**
The existing sms.py already has the right abstractions. deliver_with_retry()
accepts an injectable _send_fn. DeliveryChannel.WHATSAPP already exists in
the enum. DeliveryRequest already carries channel. The only new code is
send_whatsapp() (near-copy of send_sms with "whatsapp:" prefix) and
send_message() (5-line router). Existing tests don't break because they
inject their own _send_fn.

**WhatsApp sandbox for development:**
Twilio provides a WhatsApp sandbox for development/testing that doesn't
require Meta business verification. You can test with your own phone
immediately. Production WhatsApp requires a Twilio-approved sender, which
Twilio handles (no direct Meta application needed).

**Env vars needed (add to .env.example):**
```
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_SMS_FROM=+1234567890
TWILIO_WHATSAPP_FROM=+14155238886
```
