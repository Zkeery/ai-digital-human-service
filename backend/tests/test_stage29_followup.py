"""后端第 29 阶段：早期金融场景答完追问统一。"""


def _labels(body: dict) -> list[str]:
    return [item["label"] for item in body.get("quick_replies") or []]


def test_account_follow_up_keeps_chips(client):
    sid = client.post("/api/v1/sessions", json={"entry_id": "entry_pilot_001"}).json()["session_id"]
    client.put("/api/v1/config", json={"agent_enabled": False})
    t1 = client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "查余额"}).json()
    assert t1["graphic_template_ref"] == "faq:account_balance"
    assert "您还想咨询" in t1["spoken_text"]
    assert "查流水" in _labels(t1)
    assert "余额对不上" in _labels(t1)
    assert "查余额" not in _labels(t1)


def test_credit_follow_up_keeps_chips(client):
    sid = client.post("/api/v1/sessions", json={"entry_id": "entry_pilot_001"}).json()["session_id"]
    client.put("/api/v1/config", json={"agent_enabled": False})
    client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "信用卡"})
    t2 = client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "查额度"}).json()
    assert t2["graphic_template_ref"] == "faq:credit_limit"
    assert "您还想咨询" in t2["spoken_text"]
    assert "还款与账单" in _labels(t2)
    assert "申请提额" in _labels(t2)
    assert "查额度" not in _labels(t2)


def test_transfer_follow_up(client):
    sid = client.post("/api/v1/sessions", json={"entry_id": "entry_pilot_001"}).json()["session_id"]
    client.put("/api/v1/config", json={"agent_enabled": False})
    t1 = client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "转账失败"}).json()
    assert t1["graphic_template_ref"] == "faq:transfer_fail"
    assert "您还想咨询" in t1["spoken_text"]
    assert "对方没收到" in _labels(t1)
