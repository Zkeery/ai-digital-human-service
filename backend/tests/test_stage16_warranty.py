"""后端第 16 阶段：保修质保咨询多轮。"""


def _labels(body: dict) -> list[str]:
    return [item["label"] for item in body.get("quick_replies") or []]


def test_warranty_clarify_then_apply(client):
    sid = client.post("/api/v1/sessions", json={"entry_id": "entry_pilot_001"}).json()["session_id"]
    client.put("/api/v1/config", json={"agent_enabled": False})

    t1 = client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "保修"}).json()
    assert t1["source"] == "warranty_dialogue"
    assert t1["graphic_template_ref"] == "faq:warranty_clarify"
    assert "保修" in t1["spoken_text"]
    assert len(t1["spoken_text"]) < 40
    assert "怎么申请" in _labels(t1)

    t2 = client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "怎么申请"}).json()
    assert t2["graphic_template_ref"] == "faq:warranty_apply"
    assert not t2["spoken_text"].startswith("怎么申请")
    assert t2["suggest_transfer_human"] is True


def test_warranty_coverage(client):
    sid = client.post("/api/v1/sessions", json={"entry_id": "entry_pilot_001"}).json()["session_id"]
    client.put("/api/v1/config", json={"agent_enabled": False})
    client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "保修"})
    t2 = client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "在不在保"}).json()
    assert t2["graphic_template_ref"] == "faq:warranty_coverage"


def test_warranty_does_not_steal_coupon(client):
    sid = client.post("/api/v1/sessions", json={"entry_id": "entry_pilot_001"}).json()["session_id"]
    client.put("/api/v1/config", json={"agent_enabled": False})
    client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "优惠券"})
    body = client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "保修"}).json()
    assert body["source"] == "coupon_dialogue"
