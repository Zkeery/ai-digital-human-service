"""后端第 9 阶段：发票开票咨询多轮。"""


def _labels(body: dict) -> list[str]:
    return [item["label"] for item in body.get("quick_replies") or []]


def test_invoice_clarify_then_electronic(client):
    sid = client.post("/api/v1/sessions", json={"entry_id": "entry_pilot_001"}).json()["session_id"]
    client.put("/api/v1/config", json={"agent_enabled": False})

    t1 = client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "开发票"}).json()
    assert t1["source"] == "invoice_dialogue"
    assert "电子发票" in _labels(t1)

    t2 = client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "电子发票"}).json()
    assert t2["graphic_template_ref"] == "faq:invoice_electronic"
    assert "订单详情" in t2["spoken_text"]
    assert t2.get("quick_replies") == []


def test_invoice_reissue_suggests_transfer(client):
    sid = client.post("/api/v1/sessions", json={"entry_id": "entry_pilot_001"}).json()["session_id"]
    client.put("/api/v1/config", json={"agent_enabled": False})
    client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "发票"})
    t2 = client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "重开改抬头"}).json()
    assert t2["graphic_template_ref"] == "faq:invoice_reissue"
    assert t2["suggest_transfer_human"] is True


def test_invoice_does_not_steal_return_flow(client):
    sid = client.post("/api/v1/sessions", json={"entry_id": "entry_pilot_001"}).json()["session_id"]
    client.put("/api/v1/config", json={"agent_enabled": False})
    client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "怎么退货？"})
    body = client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "开发票"}).json()
    assert body["source"] == "return_dialogue"
    assert body["graphic_template_ref"].startswith("faq:return_reason")
