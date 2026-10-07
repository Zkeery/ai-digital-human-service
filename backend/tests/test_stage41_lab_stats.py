def test_stats_empty(client):
    res = client.get("/api/v1/stats")
    assert res.status_code == 200
    body = res.json()
    assert body["sessions_total"] == 0
    assert body["agent_used"] == 0
    assert body["sessions_transferred"] == 0
    assert len(body["by_entry"]) >= 2
    assert all(row["sessions"] == 0 for row in body["by_entry"])


def test_stats_aggregates_by_entry_and_agent(client):
    client.put("/api/v1/config", json={"agent_enabled": True})

    general = client.post("/api/v1/sessions", json={"entry_id": "entry_pilot_001"}).json()
    credit = client.post("/api/v1/sessions", json={"entry_id": "entry_credit_001"}).json()

    # 通用入口：总闸开但入口关 → agent skipped
    client.post(
        f"/api/v1/sessions/{general['session_id']}/messages",
        json={"text": "今天天气怎么样啊随便问问"},
    )
    # 信用卡入口：可走 Agent（mock）
    client.post(
        f"/api/v1/sessions/{credit['session_id']}/messages",
        json={"text": "今天天气怎么样啊随便问问"},
    )
    client.post(f"/api/v1/sessions/{credit['session_id']}/transfer", json={})

    body = client.get("/api/v1/stats").json()
    assert body["sessions_total"] == 2
    assert body["sessions_transferred"] == 1
    assert body["transfer_events"] >= 1
    assert body["messages_replied"] >= 2
    assert body["agent_used"] >= 1
    assert body["agent_skipped"] >= 1

    by_id = {row["entry_id"]: row for row in body["by_entry"]}
    assert by_id["entry_pilot_001"]["sessions"] == 1
    assert by_id["entry_pilot_001"]["agent_skipped"] >= 1
    assert by_id["entry_credit_001"]["sessions"] == 1
    assert by_id["entry_credit_001"]["transferred"] == 1
    assert by_id["entry_credit_001"]["agent_used"] >= 1
