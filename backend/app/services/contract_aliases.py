from __future__ import annotations

from typing import Any

# 方案级字段别名：本地契约 ↔ 现网语义（尚未与 OpenAPI 终态对账）
ALIASES: list[dict[str, str]] = [
    {"local": "session_id", "jtalk_semantic": "sid", "note": "会话 ID"},
    {"local": "d_profile_key", "jtalk_semantic": "dProfileKey", "note": "形象 001–004"},
    {"local": "room_id", "jtalk_semantic": "roomId", "note": "数字人房间"},
    {"local": "spoken_text", "jtalk_semantic": "content/口播文本", "note": "推流口播"},
    {"local": "action_intent", "jtalk_semantic": "动作配置映射", "note": "不得自造未登记动作"},
    {"local": "command_id", "jtalk_semantic": "特殊指令 ID", "note": "0001–0005 等"},
    {"local": "graphic_template_ref", "jtalk_semantic": "图文模板引用", "note": "非任意 HTML"},
    {"local": "suggest_transfer_human", "jtalk_semantic": "转人工建议", "note": "执行须确定性接口"},
]


def list_aliases() -> dict[str, Any]:
    return {
        "status": "draft_local",
        "disclaimer": "未与现网 OpenAPI 字段级对账前不得直接编码对接",
        "aliases": ALIASES,
    }


def list_themes() -> dict[str, Any]:
    return {
        "themes": [
            {"id": "default", "label": "默认浅色"},
            {"id": "ink", "label": "深色点缀"},
        ]
    }
