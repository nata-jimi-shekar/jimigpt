# R01: LLM Abstraction & Intelligence Foundation — Refactoring Feature

**Phase:** 1B (Insert between F02 complete and F03 start)
**Priority:** CRITICAL — addresses existential risk of single-provider dependency
**Architecture Reference:** docs/model-resilience-intelligence.md
**Depends On:** F02 (Message Pipeline) complete

> This is a refactoring feature, not a new feature. It restructures
> existing code without changing behavior. All existing tests MUST
> pass unchanged after each task.

## Why This Exists

Two existential risks identified during architecture review:
1. **Single-provider dependency:** If Anthropic goes down, zero messages
   deliver. No fallback. No degraded mode.
2. **Zero intelligence accumulation:** Effectiveness data flows into a
   dead end. No learning loop. No proprietary intelligence. We're a
   prompt wrapper.

This refactoring addresses Risk 1 immediately and lays the data
collection foundation for Risk 2.

## What "Done" Looks Like
- generator.py uses a provider abstraction, not direct Anthropic calls
- Any provider can be swapped via config without code changes
- A CachedProvider stub exists for fallback
- OpenAI provider stub exists (not implemented, raises NotConfigured)
- Routing config YAML skeleton exists
- MessageGenerationLog model defined for data collection
- All existing F01 and F02 tests pass unchanged
- New tests cover the abstraction layer

---

## Micro-Tasks

### Task 1: LLM Provider Interface & Models
**Time:** 25 min
**Context:** Read docs/model-resilience-intelligence.md Part 1
**What to do:**
- Create src/shared/llm.py with:
  - LLMProvider enum (ANTHROPIC, OPENAI, LOCAL, CACHED)
  - ModelConfig model (provider, model_id, cost rates, quality tier)
  - LLMResponse model (content, provider, model_id, tokens, cost, latency)
  - RoutingDecision model (selected model, reason, fallback chain)
  - BaseProvider abstract class with async generate() method signature:
    ```python
    class BaseProvider:
        async def generate(
            self, system_prompt: str, user_message: str,
            *, model: str, max_tokens: int
        ) -> LLMResponse:
            ...
    ```
- Write tests/shared/test_llm.py:
  - All models validate correctly
  - LLMProvider enum has all expected values
  - LLMResponse computes cost from token counts
**Done when:** Models validate, interface defined, tests pass
**Commit:** `feat(shared): add LLM provider interface and response models`

### Task 2: Anthropic Provider Implementation
**Time:** 25 min
**Context:** Current generator.py Anthropic integration
**What to do:**
- Create AnthropicProvider class in src/shared/llm.py implementing BaseProvider
- Move the Anthropic-specific code from generator.py into this class:
  - Client initialization (anthropic.AsyncAnthropic)
  - messages.create() call
  - Response parsing (content[0].text, usage tokens)
  - Error handling
- AnthropicProvider.generate() returns LLMResponse with:
  - content from response
  - cost calculated from ModelConfig rates
  - latency measured with time.monotonic
- Write tests:
  - Mock Anthropic client, verify LLMResponse populated correctly
  - Error from API produces clear exception
  - Cost calculation is accurate
**Done when:** AnthropicProvider generates LLMResponse from Anthropic API
**Commit:** `feat(shared): add AnthropicProvider implementation`

### Task 3: Refactor generator.py to Use Provider
**Time:** 20 min
**Context:** Tasks 1-2. This is the critical swap.
**What to do:**
- Update generate_message() to accept BaseProvider instead of anthropic.AsyncAnthropic
- Replace direct Anthropic calls with provider.generate()
- Map LLMResponse fields to GeneratedMessage fields
- Add provider and cost_usd fields to GeneratedMessage:
  ```python
  provider: str = "anthropic"  # Which provider generated this
  cost_usd: float = 0.0        # Cost of this generation
  latency_ms: int = 0          # Generation latency
  ```
- **CRITICAL:** All existing F02 tests must pass without modification.
  The tests inject a mock client — update the mock to return LLMResponse
  instead of raw Anthropic response, OR keep backward compatibility
  with the old client parameter for existing tests.
- Write one new test: generate_message with AnthropicProvider mock
**Done when:** generator.py uses provider abstraction, ALL existing tests pass
**Commit:** `refactor(messaging): use LLM provider abstraction in generator`

### Task 4: Provider Stubs — OpenAI, Local, Cached
**Time:** 20 min
**Context:** docs/model-resilience-intelligence.md Part 1
**What to do:**
- Add to src/shared/llm.py:
  - OpenAIProvider(BaseProvider) — raises NotConfiguredError with helpful message
  - LocalProvider(BaseProvider) — raises NotConfiguredError
  - CachedProvider(BaseProvider) — stub that returns from a message pool
    (pool is empty for now, returns "Message temporarily unavailable" if called)
- Write tests:
  - OpenAIProvider raises NotConfiguredError
  - LocalProvider raises NotConfiguredError  
  - CachedProvider returns fallback message when pool is empty
**Done when:** All four provider classes exist, stubs behave correctly
**Commit:** `feat(shared): add OpenAI, Local, and Cached provider stubs`

