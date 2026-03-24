# Codex Feature-Level Triage — F02: Message Pipeline

**Date:** [03/23/2026]
**Reviewer:** ChatGPT Codex
**Feature reviewed:** F02 — message-pipeline.md
**Tasks covered:** T1 through T10
**Files reviewed:** See F01-codex-brief-READY.md for full list

---

 
• ### Critical Issues (Fix Now)

  1. MessageComposer.compose() feeds archetype blend weights into select_intent(), not archetype intent weights.
     File: /C:/shekar73/Documents/Projects/jimigpt/src/messaging/composer.py:120, /C:/shekar73/Documents/Projects/
     jimigpt/src/messaging/intent.py:63, /C:/shekar73/Documents/Projects/jimigpt/src/personality/archetypes.py:31, /C:/
     shekar73/Documents/Projects/jimigpt/src/personality/models.py:94
     Function: MessageComposer.compose(), select_intent()
     Issue: select_intent() expects weights keyed by MessageIntent values, but compose() passes
     entity.archetype_weights, which are blend weights keyed by archetype id. In the integrated F01 model,
     EntityProfile.archetype_weights is metadata like {"jimigpt:chaos_gremlin": 1.0}, while the real intent distribution
     lives on ArchetypeConfig.intent_weights.
     Impact: intent selection is wrong anywhere weights matter. Anniversary selection collapses to the first preferred
     intent, personality_moment collapses to ENERGIZE, and unknown categories can raise when MessageIntent(best)
     receives an archetype id. This is the main F01 -> F02 integration contract break.
     Suggested fix: pass intent_weights explicitly into compose() alongside tone_defaults, or add a separate intent-
     weight input model. Do not reuse EntityProfile.archetype_weights for intent logic.
  2. score_effectiveness() awards a positive-sentiment bonus even when no reply occurred.
     File: /C:/shekar73/Documents/Projects/jimigpt/src/messaging/effectiveness.py:47
     Function: score_effectiveness()
     Issue: the function adds +0.2 whenever reply_sentiment == "positive", regardless of user_replied. I verified
     score_effectiveness(None, False, "positive") == 0.2.
     Impact: effectiveness scores are inflated for logically inconsistent records and downstream preference-learning/
     analytics will over-credit messages that never actually got a reply.
     Suggested fix: gate the sentiment bonus behind user_replied, or normalize reply_sentiment=None whenever
     user_replied=False. Add an explicit regression test for this case.
  3. Invalid cron expressions can crash trigger evaluation instead of failing closed.
     Files: /C:/shekar73/Documents/Projects/jimigpt/src/messaging/time_trigger.py:41, /C:/shekar73/Documents/Projects/
     jimigpt/src/messaging/orchestrator.py:49
     Function: evaluate_time_trigger(), evaluate_triggers()
     Issue: croniter(...) / get_next() is not wrapped. A malformed schedule_cron propagates out of
     evaluate_time_trigger(), and evaluate_triggers() does not catch it.
     Impact: one bad trigger rule can abort the whole evaluation pass for that user instead of just disabling the bad
     rule.
     Suggested fix: catch cron parsing errors in evaluate_time_trigger() and return False with logging, or catch per-
     rule failures in evaluate_triggers().

  ### Important Issues (Fix Later)

  1. SignalCollector.collect() does not actually support async collectors.
     File: /C:/shekar73/Documents/Projects/jimigpt/src/messaging/signals.py:69
     Function: SignalCollector.collect()
     Issue: the method is async, but it blindly does signals.extend(collector_fn(...)). With an async collector, it
     drops the source, logs a warning, and emits an unawaited-coroutine runtime warning.
     Impact: the Phase 1 sync collectors work, but future async collectors will silently fail at runtime.
     Suggested fix: broaden CollectorFn to support sync or async callables and await when the collector returns an
     awaitable.
  2. The composer claims life-context flow, but compose() neither accepts nor forwards life_contexts.
     File: /C:/shekar73/Documents/Projects/jimigpt/src/messaging/composer.py:6, /C:/shekar73/Documents/Projects/jimigpt/
     src/messaging/composer.py:100
     Function: MessageComposer.compose()
     Issue: the module docstring says life_contexts flows through intent/tone/state engines, but compose() has no
     life_contexts parameter and never passes one to select_intent(), calibrate_tone(), or infer_recipient_state().
     Impact: the declared Phase 2 foundation is only partially wired. Activating life contexts later will require
     changing the public composer interface instead of just turning on no-op fields.
     Suggested fix: add life_contexts: list[str] | None = None to compose() now and forward it through unchanged.
  3. The window logic only supports non-wrapping windows; overnight windows are impossible.
     Files: /C:/shekar73/Documents/Projects/jimigpt/src/messaging/time_trigger.py:47, /C:/shekar73/Documents/Projects/
     jimigpt/src/messaging/random_trigger.py:43
     Function: evaluate_time_trigger(), evaluate_random_trigger()
     Issue: both use start <= local_time < end. Any configured window like 22:00 to 07:00 can never match.
     Impact: if scheduling windows are ever configured across midnight, those rules become permanently ineligible.
     Suggested fix: handle wrapped intervals explicitly: normal case when start < end, overnight case when local_time >=
     start or local_time < end.
  4. Tests miss the real F01 -> F02 intent-weight integration path.
     Files: /C:/shekar73/Documents/Projects/jimigpt/tests/messaging/test_pipeline_integration.py:61, /C:/shekar73/
     Documents/Projects/jimigpt/tests/messaging/test_composer.py:188, /C:/shekar73/Documents/Projects/jimigpt/tests/
     messaging/test_effectiveness.py:175
     Issue: integration tests compose a blend_archetypes() profile and only exercise the greeting path, where wrong
     intent weights are invisible. The effectiveness tests also explicitly permit the inconsistent
     reply_sentiment="positive", user_replied=False case.
     Impact: both critical logic bugs above can pass the current suite.
     Suggested fix: add integration tests for personality_moment and anniversary using a real
     ArchetypeConfig.intent_weights, plus a failing test for positive sentiment without reply.

  ### Observations

  - The module split is good. Triggering, signal collection, intent, tone, recipient inference, generation, quality, and
    effectiveness are separated cleanly.
  - The tone rules file is readable and editable enough for a non-developer to tweak safely, assuming invalid dimensions
    are validated later.
  - The quality gate’s CONSECUTIVE_COHERENCE check is wired against previous_message.intended_intent and
    composition.intent.primary_intent, which matches the intended contract.

  ### Strengths

  - The 8-block prompt structure is present and easy to inspect in /C:/shekar73/Documents/Projects/jimigpt/src/
    messaging/composer.py:156.
  - Foundation fields are present on the right models and mostly behave as no-ops, which is the
  right forward-
    compatibility shape.
  - The quality gate is well-factored: checks are isolated, composable, and easy to extend.
  - The TIME / INTERACTION / SEASONAL collectors are simple and readable, and the functools.partial registration pattern
    is sound for the current sync collectors.

  ### Summary

  F02 has a solid modular shape, but two core contracts are wrong today: intent selection is wired to the wrong data
  source, and effectiveness scoring overcounts positive sentiment without a reply. After those are fixed, the next
  priority is hardening scheduling and collector error handling so bad config or future async collectors cannot silently
  break the pipeline.

  Verification: I reviewed the referenced docs, source, config, and tests, and I validated key behaviors with targeted
  Python snippets. I could not run the full jimigpt pytest suite in this environment because that repo is outside the
  writable sandbox roots here, and time_trigger.py also depends on croniter, which is unavailable in this shell.