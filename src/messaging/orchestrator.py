"""Trigger evaluation orchestrator — routes rules to the right evaluator
and enforces global constraints across all trigger types."""

from datetime import datetime

from src.messaging.random_trigger import evaluate_random_trigger
from src.messaging.time_trigger import evaluate_time_trigger
from src.messaging.triggers import TriggerRule, TriggerType

_MAX_PER_DAY = 5


def evaluate_triggers(
    rules: list[TriggerRule],
    current_time: datetime,
    user_context: dict,
    *,
    sibling_entity_schedules: list[dict] | None = None,
) -> list[TriggerRule]:
    """Return every rule that should fire at current_time for this user.

    Routing:
    - TIME_BASED       → evaluate_time_trigger (uses context timezone)
    - RANDOM_INTERVAL  → evaluate_random_trigger (uses rule timezone + context counts)
    - All other types  → skipped in Phase 1 (EVENT_BASED, RESPONSE_TRIGGERED, MILESTONE)

    Global constraints applied here (not inside individual evaluators):
    - Maximum 5 messages per day across all trigger types. The running count
      starts at user_context["messages_today"] and increments with each fired rule.

    Foundation (Phase 2):
    - sibling_entity_schedules is accepted but ignored in Phase 1. In Phase 2
      this will coordinate timing across entities belonging to the same user.
    """
    # --- extract context ---
    timezone: str = str(user_context.get("timezone", "UTC"))
    messages_today: int = int(user_context.get("messages_today", 0))
    last_fired_by_rule: dict[str, datetime] = dict(
        user_context.get("last_fired_by_rule", {})
    )

    fired: list[TriggerRule] = []

    for rule in rules:
        # Global daily cap — stop as soon as it is reached.
        if messages_today + len(fired) >= _MAX_PER_DAY:
            break

        if rule.trigger_type == TriggerType.TIME_BASED:
            if evaluate_time_trigger(rule, current_time, timezone):
                fired.append(rule)

        elif rule.trigger_type == TriggerType.RANDOM_INTERVAL:
            last_fired = last_fired_by_rule.get(rule.rule_id)
            running_total = messages_today + len(fired)
            if evaluate_random_trigger(rule, current_time, last_fired, running_total):
                fired.append(rule)

        # EVENT_BASED, RESPONSE_TRIGGERED, MILESTONE: not implemented in Phase 1.

    return fired
