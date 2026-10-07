from __future__ import annotations

from typing import Any

from app.services import finance_followup as ff
from app.services import return_dialogue as rd

# 金融投诉／纠纷：短澄清 → 分支答后保留选项并追问（不自动转接）

ASK_COMPLAINT_KEYWORDS = (
    "我要投诉",
    "投诉你们",
    "要投诉",
    "投诉",
    "举报",
    "纠纷",
    "我要申诉",
    "申诉",
)
ACCOUNT_KEYWORDS = (
    "账户交易纠纷",
    "账户纠纷",
    "交易纠纷",
    "扣款不对",
    "乱扣款",
    "莫名扣款",
    "账不对",
)
CARD_KEYWORDS = (
    "卡片额度相关",
    "卡片问题",
    "额度问题",
    "信用卡纠纷",
    "卡片纠纷",
    "额度纠纷",
)
SERVICE_KEYWORDS = (
    "服务态度",
    "态度差",
    "客服态度",
    "服务差",
    "态度",
)
HUMAN_KEYWORDS = ("转人工", "人工客服", "找人工")
DONE_KEYWORDS = ("不用了", "没有了", "先这样", "没了", "就这些", "暂时不用")

TOPIC_LABELS = {
    "account": "账户交易纠纷",
    "card": "卡片额度相关",
    "service": "服务态度",
}
TOPIC_ORDER = ("account", "card", "service")

_BUSY = (
    "account_flow",
    "transfer_flow",
    "card_flow",
    "auth_flow",
    "credit_flow",
    "wealth_flow",
    "branch_flow",
)


def _contains_any(text: str, keywords: tuple[str, ...]) -> bool:
    t = text.strip().lower()
    return any(k.lower() in t for k in keywords)


def _parse_seen(raw: Any) -> set[str]:
    if not raw:
        return set()
    if isinstance(raw, list):
        return {str(x) for x in raw if str(x) in TOPIC_LABELS}
    return {p for p in str(raw).split(",") if p in TOPIC_LABELS}


def _dump_seen(seen: set[str]) -> str:
    return ",".join(k for k in TOPIC_ORDER if k in seen)


def _follow_up(seen: set[str]) -> str:
    remain = [TOPIC_LABELS[k] for k in TOPIC_ORDER if k not in seen]
    if not remain:
        return "如需继续处理投诉，请点「转人工」，或直接说其他问题。"
    parts = [f"「{x}」" for x in remain]
    if len(parts) == 1:
        joined = parts[0]
    elif len(parts) == 2:
        joined = f"{parts[0]}或{parts[1]}"
    else:
        joined = "、".join(parts[:-1]) + f"或{parts[-1]}"
    return f"您还想咨询{joined}吗？可继续点下方选项。"


def clarify_reply() -> dict[str, Any]:
    return rd._reply(
        "抱歉给您带来不便。请先说明投诉类型：账户交易纠纷、卡片额度相关，还是服务态度？"
        "选定后我会告知材料与转人工路径；本客服不能直接改账或下处罚决定。",
        "faq:complaint_clarify",
        action="none",
    )


def done_reply() -> dict[str, Any]:
    return rd._reply(
        "好的。如仍需处理投诉或核对交易，请点「转人工」，或随时再说。",
        "faq:complaint_done",
        action="none",
        suggest_transfer=True,
    )


def account_body() -> str:
    return (
        "请先截取相关余额或交易明细页，并记下争议时间与金额。"
        "本客服无法查询银行核心账务，请点「转人工」由同事核对。"
    )


def card_body() -> str:
    return (
        "卡片或额度争议，请先在 App「信用卡／卡片管理」查看披露信息；"
        "本客服不能改额度或代办挂失。"
        "若需正式投诉或核对，请点「转人工」。请勿发送完整卡号。"
    )


def service_body() -> str:
    return (
        "服务未达预期，抱歉。"
        "这类情况更适合同事当面了解经过，请点「转人工」优先处理。"
    )


