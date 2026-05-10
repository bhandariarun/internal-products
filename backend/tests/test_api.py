import os
import sys
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
import uuid

# Ensure backend root is importable when running tests from backend/tests
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from app.main import app
from app.database import engine, Base

@pytest_asyncio.fixture(scope="session", autouse=True)
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest_asyncio.fixture
async def ac():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c

@pytest.mark.asyncio
async def test_auth_enforcement(ac: AsyncClient):
    # Try to access candidates without token
    response = await ac.get("/candidates")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_register_and_login(ac: AsyncClient):
    unique_email = f"test_{uuid.uuid4()}@techkraft.com"
    # Register
    reg_res = await ac.post("/auth/register", json={
        "full_name": "Test User",
        "email": unique_email,
        "password": "password123",
        "role": "admin" # The API should ignore this and force "reviewer"
    })
    assert reg_res.status_code == 201
    assert reg_res.json()["role"] == "reviewer"

    # Login
    login_res = await ac.post("/auth/login", data={
        "username": unique_email,
        "password": "password123"
    })
    assert login_res.status_code == 200
    assert "access_token" in login_res.json()


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
