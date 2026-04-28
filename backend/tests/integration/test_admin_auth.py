import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_admin_login_success(client: AsyncClient, seeded_data: dict) -> None:
    response = await client.post(
        "/admin/auth/login",
        json={
            "email": seeded_data["admin"]["email"],
            "password": seeded_data["admin"]["password"],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["token_type"] == "bearer"
    assert payload["access_token"]
    assert payload["expires_at"]


@pytest.mark.asyncio
async def test_admin_login_failure(client: AsyncClient, seeded_data: dict) -> None:
    response = await client.post(
        "/admin/auth/login",
        json={
            "email": seeded_data["admin"]["email"],
            "password": "wrong-password",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials."


@pytest.mark.asyncio
async def test_admin_auth_me(client: AsyncClient, seeded_data: dict, auth_headers) -> None:
    headers = await auth_headers(
        seeded_data["admin"]["email"],
        seeded_data["admin"]["password"],
    )

    response = await client.get("/admin/auth/me", headers=headers)

    assert response.status_code == 200
    payload = response.json()
    assert payload["email"] == seeded_data["admin"]["email"]
    assert payload["role"] == "admin"
    assert payload["zone"] is None
