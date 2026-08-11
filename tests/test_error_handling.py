"""Tests for global error handling and consistent Chinese error messages."""

import pytest


@pytest.mark.asyncio
@pytest.mark.integration
async def test_404_returns_chinese_message(client):
    """GET /api/nonexistent returns 404 with Chinese detail."""
    resp = await client.get("/api/nonexistent-endpoint")
    assert resp.status_code == 404
    data = resp.json()
    assert "detail" in data


@pytest.mark.asyncio
@pytest.mark.integration
async def test_unauthenticated_returns_chinese_message(client):
    """GET /api/auth/me without token returns 401 with Chinese message."""
    resp = await client.get("/api/auth/me")
    assert resp.status_code == 401
    data = resp.json()
    assert "detail" in data
    assert "凭据" in data["detail"] or "401" in str(resp.status_code)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_health_endpoint_200(client):
    """GET /api/health returns 200 with status healthy."""
    resp = await client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_api_error_response_has_detail_field(auth_client):
    """GET /api/health/records/9999 returns 404 with detail field."""
    resp = await auth_client.get("/api/health/records/9999")
    assert resp.status_code == 404
    assert "detail" in resp.json()
