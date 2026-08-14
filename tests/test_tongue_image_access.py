"""Security regression tests for authenticated tongue image access (S-N1)."""

from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

import models
from auth import create_access_token, get_password_hash


def _create_diagnosis(db, user_id: int, image_path: Path) -> models.TongueDiagnosis:
    diagnosis = models.TongueDiagnosis(
        user_id=user_id,
        image_path=str(image_path),
        analysis_status="completed",
    )
    db.add(diagnosis)
    db.flush()
    return diagnosis


@pytest.mark.asyncio
async def test_tongue_image_requires_owner_authentication(app, db, client, anon_client, tmp_path, monkeypatch):
    from services import tongue_service

    monkeypatch.setattr(tongue_service, "UPLOAD_DIR", str(tmp_path))
    image_path = tmp_path / "owned.png"
    image_path.write_bytes(b"owned-image")
    # Obtain the fixture user from the database instead of depending on token internals.
    owner = db.query(models.User).filter_by(name="testuser").one()
    diagnosis = _create_diagnosis(db, owner.id, image_path)

    anonymous = await anon_client.get(f"/api/tongue/image/{diagnosis.id}")
    assert anonymous.status_code == 401

    owned = await client.get(f"/api/tongue/image/{diagnosis.id}")
    assert owned.status_code == 200
    assert owned.content == b"owned-image"

    other_user = models.User(
        name="other-user",
        password_hash=get_password_hash("testpass123"),
        invite_code="health2026",
    )
    db.add(other_user)
    db.flush()
    other_token = create_access_token(data={"sub": str(other_user.id)})
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as other_client:
        other_client.headers["Authorization"] = f"Bearer {other_token}"
        forbidden = await other_client.get(f"/api/tongue/image/{diagnosis.id}")

    assert forbidden.status_code == 404


@pytest.mark.asyncio
async def test_uploaded_files_are_not_publicly_mounted(app, anon_client):
    assert not any(getattr(route, "path", None) == "/uploads" for route in app.routes)

    image_path = Path("uploads") / "tongue" / "security-regression.png"
    image_path.parent.mkdir(parents=True, exist_ok=True)
    image_path.write_bytes(b"private-image-bytes")
    try:
        response = await anon_client.get("/uploads/tongue/security-regression.png")
    finally:
        image_path.unlink(missing_ok=True)

    assert response.status_code != 200
    assert response.content != b"private-image-bytes"
    assert "blob:" in response.headers["content-security-policy"]


@pytest.mark.asyncio
async def test_tongue_image_rejects_path_outside_upload_directory(app, db, client, tmp_path):
    owner = db.query(models.User).filter_by(name="testuser").one()
    outside_file = tmp_path / "outside.png"
    outside_file.write_bytes(b"must-not-leak")
    diagnosis = _create_diagnosis(db, owner.id, outside_file)

    response = await client.get(f"/api/tongue/image/{diagnosis.id}")

    assert response.status_code == 404
