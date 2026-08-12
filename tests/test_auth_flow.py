"""Tests for authentication flow: register, login, me."""

import pytest


@pytest.mark.asyncio
@pytest.mark.integration
async def test_register_success(client):
    """Register with valid invite code returns 200."""
    resp = await client.post(
        "/api/auth/register",
        json={
            "name": "newuser",
            "password": "password123",
            "invite_code": "health2026",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "newuser"
    assert "id" in data


@pytest.mark.asyncio
@pytest.mark.integration
async def test_register_duplicate_name(client):
    """Registering the same username twice returns 400."""
    payload = {
        "name": "dupuser",
        "password": "password123",
        "invite_code": "health2026",
    }
    await client.post("/api/auth/register", json=payload)
    resp = await client.post("/api/auth/register", json=payload)
    assert resp.status_code == 400
    assert "已存在" in resp.json()["detail"]


@pytest.mark.asyncio
@pytest.mark.integration
async def test_register_invalid_invite_code(client):
    """Register with invalid invite code returns 400."""
    resp = await client.post(
        "/api/auth/register",
        json={
            "name": "badcodeuser",
            "password": "password123",
            "invite_code": "INVALID_CODE",
        },
    )
    assert resp.status_code == 400
    assert "邀请码" in resp.json()["detail"]


@pytest.mark.asyncio
@pytest.mark.integration
async def test_login_success(client):
    """Login after registration returns a token."""
    await client.post(
        "/api/auth/register",
        json={
            "name": "loginuser",
            "password": "password123",
            "invite_code": "health2026",
        },
    )
    resp = await client.post(
        "/api/auth/login",
        data={"username": "loginuser", "password": "password123"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_login_wrong_password(client):
    """Login with wrong password returns 401."""
    await client.post(
        "/api/auth/register",
        json={
            "name": "wrongpassuser",
            "password": "password123",
            "invite_code": "health2026",
        },
    )
    resp = await client.post(
        "/api/auth/login",
        data={"username": "wrongpassuser", "password": "wrongpassword"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
@pytest.mark.integration
async def test_me_endpoint_authenticated(client):
    """GET /api/auth/me with valid token returns user data."""
    resp = await client.get("/api/auth/me")
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "testuser"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_me_endpoint_unauthenticated(anon_client):
    """GET /api/auth/me without token returns 401."""
    resp = await anon_client.get("/api/auth/me")
    assert resp.status_code == 401
