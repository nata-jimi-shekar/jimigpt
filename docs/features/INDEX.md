# Feature Index

## Execution Order

```
PHASE 1A:  F01 ✓
PHASE 1B:  F02 ✓ → R01 → F03 → F04
PHASE 1C:  F05 → F06 → F07
PHASE 1D:  F08 → F09 → Self-dogfood (14 days)
```

For phases beyond 1, see docs/unified-roadmap.md.

## Features

| ID | Name | Tasks | Hours | Phase | Status |
|----|------|-------|-------|-------|--------|
| F01 | Personality Engine | 10 | 4.0h | 1A | ✅ Complete |
| F02 | Message Pipeline | 14 | 6.5h | 1B | ✅ Complete |
| R01 | LLM Abstraction & Intelligence Foundation | 8 | 3.0h | 1B | **NEXT** |
| F03 | Delivery Layer | 6 | 2.0h | 1B | Not started |
| F04 | Trust & Safety | 4 | 1.5h | 1B | Not started |
| F05 | Database, Auth & Payments | 6 | 2.5h | 1C | Not started |
| F06 | Birthing Ceremony API | 5 | 2.0h | 1C | Not started |
| F07 | Frontend Birthing | 9 | 3.5h | 1C | Not started |
| F08 | Feedback & Refinement | 6 | 2.5h | 1D | Not started |
| F09 | Batch Runner & Monitoring | 6 | 2.5h | 1D | Not started |

## Feature Files

- [F01: Personality Engine](F01-personality-engine.md)
- [F02: Message Pipeline](F02-message-pipeline.md)
- [R01: LLM Abstraction & Intelligence Foundation](R01-llm-abstraction.md)
- [F03: Delivery Layer](F03-delivery-layer.md)
- [F04: Trust & Safety](F04-trust-safety.md)
- [F05: Database, Auth & Payments](F05-database-auth-payments.md)
- [F06: Birthing Ceremony API](F06-birthing-ceremony-api.md)
- [F07: Frontend Birthing](F07-frontend-birthing.md)
- [F08: Feedback & Refinement](F08-feedback-refinement.md)
- [F09: Batch Runner & Monitoring](F09-batch-runner-monitoring.md)

## Reference Documents

- [Unified Roadmap](../unified-roadmap.md) — single source for all phases
- [Category Architecture](../category-architecture.md) — shared engine specs
- [JimiGPT Architecture](../jimigpt-architecture.md) — product-specific specs
- [Message Modeling](../message-modeling.md) — intent, tone, signals, composition
- [Future Architecture](../future-architecture.md) — Phase 2+ designs (arcs, multi-recipient, life events)
- [Model Resilience & Intelligence](../model-resilience-intelligence.md) — provider abstraction, intelligence accumulation
- [Foundation Per Feature](../foundation-per-feature.md) — Phase 2 foundation fields checklist
- [Review Workflow](../review/REVIEW-WORKFLOW.md) — multi-model review system
- [Strategic Deep Dive](../strategic-deep-dive.md) — B2B + content platform logical path
