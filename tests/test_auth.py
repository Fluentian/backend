"""Test auth endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_and_verify_user(client: AsyncClient):
    """Test user registration and subsequent email verification."""
    payload = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "strongpassword123",
    }
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    reg_data = response.json()
    assert reg_data["message"] == "Verification code sent to your email"
    assert "detail" in reg_data  # Holds the OTP in testing/debug mode
    otp = reg_data["detail"]

    # Verify email
    verify_payload = {
        "email": "test@example.com",
        "otp": otp,
    }
    verify_res = await client.post("/api/v1/auth/verify-email", json=verify_payload)
    assert verify_res.status_code == 200
    data = verify_res.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["user"]["username"] == "testuser"


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient):
    """Test duplicate email registration."""
    payload = {
        "username": "testuser2",
        "email": "test@example.com",
        "password": "strongpassword123",
    }
    await client.post("/api/v1/auth/register", json=payload)
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_login_unverified_sends_new_otp(client: AsyncClient):
    """Test login attempt before verification fails and triggers new OTP."""
    # Register first
    await client.post("/api/v1/auth/register", json={
        "username": "unverifieduser",
        "email": "unverified@example.com",
        "password": "password123"
    })

    # Try login without verification
    login_res = await client.post("/api/v1/auth/login", json={
        "email": "unverified@example.com",
        "password": "password123"
    })
    assert login_res.status_code == 401
    login_data = login_res.json()
    assert login_data["message"] == "Email not verified"
    assert login_data["detail"] == "unverified@example.com"


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    """Test successful login after verification."""
    # Register
    reg_response = await client.post("/api/v1/auth/register", json={
        "username": "loginuser",
        "email": "login@example.com",
        "password": "password123"
    })
    otp = reg_response.json()["detail"]

    # Verify
    await client.post("/api/v1/auth/verify-email", json={
        "email": "login@example.com",
        "otp": otp
    })
    
    # Login
    response = await client.post("/api/v1/auth/login", json={
        "email": "login@example.com",
        "password": "password123"
    })
    assert response.status_code == 200
    assert "access_token" in response.json()
