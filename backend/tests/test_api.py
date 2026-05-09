import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest_asyncio.fixture
async def ac():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c

@pytest.mark.asyncio
async def test_auth_enforcement(ac: AsyncClient):
    # Try to access candidates without token
    response = await ac.get("/candidates")
    assert response.status_code == 403

import uuid

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