### Task 5: Routing Config & Provider Factory
**Time:** 25 min
**Context:** docs/model-resilience-intelligence.md routing rules section
**What to do:**
- Create config/llm_routing.yaml with:
  ```yaml
  default:
    primary: "anthropic:claude-haiku-4-5"
    fallback:
      - "cached:personality_matched"
    max_cost_per_message_usd: 0.001

  high_stakes:
    triggers:
      - trust_stage: "deep"
      - intent: "comfort"
      - intent: "defer"
    primary: "anthropic:claude-sonnet-4-6"
    fallback:
      - "anthropic:claude-haiku-4-5"
      - "cached:personality_matched"

  quality_test:
    sample_rate: 0.05
    model: "openai:gpt-4o-mini"
    enabled: false  # Enable when OpenAI provider is implemented
  ```
- Create get_provider(config_key: str) factory function that:
  - Loads routing config from YAML
  - Returns the appropriate BaseProvider instance
  - Falls back through the chain if primary is unavailable
- In Phase 1, this always returns AnthropicProvider (OpenAI/Local not configured)
- Write tests:
  - Factory returns AnthropicProvider for default config
  - Factory returns AnthropicProvider for high_stakes (both are Anthropic in Phase 1)
  - Config loads without error
**Done when:** Routing config exists, factory returns correct provider
**Commit:** `feat(shared): add LLM routing config and provider factory`

### Task 6: MessageGenerationLog Model
**Time:** 20 min
**Context:** docs/model-resilience-intelligence.md Part 4 (Data Collection)
**What to do:**
- Create src/shared/generation_log.py with:
  - MessageGenerationLog Pydantic model (full telemetry):
    composition snapshot, prompt text, tokens, content, model used,
    provider, latency, cost, quality gate result, effectiveness fields
  - log_generation() function that creates a MessageGenerationLog
    from a GeneratedMessage + MessageComposition + QualityResult
  - In Phase 1, this function STORES LOCALLY (JSON file or in-memory list)
    since database isn't built yet. In F05, it writes to DB.
- Write tests:
  - Log model validates with all required fields
  - log_generation produces correct record from inputs
  - Effectiveness fields default to None (filled later)
**Done when:** Generation log model defined, logging function works
**Commit:** `feat(shared): add MessageGenerationLog model for intelligence collection`

### Task 7: Wire Logging to Generator
**Time:** 20 min
**Context:** Tasks 3 and 6
**What to do:**
- Update generate_message() to call log_generation() after each
  successful generation
- The log captures: full composition, prompt text, response content,
  model, provider, tokens, cost, latency
- Logging is fire-and-forget — it MUST NOT slow down or break message
  generation. Wrap in try/except, log errors, continue.
- Write tests:
  - Generation still works when logging is present
  - Generation still works when logging fails (graceful degradation)
  - Log contains correct composition data
**Done when:** Every generation creates a log record, failures are silent
**Commit:** `feat(messaging): wire generation logging for intelligence collection`

### Task 8: Personality Fingerprint Foundation
**Time:** 25 min
**Context:** docs/model-resilience-intelligence.md Part 2 (Model Quality Monitoring)
**What to do:**
- Create src/shared/fingerprint.py with:
  - PersonalityFingerprint model:
    archetype_id, model_id, generated_at, avg_message_length,
    exclamation_rate, emoji_rate, caps_word_rate, question_rate,
    avg_sentence_length, vocabulary_diversity, energy_proxy,
    warmth_proxy, humor_proxy
  - extract_fingerprint(messages: list[str]) -> PersonalityFingerprint
    Pure function that computes linguistic features from a list of messages
  - DriftDetection model:
    model_a, model_b, drift_score, dimensions_drifted, alert_level
  - compare_fingerprints(a, b) -> DriftDetection
    Computes drift score between two fingerprints
- Create config/fingerprint_tests.yaml with 10 test scenarios
  (one per archetype + 2 cross-archetype edge cases)
- Write tests:
  - High-energy messages produce high energy_proxy
  - Emoji-heavy messages produce high emoji_rate
  - Two identical message sets produce drift_score near 0.0
  - Very different message sets produce drift_score > 0.3
**Done when:** Fingerprint extraction and comparison work correctly
**Commit:** `feat(shared): add personality fingerprinting for model drift detection`

---

## Task Summary

| # | Task | Time | Depends On |
|---|------|------|------------|
| 1 | LLM Provider interface & models | 25 min | F02 complete |
| 2 | Anthropic Provider implementation | 25 min | Task 1 |
| 3 | Refactor generator.py | 20 min | Task 2 |
| 4 | Provider stubs (OpenAI, Local, Cached) | 20 min | Task 1 |
| 5 | Routing config & provider factory | 25 min | Tasks 2, 4 |
| 6 | MessageGenerationLog model | 20 min | Task 3 |
| 7 | Wire logging to generator | 20 min | Tasks 3, 6 |
| 8 | Personality fingerprint foundation | 25 min | F02 complete |

**Total estimated time:** ~3 hours (8 reps across 2-3 daily sessions)

---

## Review Plan

**Codex review:** After all 8 tasks complete (per standard feature review)
**Opus review:** Tasks 3 (generator refactor — must not break anything) and
Task 5 (routing config — determines fallback behavior)

---

## What This Enables

After R01, the system has:
- Provider-agnostic generation (can switch models via config)
- Fallback chain defined (primary → secondary → cached → skip)
- Every generation logged for future intelligence training
- Personality drift detection ready for use
- Cost tracking per message

What it does NOT have yet (Phase 2):
- Working OpenAI provider
- Working local model provider
- Populated cached message pool
- Active routing rules (always uses primary in Phase 1)
- Database storage for logs (uses local storage until F05)
- Automated fingerprint testing schedule
