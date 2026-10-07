"""后端第 21 阶段：账户／余额／流水指引。"""


def _labels(body: dict) -> list[str]:
    return [item["label"] for item in body.get("quick_replies") or []]


def test_account_clarify_then_balance(client):
    sid = client.post("/api/v1/sessions", json={"entry_id": "entry_pilot_001"}).json()["session_id"]
    client.put("/api/v1/config", json={"agent_enabled": False})

    t1 = client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "查余额"}).json()
    assert t1["source"] == "account_dialogue"
    assert t1["graphic_template_ref"] == "faq:account_balance"
    assert "您还想咨询" in t1["spoken_text"]
    assert "查流水" in _labels(t1)


def test_account_mismatch(client):
    sid = client.post("/api/v1/sessions", json={"entry_id": "entry_pilot_001"}).json()["session_id"]
    client.put("/api/v1/config", json={"agent_enabled": False})
    client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "流水"})
    t2 = client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "余额对不上"}).json()
    assert t2["graphic_template_ref"] == "faq:account_mismatch"
    assert t2["suggest_transfer_human"] is True
    assert "您还想咨询" in t2["spoken_text"]


def test_ecommerce_return_no_longer_routed(client):
    sid = client.post("/api/v1/sessions", json={"entry_id": "entry_pilot_001"}).json()["session_id"]
    client.put("/api/v1/config", json={"agent_enabled": False})
    body = client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "怎么退货？"}).json()
    assert body["source"] != "return_dialogue"
    assert body["source"] == "offtopic_rule"
    assert body["graphic_template_ref"] == "faq:offtopic_ecommerce"
    assert "零售金融" in body["spoken_text"]
    assert "网购售后" in body["spoken_text"] or "不办理" in body["spoken_text"]
