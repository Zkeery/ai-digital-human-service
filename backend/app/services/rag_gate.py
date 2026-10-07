"""近程 C2：RAG 冻结样例门禁（命中／未命中／拒答）。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_CASES_PATH = Path(__file__).resolve().parents[1] / "knowledge" / "rag_gate_cases.json"


def load_gate_suite() -> dict[str, Any]:
    return json.loads(_CASES_PATH.read_text(encoding="utf-8"))


def list_cases() -> list[dict[str, Any]]:
    return list(load_gate_suite().get("cases") or [])


def forbidden_phrases(suite: dict[str, Any] | None = None) -> list[str]:
    data = suite or load_gate_suite()
    return [str(x) for x in (data.get("forbidden_phrases") or [])]


def _contains_all(text: str, items: list[str]) -> list[str]:
    missing = [x for x in items if x and x not in text]
    return missing


def _contains_any(text: str, items: list[str]) -> bool:
    return any(x and x in text for x in items)


def _find_forbidden(text: str, phrases: list[str]) -> list[str]:
    return [p for p in phrases if p and p in text]


def evaluate_case_result(
    *,
    case: dict[str, Any],
    spoken: str,
    event_keys: list[str],
    event_payloads: list[dict[str, Any]],
    suite: dict[str, Any] | None = None,
) -> list[str]:
    """返回错误列表；空列表表示通过。"""
    errors: list[str] = []
    expect = case.get("expect") or {}
    shared_forbid = forbidden_phrases(suite)
    extra_forbid = [str(x) for x in (expect.get("spoken_forbids_extra") or [])]
    all_forbid = shared_forbid + extra_forbid

    hit_forbid = _find_forbidden(spoken, all_forbid)
    if hit_forbid:
        errors.append(f"口播含禁词：{', '.join(hit_forbid)}")

    must = [str(x) for x in (expect.get("spoken_contains") or [])]
    missing = _contains_all(spoken, must)
    if missing:
        errors.append(f"口播缺少：{', '.join(missing)}")

    any_need = [str(x) for x in (expect.get("spoken_contains_any") or [])]
    if any_need and not _contains_any(spoken, any_need):
        errors.append(f"口播未命中任一必要片段：{', '.join(any_need)}")

    want_event = expect.get("event")
    if want_event and want_event not in event_keys:
        errors.append(f"缺少事件 {want_event}，实际={event_keys}")

    opt_event = expect.get("event_optional")
    # optional：不强制

    chunk_id = expect.get("chunk_id")
    if chunk_id:
        matched = False
        for payload in event_payloads:
            if payload.get("chunk_id") == chunk_id:
                matched = True
                break
        if not matched and "dh_rag_hit" in event_keys:
            errors.append(f"dh_rag_hit 未带 chunk_id={chunk_id}")
        elif not matched and want_event == "dh_rag_hit":
            errors.append(f"未找到 chunk_id={chunk_id} 的命中载荷")

    if expect.get("spoken_forbids_policy_tone"):
        # 未命中荐股：不得伪装成正式投顾结论
        bad_tone = ["建议您买入", "必涨", "内幕", "稳赚"]
        tone_hits = _find_forbidden(spoken, bad_tone)
        if tone_hits:
            errors.append(f"未命中场景出现不当投顾语气：{', '.join(tone_hits)}")

    _ = opt_event
    return errors
