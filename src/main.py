"""JimiGPT FastAPI application entry point."""

from fastapi import FastAPI

app = FastAPI(
    title="JimiGPT",
    description="Digital Twin for Pets — Personality-Driven Contextual Messaging",
    version="0.1.0",
)


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}
