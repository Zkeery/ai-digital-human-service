"""后端第 7 阶段：退款多轮澄清与快捷选项。"""


def _labels(body: dict) -> list[str]:
    return [item["label"] for item in body.get("quick_replies") or []]


def test_refund_clarify_then_progress(client):
    sid = client.post("/api/v1/sessions", json={"entry_id": "entry_pilot_001"}).json()["session_id"]
    client.put("/api/v1/config", json={"agent_enabled": False})

    t1 = client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "我想退款"}).json()
    assert t1["source"] == "refund_dialogue"
    assert "已经寄回" in t1["spoken_text"] or "还没办理" in t1["spoken_text"]
    assert "提交退货申请" not in t1["spoken_text"]
    labels = _labels(t1)
    assert "已经寄回等退款" in labels
    assert "还没办理退货" in labels

    t2 = client.post(
        f"/api/v1/sessions/{sid}/messages", json={"text": "已经寄回等退款"}
    ).json()
    assert t2["source"] == "refund_dialogue"
    assert "退款进度" in t2["spoken_text"]
    assert "提交退货申请" not in t2["spoken_text"]
    assert t2.get("quick_replies") == []


def test_refund_clarify_then_enter_return(client):
    sid = client.post("/api/v1/sessions", json={"entry_id": "entry_pilot_001"}).json()["session_id"]
    client.put("/api/v1/config", json={"agent_enabled": False})

    client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "退款"})
    t2 = client.post(
        f"/api/v1/sessions/{sid}/messages", json={"text": "还没办理退货"}
    ).json()
    assert t2["graphic_template_ref"] == "faq:return_reason"
    assert "提交退货申请" not in t2["spoken_text"]
    assert "尺码不合适" in _labels(t2)


def test_refund_progress_direct(client):
    sid = client.post("/api/v1/sessions", json={"entry_id": "entry_pilot_001"}).json()["session_id"]
    client.put("/api/v1/config", json={"agent_enabled": False})
    body = client.post(
        f"/api/v1/sessions/{sid}/messages", json={"text": "退款进度怎么看"}
    ).json()
    assert body["source"] == "refund_dialogue"
    assert "退款进度" in body["spoken_text"]
