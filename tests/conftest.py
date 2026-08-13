"""Shared test fixtures for the health system test suite."""

import os

os.environ.setdefault("SECRET_KEY", "test-secret-key-for-testing-only")
os.environ.setdefault("INVITE_CODES", "health2026")

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


@pytest.fixture()
def test_user(db):
    """Create a test user for authenticated requests (no API round-trip).

    用 flush 而非 commit：避免用户跨测试持久化到共享内存库，与 users.name
    唯一约束冲突（S13 后重复 testuser 会触发 IntegrityError）。
    """
    import models
    from auth import get_password_hash

    user = models.User(
        name="testuser",
        password_hash=get_password_hash("testpass123"),
        invite_code="health2026",
    )
    db.add(user)
    db.flush()
    db.refresh(user)
    return user


@pytest.fixture()
def auth_token(test_user):
    """Mint a JWT for the test user. Test token is configured here in conftest."""
    from auth import create_access_token

    return create_access_token(data={"sub": str(test_user.id)})


@pytest_asyncio.fixture()
async def client(app, db, auth_token):
    """Provide an authenticated async HTTP test client (token attached here)."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        ac.headers["Authorization"] = f"Bearer {auth_token}"
        yield ac


@pytest_asyncio.fixture()
async def anon_client(app, db):
    """Provide an unauthenticated async HTTP test client."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac
