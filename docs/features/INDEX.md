# JimiGPT Feature Index

## Build Order & Dependencies

```
Phase 1A: Foundation
  F01 → Personality Engine (10 tasks, ~4 hrs)        ← +1 task for tone/intent

Phase 1B: Pipeline
  F02 → Message Pipeline (14 tasks, ~5.5 hrs)        ← Expanded with message modeling
  F03 → Delivery Layer (6 tasks, ~2 hrs)              depends on F02
  F04 → Trust & Safety (4 tasks, ~1.5 hrs)            depends on F01, F02

Phase 1C: Product
  F05 → Database, Auth & Payments (6 tasks, ~2.5 hrs)  depends on F01-F04
  F06 → Birthing Ceremony API (5 tasks, ~2 hrs)        depends on F01, F05
  F07 → Frontend Birthing (9 tasks, ~3.5 hrs)          depends on F06

Phase 1D: Polish
  F08 → Feedback & Refinement (6 tasks, ~2.5 hrs)  depends on F01-F07  ← +1 task for recipient preference
  F09 → Batch Runner & Monitoring (5 tasks, ~2 hrs) depends on F01-F06
```

**Key Architecture Documents:**
- docs/category-architecture.md — Shared engine specs (v1.1, updated)
- docs/jimigpt-architecture.md — JimiGPT-specific specs
- docs/message-modeling.md — Message composition: intent, tone, signals, state, recipient preference
- docs/user-testing-strategy.md — User-backward validation approach

## Total Estimates

| Phase | Features | Tasks | Estimated Hours |
|-------|----------|-------|-----------------|
| 1A    | F01      | 10    | 4.0             |
| 1B    | F02-F04  | 24    | 9.0             |
| 1C    | F05-F07  | 20    | 8.0             |
| 1D    | F08-F09  | 11    | 4.5             |
| **Total** | **9 features** | **65 tasks** | **~25.5 hours** |

At 3-4 productive hours per day, that's approximately **7-9 weeks** to MVP.

## Feature Files
- [F01: Personality Engine](F01-personality-engine.md)
- [F02: Message Pipeline](F02-message-pipeline.md)
- [F03: Delivery Layer](F03-delivery-layer.md)
- [F04: Trust & Safety](F04-trust-safety.md)
- [F05: Database, Auth & Payments](F05-database-auth-payments.md)
- [F06: Birthing Ceremony API](F06-birthing-ceremony-api.md)
- [F07: Frontend Birthing](F07-frontend-birthing.md)
- [F08: Feedback & Refinement](F08-feedback-refinement.md)
- [F09: Batch Runner & Monitoring](F09-batch-runner-monitoring.md)
