"""Test user endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_me_unauthorized(client: AsyncClient):
    """Test /me without token."""
    response = await client.get("/api/v1/users/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me_success(client: AsyncClient):
    """Test /me with valid token."""
    # Register and get token
    reg = await client.post("/api/v1/auth/register", json={
        "username": "meuser",
        "email": "me@example.com",
        "password": "password123"
    })
    token = reg.json()["access_token"]
    
    headers = {"Authorization": f"Bearer {token}"}
    response = await client.get("/api/v1/users/me", headers=headers)
    assert response.status_code == 200
    assert response.json()["username"] == "meuser"
