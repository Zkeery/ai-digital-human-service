"""后端第 20 阶段：缺货／到货通知多轮。"""


def _labels(body: dict) -> list[str]:
    return [item["label"] for item in body.get("quick_replies") or []]


def test_stock_clarify_then_subscribe(client):
    sid = client.post("/api/v1/sessions", json={"entry_id": "entry_pilot_001"}).json()["session_id"]
    client.put("/api/v1/config", json={"agent_enabled": False})

    t1 = client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "到货通知"}).json()
    assert t1["source"] == "stock_dialogue"
    assert t1["graphic_template_ref"] == "faq:stock_clarify"
    assert "缺货" in t1["spoken_text"]
    assert len(t1["spoken_text"]) < 40
    assert "订到货通知" in _labels(t1)
    assert len(_labels(t1)) <= 5

    t2 = client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "订到货通知"}).json()
    assert t2["graphic_template_ref"] == "faq:stock_subscribe"
    assert not t2["spoken_text"].startswith("订到货通知")


def test_stock_missed(client):
    sid = client.post("/api/v1/sessions", json={"entry_id": "entry_pilot_001"}).json()["session_id"]
    client.put("/api/v1/config", json={"agent_enabled": False})
    client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "缺货"})
    t2 = client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "订了没通知"}).json()
    assert t2["graphic_template_ref"] == "faq:stock_missed"
    assert t2["suggest_transfer_human"] is True


def test_stock_does_not_steal_price_protect(client):
    sid = client.post("/api/v1/sessions", json={"entry_id": "entry_pilot_001"}).json()["session_id"]
    client.put("/api/v1/config", json={"agent_enabled": False})
    client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "价保"})
    body = client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "缺货"}).json()
    assert body["source"] == "price_protect_dialogue"
