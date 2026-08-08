import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

# This tells pytest to run these tests asynchronously
pytestmark = pytest.mark.asyncio


async def test_health_check():
    """Test that the health endpoint returns a 200 OK."""
    # We use ASGITransport to test FastAPI directly without running a real server
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/health")

        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


async def test_create_api_key():
    """Test that the admin endpoint successfully creates a new API key."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        payload = {"name": "Test Key", "rate_limit_requests_per_minute": 10}
        response = await client.post("/admin/keys", json=payload)

        assert response.status_code == 200
        data = response.json()

        assert data["name"] == "Test Key"
        # The key should start with our gateway prefix
        assert data["api_key"].startswith("gw-")
        assert "message" in data
