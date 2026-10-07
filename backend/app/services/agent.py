from __future__ import annotations

import json
from typing import Any

import httpx

from app.core.config import Settings
from app.core.errors import AppError
from app.services.privacy import redact_sensitive

ALLOWED_ACTIONS = {"none", "wave", "nod", "transfer_announce"}


def compose_agent_reply(
    settings: Settings,
    user_text: str,
    faq_hit: dict[str, str] | None,
) -> dict[str, Any] | None:
    """返回结构化旁路结果；失败返回 None（调用方回退 FAQ／规则）。"""
    if settings.llm_mock or not settings.llm_api_key:
        return _mock_reply(user_text, faq_hit)

    # 真实调用预算闸门由上层保证；此处做超时与结构校验；外发前脱敏
    safe_utterance = redact_sensitive(user_text)[:500]
    prompt_payload = {
        "model": settings.llm_model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "你是零售金融客服口播撰稿助手。只输出 JSON："
                    '{"spoken_text":str,"action_intent":"none|wave|nod|transfer_announce",'
                    '"graphic_template_ref":str,"suggest_transfer_human":bool,"safety_flags":[]}'
                    "。紧扣用户当前问题作答；faq_hit 仅作参考，若与问题不符以用户问题为准。"
                    "业务线是零售金融咨询指引（账户／转账／卡片／密码／信用卡／理财说明书／网点／投诉），"
                    "不是电商售后，不是投顾荐股。"
                    "禁止：承诺收益或到账时刻、替用户转账／改密／挂失／批额、索要完整卡号／密码／验证码。"
                    "说不清或需查真账时，建议转人工（suggest_transfer_human=true），口播简短可播。"
                    "不要承诺未授权权益；不要自造未登记动作。"
                ),
            },
            {
                "role": "user",
                "content": json.dumps(
                    {"utterance": safe_utterance, "faq_hit": faq_hit},
                    ensure_ascii=False,
                ),
            },
        ],
        "temperature": 0.2,
    }
    try:
        with httpx.Client(timeout=settings.llm_timeout_seconds) as client:
            resp = client.post(
                f"{settings.llm_base_url.rstrip('/')}/chat/completions",
                headers={"Authorization": f"Bearer {settings.llm_api_key}"},
                json=prompt_payload,
            )
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"]
            data = _extract_json(content)
            return _validate(data)
    except Exception:
        return None


def _mock_reply(user_text: str, faq_hit: dict[str, str] | None) -> dict[str, Any]:
    base = faq_hit["spoken_text"] if faq_hit else "我已理解您的问题，下面用口播为您说明要点。"
    suggest = any(k in user_text for k in ("人工", "转接", "投诉"))
    return {
        "spoken_text": f"{base}（Agent 旁路已润色）",
        "action_intent": faq_hit["action_intent"] if faq_hit else "nod",
        "graphic_template_ref": faq_hit["graphic_template_ref"] if faq_hit else "agent:default",
        "suggest_transfer_human": suggest,
        "safety_flags": [],
    }


def _extract_json(content: str) -> dict[str, Any]:
    content = content.strip()
    if content.startswith("```"):
        lines = content.splitlines()
        lines = [ln for ln in lines if not ln.strip().startswith("```")]
        content = "\n".join(lines)
    return json.loads(content)


def _validate(data: dict[str, Any]) -> dict[str, Any] | None:
    spoken = data.get("spoken_text")
    action = data.get("action_intent")
    graphic = data.get("graphic_template_ref")
    suggest = data.get("suggest_transfer_human", False)
    if not isinstance(spoken, str) or not spoken.strip():
        return None
    if action not in ALLOWED_ACTIONS:
        return None
    if not isinstance(graphic, str) or not graphic.strip():
        return None
    if not isinstance(suggest, bool):
        return None
    flags = data.get("safety_flags", [])
    if not isinstance(flags, list):
        return None
    return {
        "spoken_text": spoken.strip(),
        "action_intent": action,
        "graphic_template_ref": graphic.strip(),
        "suggest_transfer_human": suggest,
        "safety_flags": flags,
    }


def assert_budget_allows(settings: Settings, estimated_month_cny: float) -> None:
    if estimated_month_cny > settings.monthly_budget_cny:
        raise AppError(
            "BUDGET_EXCEEDED",
            f"本月模型费用估算已超过上限 {settings.monthly_budget_cny} 元，已阻止真实调用。",
            status_code=402,
        )
