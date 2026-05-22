"""Test auth endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_user(client: AsyncClient):
    """Test user registration."""
    payload = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "strongpassword123",
    }
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["user"]["username"] == "testuser"


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient):
    """Test duplicate email registration."""
    payload = {
        "username": "testuser2",
        "email": "test@example.com", # Same as above
        "password": "strongpassword123",
    }
    await client.post("/api/v1/auth/register", json=payload)
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    """Test successful login."""
    # Register first
    await client.post("/api/v1/auth/register", json={
        "username": "loginuser",
        "email": "login@example.com",
        "password": "password123"
    })
    
    # Login
    response = await client.post("/api/v1/auth/login", json={
        "email": "login@example.com",
        "password": "password123"
    })
    assert response.status_code == 200
    assert "access_token" in response.json()
