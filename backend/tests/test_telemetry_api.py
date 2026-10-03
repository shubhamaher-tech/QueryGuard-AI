import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_telemetry_pipeline_api_flow(client):
    # 1. Trigger collection
    res_collect = client.post("/api/telemetry/collect")
    assert res_collect.status_code == 200
    collect_data = res_collect.json()
    assert collect_data["status"] == "COMPLETED"
    assert collect_data["privacy_check_passed"] is True
    assert collect_data["events_created"] >= 1
    assert "No raw rows" in collect_data["privacy_status"]

    # Strict Privacy Check on Response Content
    response_str = res_collect.text.lower()
    assert "transactions" not in response_str
    assert "order_items" not in response_str
    assert "customers" not in response_str

    # 2. Get Telemetry Status
    res_status = client.get("/api/telemetry/status")
    assert res_status.status_code == 200
    status_data = res_status.json()
    assert status_data["status"] == "COMPLETED"
    assert status_data["privacy_check_passed"] is True
    assert status_data["events_created"] >= 1

    # 3. List Telemetry Events
    res_events = client.get("/api/telemetry/events")
    assert res_events.status_code == 200
    events = res_events.json()
    assert len(events) >= 1

    target_event_id = events[0]["id"]
    assert target_event_id.startswith("TE-")
    assert events[0]["privacy_check_passed"] is True
    assert "TBL_" in events[0]["masked_query_template"]

    # 4. Get Event Detail
    res_detail = client.get(f"/api/telemetry/events/{target_event_id}")
    assert res_detail.status_code == 200
    detail = res_detail.json()
    assert detail["id"] == target_event_id
    assert len(detail["plan_nodes"]) > 0
    assert "honesty_label" in detail
    assert "Rule-based plan graph analysis; GNN/RL-ready architecture." in detail["honesty_label"]

    # Detail response must also be completely free of plaintext identifiers
    detail_str = res_detail.text.lower()
    assert "transactions" not in detail_str
    assert "customers" not in detail_str
