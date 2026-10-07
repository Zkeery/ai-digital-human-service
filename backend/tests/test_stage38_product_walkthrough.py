"""产品走查清单（零售金融本地试点）接口层冒烟：对应清单 #1～#8。"""


def test_product_walkthrough_checklist(client):
    # #5 Agent 关
    cfg = client.put("/api/v1/config", json={"agent_enabled": False}).json()
    assert cfg["agent_enabled"] is False

    sid = client.post("/api/v1/sessions", json={"entry_id": "entry_pilot_001"}).json()["session_id"]

    # #1 欢迎／引导（零售金融口径）
    guide = client.post(f"/api/v1/sessions/{sid}/guide", json={}).json()
    spoken = (guide.get("spoken_text") or "").strip()
    hello = client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "你好"}).json()
    assert hello["source"] == "faq"
    assert "零售金融" in hello["spoken_text"]
    assert "退货" not in hello["spoken_text"]
    if spoken:
        assert "退货" not in spoken

    # #2 查余额
    bal = client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "查余额"}).json()
    assert bal["source"] == "account_dialogue"
    assert bal["spoken_text"].strip()
    assert "查真" not in bal["spoken_text"]
    labels = [c.get("label") for c in bal.get("quick_replies") or []]
    assert labels
    assert "转人工" not in labels

    # 新会话测信用卡，避免账户澄清锁死
    sid2 = client.post("/api/v1/sessions", json={"entry_id": "entry_pilot_001"}).json()["session_id"]
    # #3 办信用卡
    credit = client.post(f"/api/v1/sessions/{sid2}/messages", json={"text": "办信用卡"}).json()
    assert credit["source"] == "credit_dialogue"
    credit_labels = [c.get("label") for c in credit.get("quick_replies") or []]
    assert any("办卡" in (x or "") or "申请" in (x or "") or "额度" in (x or "") for x in credit_labels)
    assert "批额" not in credit["spoken_text"]

    # #4 怎么退货
    sid3 = client.post("/api/v1/sessions", json={"entry_id": "entry_pilot_001"}).json()["session_id"]
    off = client.post(f"/api/v1/sessions/{sid3}/messages", json={"text": "怎么退货"}).json()
    assert off["source"] == "offtopic_rule"
    assert "密码****" not in off["spoken_text"]
    assert "已脱敏" not in off["spoken_text"]

    # #8 假卡号绑卡
    sid4 = client.post("/api/v1/sessions", json={"entry_id": "entry_pilot_001"}).json()["session_id"]
    fake = "6222021234567890123"
    card = client.post(
        f"/api/v1/sessions/{sid4}/messages",
        json={"text": f"卡号{fake}怎么绑"},
    ).json()
    assert card["source"] == "card_dialogue"
    assert fake not in card["spoken_text"]
    assert "已脱敏" not in card["spoken_text"]
    hist = client.get(f"/api/v1/sessions/{sid4}/history").json()["items"]
    user_texts = " ".join(i.get("text") or "" for i in hist if i.get("role") == "user")
    assert fake not in user_texts

    # #6 转人工 + #7 评价
    sid5 = client.post("/api/v1/sessions", json={"entry_id": "entry_pilot_001"}).json()["session_id"]
    client.post(f"/api/v1/sessions/{sid5}/messages", json={"text": "查余额"})
    transferred = client.post(f"/api/v1/sessions/{sid5}/transfer").json()
    assert transferred["status"] == "transferred"
    blocked = client.post(f"/api/v1/sessions/{sid5}/messages", json={"text": "还能问吗"})
    assert blocked.status_code == 409
    rated = client.post(
        f"/api/v1/sessions/{sid5}/rating",
        json={"rating_type": "digital_human", "score": 4, "comment": "走查冒烟"},
    ).json()
    assert rated["ok"] is True
    events = client.get(f"/api/v1/sessions/{sid5}/events").json()
    keys = [e["event_key"] for e in events]
    assert "dh_transfer_human" in keys
    assert "dh_rate" in keys
