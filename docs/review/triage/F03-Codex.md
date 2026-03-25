# Codex Feature-Level Triage — F03: Delivery Layer

**Date:** 2026-03-25
**Reviewer:** ChatGPT Codex
**Feature reviewed:** F03 — Delivery Layer (SMS, WhatsApp, Scheduling & Queue)
**Tasks covered:** T1 through T7
**Files reviewed:**
- src/delivery/models.py
- src/delivery/sms.py
- src/delivery/scheduler.py
- src/api/webhooks.py
- src/shared/config.py
- tests/delivery/test_models.py
- tests/delivery/test_sms.py
- tests/delivery/test_whatsapp.py
- tests/delivery/test_scheduler.py
- tests/delivery/test_retry.py
- tests/delivery/test_integration.py

---

### Critical Issues (Fix Now)
| # | File | Function | Issue | Impact | Fix Direction | Status |
|---|------|----------|-------|--------|---------------|--------|
| 1 | src/delivery/scheduler.py:61 | `DeliveryQueue.pending()` / `get_pending_deliveries()` | Due items are returned repeatedly and are never removed or marked delivered/failed. I verified the current behavior by scheduling one item and calling `get_pending_deliveries()` twice; both calls returned the same request. This also conflicts with the architecture’s queue model, which includes a delivery status lifecycle (`pending` / `sent` / `failed` / `cancelled`) in `docs/category-architecture.md:719-727`. | Any polling runner can redeliver the same message on every sweep, causing duplicate SMS/WhatsApp sends and trust damage. F09 cannot safely consume this queue as written. | Add queue state transitions now: either dequeue on claim or add explicit `mark_sent` / `mark_failed` semantics and have `pending()` return only unclaimed items. Add a regression test that calling `get_pending_deliveries()` twice does not surface already-claimed work. | [x] Done |
| 2 | src/delivery/scheduler.py:67 | `_to_utc()` | Timezone localization is done via `local_naive.replace(tzinfo=tz)`, which silently accepts nonexistent and ambiguous local times. Example: `2026-03-08 02:30` in `America/New_York` is a nonexistent DST time, but current code still converts it to UTC instead of rejecting or normalizing it. | Timing bugs around DST will schedule impossible local times and can send at the wrong real-world hour. This is exactly the kind of “message at the wrong time” trust break the brief warns about. | Replace naive `replace()` localization with explicit DST-safe handling. At minimum, detect nonexistent/ambiguous local times and either reject them or normalize by policy, then add tests for spring-forward and fall-back transitions. | [x] Done |

### Important Issues (Fix Later)
| # | File | Issue | Impact | Priority |
|---|------|-------|--------|----------|
| 1 | src/delivery/sms.py:85 | `send_whatsapp()` always prepends `whatsapp:` to both numbers and does not handle already-prefixed inputs. If a caller passes `whatsapp:+573001234567`, Twilio will receive `whatsapp:whatsapp:+573001234567`. | Preventable delivery failure on a public API surface that is supposed to be channel-agnostic. | High |
| 2 | src/api/webhooks.py:79 | The endpoint comment says it “always returns 200”, but signature validation can return `403`, and a missing `X-Twilio-Signature` header yields `422` before the handler runs. Integration tests bypass the dependency entirely, so this path is untested. | Twilio callback retries and duplicate status writes are still possible, and the code/documentation contract is currently inaccurate. | High |
| 3 | tests/delivery/test_integration.py:55 | Security-critical webhook verification is not exercised. The test suite overrides `verify_twilio_signature`, so there is no coverage for valid signatures, invalid signatures, or URL reconstruction edge cases. | The highest-risk webhook path has no direct regression protection. | High |
| 4 | tests/delivery/test_scheduler.py | Scheduler coverage is good for quiet hours and basic timezone conversion, but it does not cover DST transitions, UTC+14 / UTC-12 extremes, or repeated queue polling after a delivery is due. | The main timing edge cases called out in the review brief can still regress silently. | Medium |
| 5 | src/shared/config.py:20 and .env.example:12 | `Settings` defines `twilio_whatsapp_from`, but `.env.example` does not document `TWILIO_WHATSAPP_FROM`. | Easy misconfiguration in the primary WhatsApp market; deployment docs are incomplete for this feature. | Medium |
| 6 | src/delivery/models.py:20 | Reviewed Pydantic models do not enable strict mode, even though `docs/category-architecture.md:41` says “Pydantic v2 (strict mode, all models validated)”. | Architecture drift: coercion can happen where the docs say it should not. | Medium |
| 7 | tests/delivery/test_whatsapp.py | There is no test for already-prefixed WhatsApp numbers, malformed `From` values in the webhook, or invalid/missing signature headers. | Known bug surfaces and security edge cases are currently uncovered. | Medium |

### Observations (Worth Noting)
- The delivery layer stays entity-agnostic. I did not find pet-specific logic in the delivery, scheduler, webhook, or config modules.
- `recipient_id` is present on `DeliveryRequest`, and `active_arcs` is accepted by `schedule_delivery()` without changing Phase 1 behavior, which matches the foundation doc.
- Channel routing in `send_message()` and `deliver_with_retry()` is otherwise clean and readable. The unsupported `VOICE` / `PUSH` cases correctly raise `ValueError`.
- Retry accounting looks correct once a send function is invoked: attempts increment properly, `last_attempt_at` is updated per attempt, and there is no sleep after the final failed attempt.
- Verification was partially constrained by the local environment. `pytest tests/delivery/test_scheduler.py -q` passed (`20 passed`), but broader pytest invocations for the other delivery suites hit a Windows permission error during collection under `C:\shekar73\Documents\Projects`, so those suites were reviewed primarily from code inspection rather than a full local run.

### Disagree
| # | Codex Said | Our Reasoning |
|---|------------|---------------|
| 1 | The retry spec in the brief is internally inconsistent: it asks for 3 attempts with delays `60s`, `300s`, `900s`, while also saying there should be no sleep after the last failed attempt. The current implementation uses 3 attempts and only the first two sleeps, leaving `900s` defined but unused. | This should be clarified in the architecture/docs before changing code. If the intended policy is truly `1m, 5m, 15m`, then there must be a fourth attempt or a different retry model. |

### Codex Summary Assessment
> The feature is structurally solid and mostly aligned with the intended abstraction boundaries, but it still has two fix-now correctness problems in the scheduler: duplicate delivery risk from a queue with no claim/ack state, and incorrect handling of DST edge cases when localizing naive datetimes. After those are corrected, the main remaining work is tightening webhook/security coverage and closing a few configuration and edge-case gaps around WhatsApp and strict validation.

### Patterns (add to docs/review/patterns.md if recurring)
- [ ] In-memory “Phase 1” infrastructure needs explicit state-transition tests, otherwise placeholder implementations can accidentally violate production semantics.
- [ ] Security dependencies are being bypassed in integration tests without companion direct tests for the real security path.
- [ ] Architecture says “strict mode”, but reviewed Pydantic models do not consistently encode that contract in code.

### Comparison with F01 Review
_Did Codex flag similar issues as in the F01 review? Any patterns forming?_
- [ ] Not compared in this pass.
