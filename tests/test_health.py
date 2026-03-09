"""Tests for the health check endpoint."""

from httpx import ASGITransport, AsyncClient

from src.main import app


async def test_health_check_returns_200() -> None:
    """Health endpoint should return 200 OK."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200


async def test_health_check_returns_ok_status() -> None:
    """Health endpoint should return {"status": "ok"}."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
    assert response.json() == {"status": "ok"}


async def test_health_check_content_type() -> None:
    """Health endpoint should return JSON."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
    assert "application/json" in response.headers["content-type"]
