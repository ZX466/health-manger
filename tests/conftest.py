"""Shared test fixtures for the health system test suite."""

import os

os.environ.setdefault("SECRET_KEY", "test-secret-key-for-testing-only")

from contextlib import asynccontextmanager

import pytest
import pytest_asyncio
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from httpx import ASGITransport, AsyncClient

from database import Base, get_db


@pytest.fixture(scope="session")
def engine():
    """Create an in-memory SQLite engine for all tests."""
    import models  # noqa: F401 - register model tables with Base.metadata
    import chat_session  # noqa: F401

    eng = create_engine(
        "sqlite:///:memory:", echo=False,
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=eng)
    yield eng
    eng.dispose()


@pytest.fixture()
def db(engine):
    """Provide a transactional database session that rolls back after each test."""
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)

    from main import app
    app.dependency_overrides[get_db] = lambda: session

    yield session

    session.close()
    transaction.rollback()
    connection.close()
    app.dependency_overrides.clear()


@pytest.fixture()
def app(engine):
    """Provide a FastAPI app instance with a no-op lifespan."""
    from main import app as real_app

    @asynccontextmanager
    async def noop_lifespan(app):
        yield

    real_app.router.lifespan_context = noop_lifespan
    return real_app


@pytest_asyncio.fixture()
async def client(app, db):
    """Provide an async HTTP test client."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


@pytest_asyncio.fixture()
async def auth_client(app, db):
    """Provide an authenticated async HTTP test client."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        register_resp = await ac.post(
            "/api/auth/register",
            json={
                "name": "testuser",
                "password": "testpass123",
                "invite_code": "health2026",
            },
        )
        assert register_resp.status_code == 200, register_resp.text

        login_resp = await ac.post(
            "/api/auth/login",
            data={"username": "testuser", "password": "testpass123"},
        )
        assert login_resp.status_code == 200, login_resp.text
        token = login_resp.json()["access_token"]
        ac.headers["Authorization"] = f"Bearer {token}"
        yield ac
