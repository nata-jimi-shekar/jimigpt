# Multi-Model Review Workflow
## JimiGPT Code Quality & Strategic Review System

> **Principle:** One model touches the code at a time. Sonnet writes. Others review read-only.
> You triage. Then Sonnet implements fixes. No model writes code directly into the repo
> except through Claude Code CLI (Sonnet).

---

## The Four Review Tiers

### Tier 1a — Sonnet Self-Review (Every Task)
**Already built into your workflow. No extra process.**
- Claude Code writes tests first, then implements
- You review the diff before merging
- CI runs Ruff + mypy + pytest on push
- This catches ~80% of issues

### Tier 1b — Opus Focused Review (High-Blast-Radius Tasks Only)
**When:** During F02 (message composition, tone calibration, intent selection),
F03 (delivery timing, quiet hours), F04 (all tasks — trust and safety is entirely
high-blast), F05 (database schema, auth, payment webhooks)

**Specific tasks to flag for Opus review:**
- F02-T7: Message intent selection (wrong intent = wrong emotional impact)
- F02-T8: Tone calibration engine (miscalibration = message feels off)
- F02-T10: Message composer (this is where everything converges)
- F02-T11: LLM message generator (prompt quality = message quality)
- F02-T12: Quality gate (the last defense before a message reaches a human)
- F03-T3: Delivery scheduler (wrong time = trust violation)
- F04-T2: Trust stage evaluation (wrong stage = inappropriate intimacy)
- F04-T3: Escalation detection (missed escalation = safety failure)
- F05-T2: Database migration (schema is expensive to change)
- F05-T4: Supabase Auth (security boundary)
- F05-T6: Stripe webhooks (financial correctness)

**That's ~11 tasks out of 65.** Each review is one 20-minute rep.

**How:** Use `docs/review/opus-review-brief.md` template. Paste to Opus (Claude desktop
with Opus model, or /model opus in Claude Code). Triage output into
`docs/review/triage/F##-T##-opus.md`.

### Tier 2 — Codex Feature Review (After Every Feature)
**When:** After completing all tasks in a feature (F01 through F09). 9 reviews total.

**How:** Create a git worktree for Codex review. Use `docs/review/codex-review-brief.md`
template. Feed to ChatGPT Codex. Triage output into `docs/review/triage/F##-codex.md`.

**Workflow (one bounded container — 1 hour, 3 reps):**
- Rep 1: Prepare brief. Fill in the template with feature-specific details.
  Include the feature doc, relevant architecture sections, and file list.
- Rep 2: Run Codex review. Read output. Triage into three buckets
  (fix now / fix later / disagree).
- Rep 3: Implement "fix now" items via Claude Code.
  Commit as `refactor(scope): address codex review feedback for F##`

### Tier 3 — Gemini Strategic Review (Every 2 Features)
**When:** After F02, F04, F06, F08 — roughly every 2 features, aligned with
meaningful product milestones. 4-5 reviews total.

**Cadence rationale:**
- After F02: Message pipeline complete — first time the core product logic exists.
  Ask: "Is this composition model going to serve different customer segments?"
- After F04: Trust & safety complete — emotional boundaries are set.
  Ask: "What scenarios are we not handling? What customer situations break this?"
- After F06: Birthing ceremony API complete — onboarding flow is real.
  Ask: "Does this onboarding create the right first impression for each user type?"
- After F08: Feedback system complete — the learning loop exists.
  Ask: "Is this feedback loop going to teach us what we need to know?"

**How:** Use `docs/review/gemini-strategic-brief.md` template. Feed to Gemini.
Capture output into `docs/review/triage/F##-gemini-strategic.md`.

### Tier 4 — Parallel Message Testing (Ongoing from F02)
**When:** Starts immediately after F02-T11 (LLM generator is functional).
Runs continuously alongside all subsequent development.

**How:** Use `docs/review/parallel-testing-rubric.md`. Generate sample messages
using `scripts/generate_samples.py` (create during F02). Evaluate against rubric.
Capture learnings in `docs/review/message-testing-log.md`.

---

## Triage Rules (Apply to ALL Review Tiers)

Every piece of feedback goes into exactly one bucket:

| Bucket | Criteria | Action | Timeline |
|--------|----------|--------|----------|
| **Fix Now** | Real bug, safety issue, architecture violation, data handling error | Implement immediately via Claude Code | Same session |
| **Fix Later** | Valid improvement but non-blocking. Style, optimization, edge case | Add to `docs/review/fix-later-backlog.md` with feature tag | Before MVP |
| **Disagree** | Conflicts with documented architecture decisions, or is a preference not a defect | Note the disagreement and reasoning in triage file | No action |

**Critical rule:** If you're unsure which bucket, it's "Fix Later" not "Fix Now."
Don't let review cycles block your build momentum.

---

## Pattern Tracking (Cumulative Learning)

After every review cycle, spend 2 minutes asking:
1. Did this reviewer flag the same kind of issue as last time?
2. Is there a systemic pattern forming?
3. Should I update CLAUDE.md or architecture docs to prevent this class of issue?

Capture patterns in `docs/review/patterns.md`. Review this file monthly.

---

## File Structure

```
docs/review/
├── REVIEW-WORKFLOW.md              ← This file (process overview)
├── opus-review-brief.md            ← Template for Opus task reviews
├── codex-review-brief.md           ← Template for Codex feature reviews
├── gemini-strategic-brief.md       ← Template for Gemini strategic reviews
├── parallel-testing-rubric.md      ← Message quality testing rubric
├── message-testing-log.md          ← Running log of message test results
├── fix-later-backlog.md            ← Accumulated non-blocking improvements
├── patterns.md                     ← Recurring patterns across reviews
└── triage/                         ← Per-review triage outputs
    ├── F01-codex.md
    ├── F02-T07-opus.md
    ├── F02-codex.md
    ├── F02-gemini-strategic.md
    └── ...
```
