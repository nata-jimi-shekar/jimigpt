"""JimiGPT FastAPI application entry point."""

from fastapi import FastAPI

from src.api.webhooks import router as webhooks_router

app = FastAPI(
    title="JimiGPT",
    description="Digital Twin for Pets — Personality-Driven Contextual Messaging",
    version="0.1.0",
)

app.include_router(webhooks_router)


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}
