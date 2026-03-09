# JimiGPT 🐾

Digital Twin for Pets — Personality-Driven Contextual Messaging

JimiGPT creates a Digital Twin of your pet that sends you text messages
throughout the day in your pet's unique personality voice. Built on the
Emotional AI Category Architecture for portability to future companion products.

## Status

🚧 **In Development** — Phase 1A: Personality Engine

## Tech Stack

- **Backend:** Python 3.12+ / FastAPI / Pydantic v2
- **Database:** Supabase (PostgreSQL + Auth)
- **LLM:** Anthropic Claude API
- **Messaging:** Twilio SMS
- **Frontend:** Next.js / TypeScript / Tailwind
- **Testing:** pytest (TDD methodology)

## Quick Start

```bash
# Clone and enter project
cd jimigpt

# Install backend dependencies
pip install -e ".[dev]"

# Copy environment variables
cp .env.example .env
# Edit .env with your API keys

# Run tests
pytest

# Start dev server
uvicorn src.main:app --reload
```

## Architecture

See `docs/category-architecture.md` for the shared Emotional AI architecture
and `docs/jimigpt-architecture.md` for JimiGPT-specific design.

## Development

See `docs/features/` for feature breakdowns with micro-tasks.
Development follows TDD with 20-minute focused reps.
