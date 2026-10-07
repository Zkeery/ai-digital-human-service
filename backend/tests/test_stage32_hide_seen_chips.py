"""答过的金融主题不再出现在快捷弹层。"""


def _labels(body: dict) -> list[str]:
    return [item["label"] for item in body.get("quick_replies") or []]


def test_account_hides_answered_chip(client):
    sid = client.post("/api/v1/sessions", json={"entry_id": "entry_pilot_001"}).json()["session_id"]
    client.put("/api/v1/config", json={"agent_enabled": False})
    t1 = client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "查余额"}).json()
    labels = _labels(t1)
    assert "查余额" not in labels
    assert "查流水" in labels
    assert "余额对不上" in labels
    assert "转人工" not in labels
    assert len(labels) <= 5


def test_credit_apply_hides_answered_chip(client):
    sid = client.post("/api/v1/sessions", json={"entry_id": "entry_pilot_001"}).json()["session_id"]
    client.put("/api/v1/config", json={"agent_enabled": False})
    client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "我想办信用卡"})
    t2 = client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "申请步骤"}).json()
    labels = _labels(t2)
    assert "申请步骤" not in labels
    assert "卡种怎么选" in labels or "申请材料" in labels
    assert "转人工" not in labels


def test_clarify_still_shows_full_set(client):
    sid = client.post("/api/v1/sessions", json={"entry_id": "entry_pilot_001"}).json()["session_id"]
    client.put("/api/v1/config", json={"agent_enabled": False})
    t1 = client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "信用卡"}).json()
    labels = _labels(t1)
    assert "办卡申请" in labels
    assert "查额度" in labels
    assert "还款与账单" in labels
    assert "申请提额" in labels
