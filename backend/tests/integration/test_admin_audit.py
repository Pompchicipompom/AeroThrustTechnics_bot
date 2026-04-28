import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_audit_log_records_report_view(client: AsyncClient, seeded_data: dict, auth_headers) -> None:
    headers = await auth_headers(
        seeded_data["admin"]["email"],
        seeded_data["admin"]["password"],
    )
    report_id = seeded_data["report_ids"]["process_open"]

    view_response = await client.get(f"/admin/reports/{report_id}", headers=headers)
    assert view_response.status_code == 200

    audit_response = await client.get(
        "/admin/audit-logs",
        params={"action": "report_viewed", "entity_type": "report"},
        headers=headers,
    )
    assert audit_response.status_code == 200

    payload = audit_response.json()
    assert payload["page"]["total_items"] == 1
    item = payload["items"][0]
    assert item["entity_id"] == report_id
    assert item["action"] == "report_viewed"


@pytest.mark.asyncio
async def test_audit_log_records_status_change(client: AsyncClient, seeded_data: dict, auth_headers) -> None:
    headers = await auth_headers(
        seeded_data["admin"]["email"],
        seeded_data["admin"]["password"],
    )
    report_id = seeded_data["report_ids"]["process_open"]

    patch_response = await client.patch(
        f"/admin/reports/{report_id}/status",
        json={"status": "in_progress"},
        headers=headers,
    )
    assert patch_response.status_code == 200

    audit_response = await client.get(
        "/admin/audit-logs",
        params={"action": "status_changed", "entity_type": "report"},
        headers=headers,
    )
    assert audit_response.status_code == 200

    payload = audit_response.json()
    assert payload["page"]["total_items"] == 1
    item = payload["items"][0]
    assert item["entity_id"] == report_id
    assert item["action"] == "status_changed"
    assert item["payload_json"]["from_status"] == "new"
    assert item["payload_json"]["to_status"] == "in_progress"
