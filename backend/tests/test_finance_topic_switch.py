"""换话题时不得锁死在上一场景的同一句澄清。"""


def test_account_then_switch_to_card(client):
    sid = client.post("/api/v1/sessions", json={"entry_id": "entry_pilot_001"}).json()["session_id"]
    client.put("/api/v1/config", json={"agent_enabled": False})

    t1 = client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "查余额"}).json()
    assert t1["source"] == "account_dialogue"
    assert "账户余额" in t1["spoken_text"] or "我的资产" in t1["spoken_text"]

    t2 = client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "银行卡丢了怎么办"}).json()
    assert t2["source"] == "card_dialogue"
    assert t2["graphic_template_ref"] != "faq:account_clarify"
    assert "请问您要查余额" not in t2["spoken_text"]


def test_account_then_switch_to_credit(client):
    sid = client.post("/api/v1/sessions", json={"entry_id": "entry_pilot_001"}).json()["session_id"]
    client.put("/api/v1/config", json={"agent_enabled": False})
    client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "查余额"})
    t2 = client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "我想办信用卡"}).json()
    assert t2["source"] == "credit_dialogue"
    assert "请问您要查余额" not in t2["spoken_text"]


def test_account_then_switch_to_branch_hours(client):
    sid = client.post("/api/v1/sessions", json={"entry_id": "entry_pilot_001"}).json()["session_id"]
    client.put("/api/v1/config", json={"agent_enabled": False})
    client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "查余额"})
    t2 = client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "网点营业时间"}).json()
    assert t2["source"] == "branch_dialogue"
    assert "请问您要查余额" not in t2["spoken_text"]


def test_bare_keyword_keeps_transfer_lock(client):
    sid = client.post("/api/v1/sessions", json={"entry_id": "entry_pilot_001"}).json()["session_id"]
    client.put("/api/v1/config", json={"agent_enabled": False})
    client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "转账"})
    body = client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "银行卡"}).json()
    assert body["source"] == "transfer_dialogue"
