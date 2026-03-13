# JimiGPT

AI companion platform creating Digital Twins for pets with personality-driven
contextual messaging. Built on the Emotional AI Category Architecture — engine
code is entity-agnostic; pet-specific logic lives in configuration only.

## Tech Stack
- Backend: Python 3.12+, FastAPI, Pydantic v2
- Database: Supabase (PostgreSQL + Auth)
- LLM: Anthropic Claude API (personality/message generation)
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
- IMPORTANT: Read docs/category-architecture.md for shared component specs.
- IMPORTANT: Read docs/jimigpt-architecture.md for product-specific specs.
- Every engine component MUST be entity-agnostic at the core.
  Pet-specific logic belongs in config/ YAML files and PetProfile extension.
  Ask yourself: "Would this work for NeuroAmigo with only config changes?"
- Four-layer personality model: Communication Style, Emotional Disposition,
  Relational Stance, Knowledge & Awareness
- Message pipeline: Trigger → Context → Generate → Quality Gate → Deliver
- Pydantic models for ALL data. No raw dicts. No Any types.

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
- Mock external services (Anthropic API, Twilio, Supabase) in unit tests.

## Git Workflow
- NEVER commit directly to main.
- Branch: git checkout -b feature/[task-name]
- Small, atomic commits. One logical change per commit.
- Commit format: type(scope): description
  feat(personality): add archetype blending logic
  test(messaging): add trigger evaluation tests
  fix(delivery): handle Twilio timeout error

## Working Style
- I work in 20-minute focused reps. Keep tasks completable in one rep.
- "plan this" → planning mode only, no code.
- "implement this" → TDD: write test first, then implement.
- After completing a task, tell me what to commit and the commit message.

## Feature Workflow
- Each feature is documented in docs/features/F##-feature-name.md
- Each feature contains micro-tasks (~20 min each) with context pointers
- To start a task, tell Claude: "Read docs/features/F##. Working on Task N."
- Claude reads the feature doc + referenced architecture sections, then implements with TDD.

## Reference Docs
- Category Architecture: docs/category-architecture.md
- JimiGPT Architecture: docs/jimigpt-architecture.md
- Message Modeling: docs/message-modeling.md
- Features: docs/features/
- User Testing Strategy: docs/user-testing-strategy.md
- Current sprint: docs/tasks/current-sprint.md
