# Foundation Fields — Per-Feature Checklist
## Quick Reference for Claude Code During Implementation

> **Read this alongside each feature file.** It lists the specific foundation
> fields to include in each feature. Full design rationale is in
> docs/future-architecture.md.
>
> **Rule:** Foundation fields MUST default to None or empty. They MUST NOT
> change Phase 1 behavior. They MUST be tested with default values.

---

## F01: Personality Engine — NO CHANGES NEEDED
F01 is complete. Personality models are entity-agnostic. Multi-recipient,
arcs, and life events are messaging/pipeline concepts, not personality concepts.

---

## F02: Message Pipeline — FOUNDATION FIELDS INCLUDED
*See updated docs/features/F02-message-pipeline.md for full task details.*

| Task | Foundation Addition | Default Value |
|------|-------------------|---------------|
| T1: Trigger Models | `arc_template: str \| None` | None |
| T1: Trigger Models | `sibling_entity_ids: list[str]` | [] |
| T4: Orchestrator | `sibling_entity_schedules` param | None |
| T5: Signal Models | `USER_CONTEXT` in ContextSignalSource enum | (enum value only) |
| T6: INTERACTION | `last_reply_context_tags: list[str]` | [] |
| T7: Intent Selection | `life_contexts` param | None |
| T8: Tone Calibration | `life_contexts` param | None |
| T9: Recipient State | `life_contexts` param | None |
| T10: Composer | `arc_id: str \| None` | None |
| T10: Composer | `arc_position: int \| None` | None |
| T10: Composer | `recipient_id: str \| None` | None |
| T10: Composer | `life_contexts: list[str]` | [] |
| T10: Composer | `entity_coordination_id: str \| None` | None |
| T10: compose() | `recipient_id` param | None (uses entity owner) |
| T12: Quality Gate | CONSECUTIVE_COHERENCE check | (new check) |
| T14: Integration | Verify all None/empty defaults | (test coverage) |

---

## F03: Delivery Layer — MINOR FOUNDATION WORK

| Task | Foundation Addition | Rationale |
|------|-------------------|-----------|
| T1: Delivery Models | `recipient_id: str` on DeliveryRequest (not entity owner — explicit recipient) | Multi-recipient: delivery goes to a specific person, not just "the entity owner" |
| T3: Scheduler | Accept `active_arcs: list[dict] \| None = None` param | Arc messages have specific timing that the scheduler should be aware of in Phase 2 |
| T3: Scheduler | No UNIQUE constraint on (entity_id + user_id) in scheduling logic | Multi-recipient: same entity delivers to different people |

---

## F04: Trust & Safety — MINOR FOUNDATION WORK

| Task | Foundation Addition | Rationale |
|------|-------------------|-----------|
| T1: Trust Models | TrustProfile takes `recipient_id` (not just entity_id + user_id) | Multi-recipient: trust is per-recipient. In Phase 1, recipient_id = owner_id |
| T3: Escalation | `life_contexts: list[str] \| None = None` param on assess_escalation() | Life events affect escalation sensitivity. Pet_sick + distress language = higher urgency |
| T3: Escalation | Document in code: "No entity speaks without primary owner consent" principle | B2B foundation: this principle protects the owner's relationship with the entity |

---

## F05: Database, Auth & Payments — SCHEMA AWARENESS

| Task | Foundation Addition | Rationale |
|------|-------------------|-----------|
| T2: Migration | messages table: NO unique constraint on (entity_id, user_id, scheduled_at) | Multi-recipient: same entity can send to different users at different times |
| T2: Migration | Add `recipient_id UUID` column to messages table (nullable for now, defaults to user_id) | Ready for multi-recipient without schema migration later |
| T2: Migration | Add `arc_id UUID` column to messages table (nullable) | Track which arc a message belongs to |
| T2: Migration | Add `life_context TEXT` column to messages table (nullable) | Record active life context when message was generated |
| T2: Migration | Reserve table name: `entity_recipients` (don't create, just document) | Phase 2 table — avoid naming conflicts |
| T2: Migration | Reserve table name: `life_contexts` (don't create, just document) | Phase 2 table — avoid naming conflicts |
| T5: Messages | Message persistence uses explicit recipient_id, not derived from entity | Consistent with F02 composer pattern |

---

## F06-F09: NO FOUNDATION WORK NEEDED

F06 (Birthing Ceremony): Entity creation is single-owner. Multi-recipient
is added after birthing, not during. No changes needed.

F07 (Frontend): UI is single-user in Phase 1. Multi-recipient UI is
a Phase 2 feature. No changes needed.

F08 (Feedback): RecipientPreference evolution works per-user already.
No changes needed.

F09 (Batch Runner): Batch generation will need multi-recipient awareness
in Phase 2, but the F09 Phase 1 implementation runs per-entity which
is correct for single-owner. No changes needed — the foundation from
F02 (recipient_id on compose()) means F09 just passes the owner ID.

---

## Testing Foundation Fields

For every foundation field, write these tests:
1. **Default value test:** Field defaults to None/empty without explicit setting
2. **Pass-through test:** None/empty value flows through the pipeline without error
3. **No behavior change test:** Output with None/empty is identical to what it
   would be without the field (Phase 1 behavior unchanged)

Example:
```python
def test_message_composition_foundation_defaults():
    """Foundation fields default correctly for Phase 1."""
    comp = create_test_composition()  # No arc/recipient/life context set
    assert comp.arc_id is None
    assert comp.arc_position is None
    assert comp.recipient_id is None  # Or set to owner_id by composer
    assert comp.life_contexts == []
    assert comp.entity_coordination_id is None

def test_pipeline_works_with_foundation_defaults():
    """Full pipeline produces valid output with all foundation fields at defaults."""
    result = run_pipeline_with_defaults()
    assert result.quality_gate_passed
    assert result.message.content  # Non-empty message generated
```
