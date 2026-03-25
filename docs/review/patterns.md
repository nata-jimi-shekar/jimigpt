# Review Patterns — Cumulative Learning Log

> **Updated after every review cycle.** Spend 2 minutes after each triage asking:
> "Did this reviewer flag the same kind of issue as last time?"
> Review this file monthly to update CLAUDE.md or architecture docs.

---

## Recurring Patterns

### Code Patterns
| Pattern | First Seen | Times Seen | Source | Status |
|---------|------------|------------|--------|--------|
| _example: Missing edge case tests for None/empty inputs_ | _F01-codex_ | _1_ | _Codex_ | _Monitoring_ |
| In-memory Phase 1 infrastructure needs explicit state-transition tests — placeholder impls can violate production semantics | F03-codex | 1 | Codex | Fixed (queue claim) |
| Security dependencies bypassed in integration tests without companion direct tests for the real security path | F03-codex | 1 | Codex | Backlog (#12) |
| Architecture says "strict mode" but Pydantic models don't consistently enforce it | F03-codex | 1 | Codex | Backlog (#13) |

### Message Quality Patterns
| Pattern | First Seen | Times Seen | Source | Status |
|---------|------------|------------|--------|--------|
| _example: Chaos Gremlin loses voice at low energy settings_ | _F02 test session 1_ | _1_ | _Parallel testing_ | _Investigating_ |

### Strategic Patterns
| Pattern | First Seen | Times Seen | Source | Status |
|---------|------------|------------|--------|--------|
| _example: No handling for pet health crisis scenarios_ | _F02-gemini_ | _1_ | _Gemini_ | _Parked for F04_ |

---

## Resolved Patterns

| Pattern | Resolution | Date | Impact |
|---------|-----------|------|--------|
| | | | |

---

## Pattern → Action Rules

- **Seen 3+ times from same source:** Root cause investigation. Something
  systemic needs to change (CLAUDE.md rule, architecture update, or
  review brief refinement).
- **Seen across 2+ sources:** High confidence this is real. Prioritize fix.
- **Seen once:** Note it. Don't act unless it's Priority 1.