def _topic_reply(topic: str, seen: set[str]) -> tuple[dict[str, Any], set[str]]:
    bodies = {"account": account_body, "card": card_body, "service": service_body}
    graphics = {
        "account": "faq:complaint_account",
        "card": "faq:complaint_card",
        "service": "faq:complaint_service",
    }
    new_seen = set(seen)
    new_seen.add(topic)
    spoken = bodies[topic]() + _follow_up(new_seen)
    return (
        rd._reply(
            spoken,
            graphics[topic],
            action="none",
            suggest_transfer=True,
        ),
        new_seen,
    )


def suggest_transfer_reply() -> dict[str, Any]:
    return rd._reply(
        "好的，请点「转人工」，我帮您接通同事优先处理。",
        "faq:complaint_suggest_transfer",
        action="transfer_announce",
        suggest_transfer=True,
    )


def try_complaint_dialogue(
    text: str,
    state: dict[str, Any],
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    for key in _BUSY:
        if state.get(key, "idle") != "idle":
            return None, state

    complaint = state.get("complaint_flow", "idle")
    seen = _parse_seen(state.get("complaint_seen"))

    def pack(**kwargs: Any) -> dict[str, Any]:
        base = {
            "return_flow": "idle",
            "return_reason_category": state.get("return_reason_category"),
            "refund_flow": "idle",
            "logistics_flow": "idle",
            "invoice_flow": "idle",
            "address_flow": "idle",
            "cancel_flow": "idle",
            "exchange_flow": "idle",
            "complaint_flow": complaint,
            "payment_flow": "idle",
            "coupon_flow": "idle",
            "warranty_flow": "idle",
            "points_flow": "idle",
            "price_protect_flow": "idle",
            "stock_flow": "idle",
            "account_flow": "idle",
            "transfer_flow": "idle",
            "card_flow": "idle",
            "auth_flow": "idle",
            "credit_flow": "idle",
            "wealth_flow": "idle",
            "wealth_seen": "",
            "branch_flow": "idle",
            "branch_seen": "",
            "complaint_seen": _dump_seen(seen),
        }
        base.update(kwargs)
        if "complaint_seen" in kwargs and isinstance(kwargs["complaint_seen"], set):
            base["complaint_seen"] = _dump_seen(kwargs["complaint_seen"])
        return base

    def answer(topic: str) -> tuple[dict[str, Any], dict[str, Any]]:
        reply, new_seen = _topic_reply(topic, seen)
        if len(new_seen) >= len(TOPIC_ORDER):
            return reply, pack(complaint_flow="idle", complaint_seen="")
        return reply, pack(complaint_flow="awaiting_clarify", complaint_seen=new_seen)

    if complaint == "awaiting_clarify":
        if _contains_any(text, HUMAN_KEYWORDS):
            return suggest_transfer_reply(), pack(complaint_flow="idle", complaint_seen="")
        if _contains_any(text, DONE_KEYWORDS):
            return done_reply(), pack(complaint_flow="idle", complaint_seen="")
        if _contains_any(text, SERVICE_KEYWORDS):
            return answer("service")
        if _contains_any(text, ACCOUNT_KEYWORDS):
            return answer("account")
        if _contains_any(text, CARD_KEYWORDS):
            return answer("card")
        if ff.should_keep_clarify_lock(text):
            return clarify_reply(), pack(complaint_flow="awaiting_clarify", complaint_seen=seen)
        # 未命中本场景：释放澄清态，避免换话题仍被同一句锁死
        return None, pack(complaint_flow="idle", complaint_seen="")

    if _contains_any(text, ASK_COMPLAINT_KEYWORDS):
        if _contains_any(text, HUMAN_KEYWORDS):
            return suggest_transfer_reply(), pack(complaint_flow="idle", complaint_seen="")
        if _contains_any(text, SERVICE_KEYWORDS):
            return answer("service")
        if _contains_any(text, ACCOUNT_KEYWORDS):
            return answer("account")
        if _contains_any(text, CARD_KEYWORDS):
            return answer("card")
        return clarify_reply(), pack(complaint_flow="awaiting_clarify", complaint_seen="")

    return None, state
