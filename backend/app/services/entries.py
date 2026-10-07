"""本地多入口白名单目录（近程 A1）。访客不可见；验收模式可选。"""

from __future__ import annotations

from typing import Any

from app.core.errors import AppError

# 字段 theme／accent／logo_url／agent_enabled 供 A2 使用；A1 先返回并允许建会话。
ENTRY_CATALOG: list[dict[str, Any]] = [
    {
        "id": "entry_pilot_001",
        "label": "通用金融咨询",
        "welcome_text": (
            "您好，我是零售金融数字人客服。可咨询账户、转账、卡片、登录密码问题、信用卡、"
            "理财说明书、网点或投诉。请直接说明问题；查账、转账、改密等需本人在官方渠道办理。"
        ),
        "theme": "default",
        "accent": "#0f766e",
        "logo_url": "/entries/general.svg",
        "agent_enabled": False,
    },
    {
        "id": "entry_credit_001",
        "label": "信用卡专窗",
        "welcome_text": (
            "您好，这里是信用卡咨询专窗（数字人客服，非人工）。可了解办卡材料、额度与还款日怎么查；"
            "不审批额度、不代客办卡。资金与身份操作请走官方 App 或转人工。"
        ),
        "theme": "ink",
        "accent": "#0e7490",
        "logo_url": "/entries/credit.svg",
        "agent_enabled": True,
    },
]


def list_entries() -> list[dict[str, Any]]:
    return [dict(item) for item in ENTRY_CATALOG]


def allowed_entry_ids() -> set[str]:
    return {str(item["id"]) for item in ENTRY_CATALOG}


def get_entry(entry_id: str) -> dict[str, Any] | None:
    for item in ENTRY_CATALOG:
        if item["id"] == entry_id:
            return dict(item)
    return None


def require_allowed_entry(entry_id: str) -> dict[str, Any]:
    entry = get_entry(entry_id)
    if entry is None:
        raise AppError(
            "ENTRY_NOT_ALLOWED",
            "该入口未在本地白名单中，请改用已配置入口",
            status_code=403,
        )
    return entry


def welcome_text_for(entry_id: str, fallback: str) -> str:
    entry = get_entry(entry_id)
    if not entry:
        return fallback
    text = str(entry.get("welcome_text") or "").strip()
    return text or fallback


def entry_agent_enabled(entry_id: str) -> bool:
    entry = get_entry(entry_id)
    if not entry:
        return False
    return bool(entry.get("agent_enabled"))


def effective_agent_enabled(global_enabled: bool, entry_id: str) -> bool:
    """总闸 AND 入口开关；任一关则不用 Agent。"""
    return bool(global_enabled) and entry_agent_enabled(entry_id)
