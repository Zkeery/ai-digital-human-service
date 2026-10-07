"""后端第 22 阶段：转账失败／未到账多轮。"""


def _labels(body: dict) -> list[str]:
    return [item["label"] for item in body.get("quick_replies") or []]


def test_transfer_fail_direct(client):
    sid = client.post("/api/v1/sessions", json={"entry_id": "entry_pilot_001"}).json()["session_id"]
    client.put("/api/v1/config", json={"agent_enabled": False})
    t1 = client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "转账失败"}).json()
    assert t1["source"] == "transfer_dialogue"
    assert t1["graphic_template_ref"] == "faq:transfer_fail"
    assert not t1["spoken_text"].startswith("转账失败")


def test_transfer_clarify_then_missing(client):
    sid = client.post("/api/v1/sessions", json={"entry_id": "entry_pilot_001"}).json()["session_id"]
    client.put("/api/v1/config", json={"agent_enabled": False})
    t1 = client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "转账"}).json()
    assert t1["graphic_template_ref"] == "faq:transfer_clarify"
    assert "怎么转账" in _labels(t1)
    assert "对方没收到" in _labels(t1)
    assert len(_labels(t1)) <= 5
    t2 = client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "对方没收到"}).json()
    assert t2["graphic_template_ref"] == "faq:transfer_missing"
    assert t2["suggest_transfer_human"] is True


def test_transfer_howto_intent(client):
    sid = client.post("/api/v1/sessions", json={"entry_id": "entry_pilot_001"}).json()["session_id"]
    client.put("/api/v1/config", json={"agent_enabled": False})
    body = client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "我想转账"}).json()
    assert body["graphic_template_ref"] == "faq:transfer_howto"
    assert "转账汇款" in body["spoken_text"] or "「转账」" in body["spoken_text"]
    assert "不能代" in body["spoken_text"]
    assert "请问是转账失败" not in body["spoken_text"]


def test_transfer_can_switch_from_account(client):
    sid = client.post("/api/v1/sessions", json={"entry_id": "entry_pilot_001"}).json()["session_id"]
    client.put("/api/v1/config", json={"agent_enabled": False})
    client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "流水"})
    body = client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "转账失败"}).json()
    assert body["source"] == "transfer_dialogue"
