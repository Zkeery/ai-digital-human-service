"""后端第 10 阶段：修改收货地址多轮。"""


def _labels(body: dict) -> list[str]:
    return [item["label"] for item in body.get("quick_replies") or []]


def test_address_clarify_then_not_shipped(client):
    sid = client.post("/api/v1/sessions", json={"entry_id": "entry_pilot_001"}).json()["session_id"]
    client.put("/api/v1/config", json={"agent_enabled": False})

    t1 = client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "改地址"}).json()
    assert t1["source"] == "address_dialogue"
    assert "还没发货" in _labels(t1)

    t2 = client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "还没发货"}).json()
    assert t2["graphic_template_ref"] == "faq:address_not_shipped"
    assert "修改收货地址" in t2["spoken_text"] or "订单详情" in t2["spoken_text"]


def test_address_shipped_suggests_transfer(client):
    sid = client.post("/api/v1/sessions", json={"entry_id": "entry_pilot_001"}).json()["session_id"]
    client.put("/api/v1/config", json={"agent_enabled": False})
    client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "修改地址"})
    t2 = client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "已经发货"}).json()
    assert t2["graphic_template_ref"] == "faq:address_shipped"
    assert t2["suggest_transfer_human"] is True


def test_address_does_not_steal_return_flow(client):
    sid = client.post("/api/v1/sessions", json={"entry_id": "entry_pilot_001"}).json()["session_id"]
    client.put("/api/v1/config", json={"agent_enabled": False})
    client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "怎么退货？"})
    body = client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "改地址"}).json()
    assert body["source"] == "return_dialogue"
    assert body["graphic_template_ref"].startswith("faq:return_reason")
