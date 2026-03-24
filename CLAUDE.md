# JimiGPT

AI companion platform creating Digital Twins for pets with personality-driven
contextual messaging. Built on the Emotional AI Category Architecture — engine
code is entity-agnostic; pet-specific logic lives in configuration only.

## Tech Stack
- Backend: Python 3.12+, FastAPI, Pydantic v2
- Database: Supabase (PostgreSQL + Auth)
- LLM: Provider-agnostic via src/shared/llm.py (Anthropic primary, OpenAI fallback, local future)
- Messaging: Twilio SMS
- Testing: pytest + pytest-asyncio (TDD mandatory)
- Linting: Ruff
- Type checking: mypy --strict
- Frontend: Next.js + TypeScript + Tailwind (later phase)

## Commands
- Install: pip install -e ".[dev]"
- Test all: pytest
- Test single: pytest tests/personality/test_archetypes.py -v
- Test with coverage: pytest --cov=src
- Lint: ruff check src/ tests/
- Format: ruff format src/ tests/
- Type check: mypy src/
- Dev server: uvicorn src.main:app --reload

## Architecture Rules
- IMPORTANT: Read docs/unified-roadmap.md for the single source of all phases and milestones.
- IMPORTANT: Read docs/category-architecture.md for shared component specs.
- IMPORTANT: Read docs/jimigpt-architecture.md for product-specific specs.
- IMPORTANT: Read docs/future-architecture.md for Phase 2+ foundation designs.
  When building Phase 1 features, include the foundation fields documented here.
- IMPORTANT: Read docs/message-modeling.md for message composition architecture.
- IMPORTANT: Read docs/model-resilience-intelligence.md for LLM abstraction and intelligence strategy.
- Every engine component MUST be entity-agnostic at the core.
  Pet-specific logic belongs in config/ YAML files and PetProfile extension.
  Ask yourself: "Would this work for NeuroAmigo with only config changes?"
- Four-layer personality model: Communication Style, Emotional Disposition,
  Relational Stance, Knowledge & Awareness
- Message pipeline: Trigger → Signal Collection → Compose → Generate → Quality Gate → Deliver → Measure
- Pydantic models for ALL data. No raw dicts. No Any types.

## LLM Provider Rules
- NEVER call Anthropic (or any LLM) directly. Always go through src/shared/llm.py provider abstraction.
- Generator (src/messaging/generator.py) uses BaseProvider interface, not anthropic.AsyncAnthropic.
- Model selection comes from config/llm_routing.yaml, not hardcoded strings.
- Every generation MUST be logged via log_generation() for intelligence collection.
- Logging is fire-and-forget — MUST NOT slow down or break message generation.

## Foundation Fields (Phase 2+ Preparation)
When building F02-F05, include optional foundation fields for future features:
- Message Arcs: arc_id, arc_position on MessageComposition (None in Phase 1)
- Multi-Recipient: recipient_id parameter on compose functions (owner ID in Phase 1)
- Life Events: life_contexts parameter on intent/tone/recipient functions (None in Phase 1)
- Multi-Pet: sibling_entity_schedules on trigger orchestrator (None in Phase 1)
- User Context: USER_CONTEXT in ContextSignalSource enum (no collector in Phase 1)
These fields MUST default to None or empty. They MUST NOT change Phase 1 behavior.
They MUST be tested with their default values.

## Code Style
- Python 3.12+ features OK (type unions with |, match statements)
- Type hints on ALL function signatures. mypy strict compliance.
- Functional style preferred. Minimize classes — use them for Pydantic models
  and when state encapsulation genuinely helps.
- Functions under 30 lines. Extract if longer.
- Async by default for I/O operations.
- Use pathlib for file paths, never os.path.

## Testing (TDD)
- YOU MUST write the test FIRST, then implement.
- Every function has at least one test.
- For LLM outputs: use property-based tests (check length, contains name,
  no forbidden phrases, correct sentiment). Never assert exact LLM output.
- Test files mirror src/ structure in tests/
- Use fixtures in conftest.py for shared test data.
- Mock external services (LLM providers, Twilio, Supabase) in unit tests.
- Foundation fields: test that None/empty defaults work correctly.

## Git Workflow
- NEVER commit directly to main.
- Branch: git checkout -b feature/[task-name]
- Small, atomic commits. One logical change per commit.
- Commit format: type(scope): description
  feat(personality): add archetype blending logic
  test(messaging): add trigger evaluation tests
  fix(delivery): handle Twilio timeout error
  refactor(shared): use LLM provider abstraction in generator

## Working Style
- I work in 20-minute focused reps. Keep tasks completable in one rep.
- "plan this" → planning mode only, no code.
- "implement this" → TDD: write test first, then implement.
- After completing a task, tell me what to commit and the commit message.

## Feature Workflow
- Each feature is documented in docs/features/F##-feature-name.md (or R##)
- Feature index with execution order: docs/features/INDEX.md
- Each feature contains micro-tasks (~20 min each) with context pointers
- To start a task, tell Claude: "Read docs/features/F##. Working on Task N."
- Claude reads the feature doc + referenced architecture sections, then implements with TDD.

## Review Workflow
- Multi-model review system documented in docs/review/REVIEW-WORKFLOW.md
- Opus reviews: high-blast-radius tasks (template: docs/review/opus-review-brief.md)
- Codex reviews: after every feature (template: docs/review/codex-review-brief.md)
- Gemini reviews: strategic (template: docs/review/gemini-strategic-brief.md)
- Parallel message testing: ongoing (rubric: docs/review/parallel-testing-rubric.md)
- Triage outputs: docs/review/triage/
- Cumulative patterns: docs/review/patterns.md

## Reference Docs
- **Unified Roadmap: docs/unified-roadmap.md** ← START HERE for phases and milestones
- Category Architecture: docs/category-architecture.md
- JimiGPT Architecture: docs/jimigpt-architecture.md
- Message Modeling: docs/message-modeling.md
- Future Architecture: docs/future-architecture.md
- Model Resilience & Intelligence: docs/model-resilience-intelligence.md
- Foundation Per Feature: docs/foundation-per-feature.md
- Strategic Deep Dive: docs/strategic-deep-dive.md
- Feature Index: docs/features/INDEX.md
- User Testing Strategy: docs/user-testing-strategy.md
- Review Workflow: docs/review/REVIEW-WORKFLOW.md
- Customer Lens Review: docs/review/architecture-customer-lens-review.md
