"""Tests for health record CRUD endpoints."""

import pytest


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_health_record(auth_client):
    """POST /api/health/records with height/weight creates a record with BMI."""
    resp = await auth_client.post(
        "/api/health/records",
        json={
            "height": 175.0,
            "weight": 70.0,
            "blood_pressure_systolic": 120,
            "blood_pressure_diastolic": 80,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["height"] == 175.0
    assert data["weight"] == 70.0
    assert data["bmi"] is not None
    assert data["bmi"] > 0


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_record_generates_analysis(auth_client):
    """Creating a health record with height/weight should also create an analysis."""
    await auth_client.post(
        "/api/health/records",
        json={"height": 170.0, "weight": 65.0},
    )
    resp = await auth_client.get("/api/health/analysis/latest")
    assert resp.status_code == 200
    data = resp.json()
    assert data["bmi_status"] is not None


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_records_list(auth_client):
    """GET /api/health/records returns user's records."""
    await auth_client.post(
        "/api/health/records",
        json={"height": 180.0, "weight": 75.0},
    )
    resp = await auth_client.get("/api/health/records")
    assert resp.status_code == 200
    records = resp.json()
    assert isinstance(records, list)
    assert len(records) >= 1


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_record_not_found(auth_client):
    """GET /api/health/records/9999 returns 404."""
    resp = await auth_client.get("/api/health/records/9999")
    assert resp.status_code == 404


@pytest.mark.asyncio
@pytest.mark.integration
async def test_delete_record(auth_client):
    """DELETE /api/health/records/{id} removes the record."""
    create_resp = await auth_client.post(
        "/api/health/records",
        json={"height": 165.0, "weight": 55.0},
    )
    record_id = create_resp.json()["id"]
    resp = await auth_client.delete(f"/api/health/records/{record_id}")
    assert resp.status_code == 200
    assert resp.json()["deleted_id"] == record_id

    get_resp = await auth_client.get(f"/api/health/records/{record_id}")
    assert get_resp.status_code == 404
