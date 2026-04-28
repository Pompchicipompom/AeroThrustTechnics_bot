import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_admin_analytics_overview(client: AsyncClient, seeded_data: dict, auth_headers) -> None:
    headers = await auth_headers(
        seeded_data["admin"]["email"],
        seeded_data["admin"]["password"],
    )

    response = await client.get("/admin/analytics/overview", headers=headers)

    assert response.status_code == 200
    payload = response.json()

    assert payload["total_reports"] == 5
    assert payload["anonymous_reports"] == 1
    assert payload["open_reports"] == 4
    assert payload["anonymous_share"] == pytest.approx(0.2)
    assert payload["open_share"] == pytest.approx(0.8)
    assert payload["avg_hours_to_close"] is not None

    by_zone = {item["key"]: item["count"] for item in payload["by_zone"]}
    assert by_zone["process"] == 3
    assert by_zone["finance"] == 2


@pytest.mark.asyncio
async def test_admin_analytics_dynamics(client: AsyncClient, seeded_data: dict, auth_headers) -> None:
    headers = await auth_headers(
        seeded_data["admin"]["email"],
        seeded_data["admin"]["password"],
    )

    response = await client.get(
        "/admin/analytics/dynamics",
        params={"granularity": "day"},
        headers=headers,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["granularity"] == "day"
    assert payload["points"]
    assert sum(point["count"] for point in payload["points"]) == 5
