"""近程 C2：冻结 RAG 样例门禁。"""

from app.services import rag_gate


def _run_case(client, case: dict) -> list[str]:
    suite = rag_gate.load_gate_suite()
    client.put(
        "/api/v1/config",
        json={"rag_enabled": bool(case.get("rag_enabled", True)), "agent_enabled": False},
    )
    sid = client.post("/api/v1/sessions", json={"entry_id": "entry_pilot_001"}).json()["session_id"]
    body = {"spoken_text": "", "source": ""}
    for text in case.get("turns") or []:
        body = client.post(f"/api/v1/sessions/{sid}/messages", json={"text": text}).json()
    events = client.get(f"/api/v1/sessions/{sid}/events").json()
    keys = [e["event_key"] for e in events]
    payloads = [e.get("payload") or {} for e in events if e["event_key"] == "dh_rag_hit"]
    return rag_gate.evaluate_case_result(
        case=case,
        spoken=body.get("spoken_text") or "",
        event_keys=keys,
        event_payloads=payloads,
        suite=suite,
    )


def test_gate_suite_has_hit_miss_refuse():
    kinds = {c["kind"] for c in rag_gate.list_cases()}
    ids = {c["id"] for c in rag_gate.list_cases()}
    assert {"hit", "miss", "refuse"} <= kinds
    assert {
        "H3",
        "H4",
        "R3",
        "H5",
        "H6",
        "R4",
        "H7",
        "H8",
        "R5",
        "H9",
        "H10",
        "R6",
        "H11",
        "H12",
        "R7",
        "H13",
        "H14",
        "R8",
    } <= ids
    assert len(rag_gate.list_cases()) >= 23


def test_all_frozen_rag_gate_cases(client):
    failures = []
    for case in rag_gate.list_cases():
        errors = _run_case(client, case)
        if errors:
            failures.append(f"{case['id']} {case.get('title')}: " + "; ".join(errors))
    assert not failures, "\n".join(failures)
