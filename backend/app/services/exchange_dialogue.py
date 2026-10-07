from __future__ import annotations

from typing import Any

from app.services import return_dialogue as rd

# 换货多轮：冷启动澄清原因 → 尺码／发错／质量／建议转人工（退货进行中不抢）

ASK_EXCHANGE_KEYWORDS = ("申请换货", "我想换货", "要换货", "换货", "想换货", "换一个", "换尺码")
SIZE_KEYWORDS = ("尺码不合适", "尺码", "大小", "太大", "太小", "不合身")
WRONG_KEYWORDS = ("发错货了", "发错", "错款", "不是我买的", "寄错")
QUALITY_KEYWORDS = ("质量有问题", "质量", "破损", "坏了", "瑕疵", "损坏")
TRANSFER_KEYWORDS = ("转人工", "人工客服", "找人工")


def _contains_any(text: str, keywords: tuple[str, ...]) -> bool:
    t = text.strip().lower()
    return any(k.lower() in t for k in keywords)


def clarify_reply() -> dict[str, Any]:
    return rd._reply(
        "换货是尺码不对、发错货，还是质量问题？说一下，我告诉您下一步。",
        "faq:exchange_clarify",
        action="none",
    )


def size_reply() -> dict[str, Any]:
    return rd._reply(
        "尺码不对的话，多半能换：进订单详情找「申请换货」，选好规格提交。没有入口就回「怎么退货」，或带订单号点「转人工」。",
        "faq:exchange_size",
        action="none",
    )


def wrong_reply() -> dict[str, Any]:
    return rd._reply(
        "发错货一般能补发或换货：进订单详情找售后／补发／换货入口。找不到就带订单号回「转人工」。",
        "faq:exchange_wrong",
        action="none",
        suggest_transfer=True,
    )


def quality_reply() -> dict[str, Any]:
    return rd._reply(
        "质量或破损先拍个照留着。能换就去订单里申请换货；也可回「怎么退货」，或点「转人工」。",
        "faq:exchange_quality",
        action="none",
        suggest_transfer=True,
    )


def suggest_transfer_reply() -> dict[str, Any]:
    return rd._reply(
        "行，您点一下「转人工」，同事帮您处理换货。",
        "faq:exchange_suggest_transfer",
        action="transfer_announce",
        suggest_transfer=True,
    )


def try_exchange_dialogue(
    text: str,
    state: dict[str, Any],
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    if state.get("return_flow", "idle") != "idle":
        return None, state
    if state.get("refund_flow", "idle") != "idle":
        return None, state
    if state.get("logistics_flow", "idle") != "idle":
        return None, state
    if state.get("invoice_flow", "idle") != "idle":
        return None, state
    if state.get("address_flow", "idle") != "idle":
        return None, state
    if state.get("cancel_flow", "idle") != "idle":
        return None, state
    if state.get("complaint_flow", "idle") != "idle":
        return None, state
    if state.get("payment_flow", "idle") != "idle":
        return None, state
    if state.get("coupon_flow", "idle") != "idle":
        return None, state
    if state.get("warranty_flow", "idle") != "idle":
        return None, state
    if state.get("points_flow", "idle") != "idle":
        return None, state
    if state.get("price_protect_flow", "idle") != "idle":
        return None, state
    if state.get("stock_flow", "idle") != "idle":
        return None, state

    exchange = state.get("exchange_flow", "idle")
    category = state.get("return_reason_category")

    def pack(**kwargs: Any) -> dict[str, Any]:
        base = {
            "return_flow": "idle",
            "return_reason_category": category,
            "refund_flow": "idle",
            "logistics_flow": "idle",
            "invoice_flow": "idle",
            "address_flow": "idle",
            "cancel_flow": "idle",
            "exchange_flow": exchange,
            "complaint_flow": "idle",
            "payment_flow": "idle",
            "coupon_flow": "idle",
            "warranty_flow": "idle",
            "points_flow": "idle",
            "price_protect_flow": "idle",
            "stock_flow": "idle",
        }
        base.update(kwargs)
        return base

    if exchange == "awaiting_clarify":
        if _contains_any(text, TRANSFER_KEYWORDS):
            return suggest_transfer_reply(), pack(exchange_flow="idle")
        if _contains_any(text, SIZE_KEYWORDS):
            return size_reply(), pack(exchange_flow="idle")
        if _contains_any(text, WRONG_KEYWORDS):
            return wrong_reply(), pack(exchange_flow="idle")
        if _contains_any(text, QUALITY_KEYWORDS):
            return quality_reply(), pack(exchange_flow="idle")
        return clarify_reply(), pack(exchange_flow="awaiting_clarify")

    if _contains_any(text, ASK_EXCHANGE_KEYWORDS):
        if _contains_any(text, SIZE_KEYWORDS):
            return size_reply(), pack(exchange_flow="idle")
        if _contains_any(text, WRONG_KEYWORDS):
            return wrong_reply(), pack(exchange_flow="idle")
        if _contains_any(text, QUALITY_KEYWORDS):
            return quality_reply(), pack(exchange_flow="idle")
        return clarify_reply(), pack(exchange_flow="awaiting_clarify")

    return None, state
