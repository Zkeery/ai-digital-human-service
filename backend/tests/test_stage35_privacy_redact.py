"""敏感信息落库脱敏。"""

from app.services.privacy import redact_payload, redact_sensitive


def test_redact_card_and_id():
    assert "6222" not in redact_sensitive("我的卡号是6222021234567890123")
    assert "****" in redact_sensitive("卡 6222 0212 3456 7890 123")
    assert "110101199001011234" not in redact_sensitive("证件110101199001011234")
    assert "****" in redact_sensitive("证件110101199001011234")
    assert "已脱敏" not in redact_sensitive("卡号6222021234567890123怎么绑")


def test_redact_password_and_otp():
    assert "abc123" not in redact_sensitive("密码是abc123")
    assert "****" in redact_sensitive("密码是abc123")
    assert "884422" not in redact_sensitive("验证码是884422")
    assert "****" in redact_sensitive("验证码是884422")
    assert "已脱敏" not in redact_sensitive("验证码是884422")


def test_redact_does_not_break_topic_list():
    spoken = (
        "您可以问账户、转账、卡片、登录密码问题、信用卡、理财说明书、网点或投诉；"
        "需要同事协助请点「转人工」。"
    )
    assert redact_sensitive(spoken) == spoken
    assert "****" not in redact_sensitive(spoken)


def test_redact_keeps_normal_finance_ask():
    text = "怎么查余额"
    assert redact_sensitive(text) == text


def test_history_and_event_store_redacted(client):
    sid = client.post("/api/v1/sessions", json={"entry_id": "entry_pilot_001"}).json()["session_id"]
    client.put("/api/v1/config", json={"agent_enabled": False})
    body = client.post(
        f"/api/v1/sessions/{sid}/messages",
        json={"text": "卡号6222021234567890123怎么绑"},
    ).json()
    assert "已脱敏" not in body["spoken_text"]
    assert body["source"] == "card_dialogue"

    events = client.get(f"/api/v1/sessions/{sid}/events").json()
    replied = [e for e in events if e["event_key"] == "dh_message_replied"]
    assert replied
    blob = str(replied[-1]["payload"])
    assert "6222021234567890123" not in blob
    assert "已脱敏" not in blob

    from app.db.models import MessageHistoryRow
    from app.db.session import SessionLocal

    db = SessionLocal()
    try:
        rows = (
            db.query(MessageHistoryRow)
            .filter(MessageHistoryRow.session_id == sid, MessageHistoryRow.role == "user")
            .all()
        )
        assert rows
        assert "6222021234567890123" not in rows[-1].text
        assert "****" in rows[-1].text
        assert "已脱敏" not in rows[-1].text
    finally:
        db.close()


def test_assistant_history_keeps_password_topic_word(client):
    sid = client.post("/api/v1/sessions", json={"entry_id": "entry_pilot_001"}).json()["session_id"]
    client.put("/api/v1/config", json={"agent_enabled": False})
    body = client.post(f"/api/v1/sessions/{sid}/messages", json={"text": "怎么退货"}).json()
    assert "登录密码问题" in body["spoken_text"]
    assert "密码****" not in body["spoken_text"]

    from app.db.models import MessageHistoryRow
    from app.db.session import SessionLocal

    db = SessionLocal()
    try:
        rows = (
            db.query(MessageHistoryRow)
            .filter(MessageHistoryRow.session_id == sid, MessageHistoryRow.role == "assistant")
            .all()
        )
        assert rows
        assert "密码****" not in rows[-1].text
        assert "登录密码问题" in rows[-1].text
    finally:
        db.close()


def test_redact_payload_nested():
    out = redact_payload({"text": "验证码是112233", "nested": {"pwd": "密码是secret"}})
    assert "112233" not in out["text"]
    assert "secret" not in out["nested"]["pwd"]
    assert "已脱敏" not in out["text"]
