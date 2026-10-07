"""后端第 18 阶段：价保咨询多轮。"""


def _labels(body: dict) -> list[str]:
    return [item["label"] for item in body.get("quick_replies") or []]


def test_price_protect_clarify_then_apply(client):
    sid = client.post("/api/v1/sessions", json={"entry_id": "entry_pilot_001"}).json()["session_id"]
    client.put("/api/v1/config", json={"agent_enabled": False})

    t1 = client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "价保"}).json()
    assert t1["source"] == "price_protect_dialogue"
    assert t1["graphic_template_ref"] == "faq:price_protect_clarify"
    assert "价保" in t1["spoken_text"]
    assert len(t1["spoken_text"]) < 45
    assert "怎么申请" in _labels(t1)

    t2 = client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "怎么申请"}).json()
    assert t2["graphic_template_ref"] == "faq:price_protect_apply"
    assert not t2["spoken_text"].startswith("怎么申请")


def test_price_protect_pending(client):
    sid = client.post("/api/v1/sessions", json={"entry_id": "entry_pilot_001"}).json()["session_id"]
    client.put("/api/v1/config", json={"agent_enabled": False})
    client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "价保"})
    t2 = client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "差价没到"}).json()
    assert t2["graphic_template_ref"] == "faq:price_protect_pending"
    assert t2["suggest_transfer_human"] is True
    assert not t2["spoken_text"].startswith("差价没到")


def test_price_protect_does_not_steal_points(client):
    sid = client.post("/api/v1/sessions", json={"entry_id": "entry_pilot_001"}).json()["session_id"]
    client.put("/api/v1/config", json={"agent_enabled": False})
    client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "会员积分"})
    body = client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "价保"}).json()
    assert body["source"] == "points_dialogue"
