"""Tests for the health check endpoint."""

import pytest


@pytest.mark.asyncio
@pytest.mark.integration
async def test_health_endpoint(client):
    """Verify /api/health returns 200 with healthy status."""
    response = await client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}
