"""后端第 13 阶段：电商投诉样例（已归档，不再作为现行需求）。"""

import pytest

pytestmark = pytest.mark.skip(reason="电商投诉样例已归档；现行见 test_stage28_complaint")


def _labels(body: dict) -> list[str]:
    return [item["label"] for item in body.get("quick_replies") or []]


def test_complaint_clarify_then_logistics(client):
    sid = client.post("/api/v1/sessions", json={"entry_id": "entry_pilot_001"}).json()["session_id"]
    client.put("/api/v1/config", json={"agent_enabled": False})
    t1 = client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "我要投诉"}).json()
    assert t1["source"] == "complaint_dialogue"
