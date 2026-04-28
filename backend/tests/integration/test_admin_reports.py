import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_rbac_admin_sees_all_reports(client: AsyncClient, seeded_data: dict, auth_headers) -> None:
    headers = await auth_headers(
        seeded_data["admin"]["email"],
        seeded_data["admin"]["password"],
    )

    response = await client.get("/admin/reports", headers=headers)

    assert response.status_code == 200
    payload = response.json()
    assert payload["page"]["total_items"] == 5
    assert len(payload["items"]) == 5


@pytest.mark.asyncio
async def test_rbac_resolver_sees_only_own_zone(client: AsyncClient, seeded_data: dict, auth_headers) -> None:
    headers = await auth_headers(
        seeded_data["resolver"]["email"],
        seeded_data["resolver"]["password"],
    )

    response = await client.get("/admin/reports", headers=headers)

    assert response.status_code == 200
    payload = response.json()
    assert payload["page"]["total_items"] == 3
    assert {item["zone"] for item in payload["items"]} == {"process"}


@pytest.mark.asyncio
async def test_rbac_resolver_cannot_access_foreign_zone_report(
    client: AsyncClient,
    seeded_data: dict,
    auth_headers,
) -> None:
    headers = await auth_headers(
        seeded_data["resolver"]["email"],
        seeded_data["resolver"]["password"],
    )

    response = await client.get(
        f"/admin/reports/{seeded_data['report_ids']['finance_closed']}",
        headers=headers,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Report not found."


@pytest.mark.asyncio
async def test_reports_list_filters(client: AsyncClient, seeded_data: dict, auth_headers) -> None:
    headers = await auth_headers(
        seeded_data["admin"]["email"],
        seeded_data["admin"]["password"],
    )

    response = await client.get(
        "/admin/reports",
        params={"category": "safety", "zone": "finance", "status": "closed"},
        headers=headers,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["page"]["total_items"] == 1
    assert payload["items"][0]["public_number"] == "AERO-0004"


@pytest.mark.asyncio
async def test_reports_list_pagination(client: AsyncClient, seeded_data: dict, auth_headers) -> None:
    headers = await auth_headers(
        seeded_data["admin"]["email"],
        seeded_data["admin"]["password"],
    )

    response = await client.get(
        "/admin/reports",
        params={"page": 2, "page_size": 2},
        headers=headers,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["page"] == {
        "page": 2,
        "page_size": 2,
        "total_items": 5,
        "total_pages": 3,
    }
    assert len(payload["items"]) == 2


@pytest.mark.asyncio
async def test_report_card_returns_detail(client: AsyncClient, seeded_data: dict, auth_headers) -> None:
    headers = await auth_headers(
        seeded_data["admin"]["email"],
        seeded_data["admin"]["password"],
    )

    response = await client.get(
        f"/admin/reports/{seeded_data['report_ids']['process_open']}",
        headers=headers,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["public_number"] == "AERO-0001"
    assert payload["author"]["telegram_username"] == "open_author"
    assert len(payload["attachments"]) == 1


@pytest.mark.asyncio
async def test_anonymous_report_hides_author_in_list_and_detail(
    client: AsyncClient,
    seeded_data: dict,
    auth_headers,
) -> None:
    headers = await auth_headers(
        seeded_data["admin"]["email"],
        seeded_data["admin"]["password"],
    )

    list_response = await client.get(
        "/admin/reports",
        params={"submit_mode": "anonymous"},
        headers=headers,
    )
    assert list_response.status_code == 200
    list_payload = list_response.json()
    assert list_payload["page"]["total_items"] == 1
    assert list_payload["items"][0]["author"] is None

    detail_response = await client.get(
        f"/admin/reports/{seeded_data['report_ids']['process_anonymous']}",
        headers=headers,
    )
    assert detail_response.status_code == 200
    assert detail_response.json()["author"] is None


@pytest.mark.asyncio
async def test_report_status_transitions_and_closed_at(
    client: AsyncClient,
    seeded_data: dict,
    auth_headers,
) -> None:
    headers = await auth_headers(
        seeded_data["admin"]["email"],
        seeded_data["admin"]["password"],
    )
    report_id = seeded_data["report_ids"]["process_open"]

    to_in_progress = await client.patch(
        f"/admin/reports/{report_id}/status",
        json={"status": "in_progress"},
        headers=headers,
    )
    assert to_in_progress.status_code == 200
    first_payload = to_in_progress.json()
    assert first_payload["status"] == "in_progress"
    assert first_payload["closed_at"] is None

    to_closed = await client.patch(
        f"/admin/reports/{report_id}/status",
        json={"status": "closed"},
        headers=headers,
    )
    assert to_closed.status_code == 200
    second_payload = to_closed.json()
    assert second_payload["status"] == "closed"
    assert second_payload["closed_at"] is not None
