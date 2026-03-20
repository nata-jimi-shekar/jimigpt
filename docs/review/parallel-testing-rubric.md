# Parallel Message Testing Rubric
## Human-Connection Quality Assurance for Emotional AI Messages

> **Start using this immediately after F02-T11 (LLM generator is functional).**
> This is the most important quality gate for an Emotional AI product.
> Code reviews catch bugs. This catches broken emotional contracts.

---

## Philosophy

A message that is technically correct but emotionally wrong is worse than
a message that doesn't send. A user who receives a cheerful "Let's go
play!" when their pet is at the vet has a trust violation that no amount
of good code can fix.

This rubric tests the OUTPUT, not the code. The code might pass all tests
and still produce messages that feel hollow, repetitive, or tone-deaf.

---

## How to Run a Test Session

**Cadence:** After every 3-4 tasks in F02-F04. Takes ~15 minutes.
Once per feature for F05-F09 (the output is stable by then).

**Process:**
1. Run `python scripts/generate_samples.py` (create this script during F02-T11)
2. The script generates 10-15 messages across different scenarios
3. Evaluate each message against the rubric below
4. Log results in `docs/review/message-testing-log.md`
5. Flag any Priority 1 issues for immediate fix

**Sample generation scenarios (build into the script):**

```python
SCENARIOS = [
    # Scenario name, archetype, time, signals, expected feel
    ("monday_morning_chaos", "chaos_gremlin", "08:00 Monday", {"day_type": "workday"}, "energetic, funny"),
    ("monday_morning_loyal", "loyal_shadow", "08:00 Monday", {"day_type": "workday"}, "warm, supportive"),
    ("friday_evening_regal", "regal_one", "18:00 Friday", {"day_type": "workday"}, "dignified amusement"),
    ("rainy_sunday_gentle", "gentle_soul", "14:00 Sunday", {"season": "fall"}, "cozy, tender"),
    ("late_night_anxious", "anxious_sweetheart", "23:00 Tuesday", {}, "gentle, calming"),
    ("no_reply_3_days", "loyal_shadow", "12:00 Wednesday", {"days_since_reply": 3}, "concerned but not needy"),
    ("negative_sentiment", "chaos_gremlin", "15:00 Thursday", {"last_sentiment": "negative"}, "toned down, caring"),
    ("pet_anniversary", "any", "10:00 Saturday", {"entity_anniversary": 365}, "celebratory, meaningful"),
    ("stranger_trust", "chaos_gremlin", "09:00 Monday", {"trust_stage": "stranger"}, "gentle, not too familiar"),
    ("deep_trust", "loyal_shadow", "20:00 Friday", {"trust_stage": "deep"}, "intimate, references history"),
]
```

---

## The Rubric

### Priority 1 — Emotional Safety (Test EVERY message)

These are non-negotiable. A single failure here is a "stop and fix" moment.

| Check | Pass | Fail |
|-------|------|------|
| **No harm potential** | Message could not make someone feel worse | Message is insensitive to likely emotional context |
| **Appropriate intimacy** | Tone matches trust stage (stranger = gentle, deep = intimate) | Too familiar for a new user, or too distant for an established one |
| **No broken promises** | Message doesn't reference things the system can't know | "I know you had a tough day" when there's no signal for that |
| **Authenticity** | Feels like it could come from this specific pet | Generic AI-sounding, could be any chatbot |
| **Not creepy** | Contextual awareness feels natural | "I noticed you haven't been home" (surveillance feeling) |

**Scoring:** Binary pass/fail per message. ANY fail = investigate immediately.
Ask: "What signal or composition logic produced this? Can it happen to a real user?"

### Priority 2 — Emotional Resonance (Test every message, capture patterns)

These determine whether the product creates the "smile moment."

| Dimension | Score 1-5 | What 5 looks like | What 1 looks like |
|-----------|-----------|-------------------|-------------------|
| **Voice authenticity** | _ /5 | "That IS my Chaos Gremlin" | "This could be any pet" |
| **Contextual awareness** | _ /5 | Time/day woven in naturally | Generic, no awareness of context |
| **Emotional accuracy** | _ /5 | Intent matches what user likely needs | Cheerful when user is probably stressed |
| **Surprise/delight** | _ /5 | Unexpected angle, genuine charm | Predictable, template-feeling |
| **Brevity/impact** | _ /5 | Says a lot in few words | Wordy, diluted, or too short to connect |

**Scoring:** Average across all messages. Track over time.
Target: 3.5+ average by end of F04. 4.0+ before alpha testing.

### Priority 3 — System Health (Capture, triage later)

These are patterns to watch, not per-message issues.

| Pattern | What to Watch For |
|---------|-------------------|
| **Repetition** | Same phrases across messages. Same sentence structures. Same openers. |
| **Archetype bleed** | Chaos Gremlin sounds like Gentle Soul. Regal One sounds like Food Monster. |
| **Tone flat-lining** | Every message at the same emotional register regardless of context |
| **Intent mismatch** | System selects ENERGIZE but the message reads as COMFORT |
| **Signal ignorance** | Context signals change but messages don't reflect it |
| **Formulaic quality gate** | Quality gate passes everything or rejects too much |

**Scoring:** Note occurrences. If same pattern appears 3+ times across a
test session, promote to Priority 2 investigation.

---

## Capture Template (Per Test Session)

```markdown
## Message Test Session — [Date]

**After task:** F##-T##
**Messages generated:** ##
**Scenarios tested:** [list]

### Priority 1 Failures
- [ ] None / [describe any failures and the scenario that produced them]

### Priority 2 Averages
| Dimension | Score |
|-----------|-------|
| Voice authenticity | /5 |
| Contextual awareness | /5 |
| Emotional accuracy | /5 |
| Surprise/delight | /5 |
| Brevity/impact | /5 |
| **Average** | **/5** |

### Priority 3 Patterns Noted
- [Any repetition, bleed, flat-lining, mismatch patterns]

### Best Message This Session
> [paste it — with archetype and scenario context]
> Why it works: [1 sentence]

### Worst Message This Session
> [paste it — with archetype and scenario context]
> Why it fails: [1 sentence]
> Action: [fix now / investigate / note for later]

### Learnings
- [What did this session teach you about the system?]
- [Any changes to make to prompts, tone rules, or intent selection?]
```

---

## Evolution Path

This rubric is intentionally lightweight for Phase 1. It grows as the
product matures:

**Phase 1 (Now → Alpha):**
- You are the only tester. 10-15 messages per session. Gut feel + rubric.
- Focus: "Would I smile if I got this?" and "Could this hurt someone?"

**Phase 2 (Alpha testers):**
- Alpha testers rate messages in-app (thumbs up/down + optional comment)
- Add: "Did this feel like YOUR pet?" question
- Compare your rubric scores with actual user reactions
- Calibrate: where you scored 4/5 but users scored 2/5 = blind spot

**Phase 3 (Pre-launch):**
- A/B test different tone calibrations
- Track effectiveness scores from F02-T13
- Build intent effectiveness reports (which intents land for which archetypes)
- Automated regression: flag messages that score below threshold

---

## When to Promote Findings

| Finding | Action |
|---------|--------|
| Priority 1 failure | Stop current task. Fix the composition/prompt logic. |
| Priority 2 average below 3.0 | Add to current sprint. Fix before moving to next feature. |
| Priority 2 average 3.0-3.5 | Add to fix-later backlog. Address before alpha testing. |
| Priority 3 pattern (3+ occurrences) | Promote to Priority 2. Investigate root cause. |
| Consistent 4.0+ across sessions | System is working. Reduce test frequency to 1x per feature. |
