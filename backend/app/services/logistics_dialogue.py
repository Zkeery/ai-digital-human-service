from __future__ import annotations

from typing import Any

from app.services import return_dialogue as rd

# 物流多轮：泛问物流／发货 → 澄清 → 轨迹说明／催发货／建议转人工

ASK_LOGISTICS_KEYWORDS = ("物流", "快递", "发货", "到哪了", "运单", "查物流", "快递到哪")
SHIPPED_KEYWORDS = ("已经发货", "已发货", "查轨迹", "已经发货查轨迹", "看物流")
NOT_SHIPPED_KEYWORDS = ("还没发货", "催发货", "什么时候发", "还没发货催一下")
TRANSFER_KEYWORDS = ("转人工", "人工客服", "找人工")


def _contains_any(text: str, keywords: tuple[str, ...]) -> bool:
    t = text.strip().lower()
    return any(k.lower() in t for k in keywords)


def clarify_reply() -> dict[str, Any]:
    return rd._reply(
        "物流这边：已经发货想查轨迹，还是还没发、想催一下？点一下就行。",
        "faq:logistics_clarify",
        action="none",
    )


def tracking_reply() -> dict[str, Any]:
    return rd._reply(
        "已发货的话，打开订单详情就能看物流和运单号。好久不更新或显示异常，把订单号发我并回「转人工」。",
        "faq:logistics_tracking",
        action="none",
    )


def not_shipped_reply() -> dict[str, Any]:
    return rd._reply(
        "还没发的话，订单详情里通常有预计发货时间，高峰可能慢一点。已经超时了，把订单号发我并回「转人工」催一下。",
        "faq:logistics_not_shipped",
        action="none",
        suggest_transfer=True,
    )


def suggest_transfer_reply() -> dict[str, Any]:
    return rd._reply(
        "行，您点一下「转人工」，同事帮您查物流。",
        "faq:logistics_suggest_transfer",
        action="transfer_announce",
        suggest_transfer=True,
    )


def try_logistics_dialogue(
    text: str,
    state: dict[str, Any],
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    """退货／退款进行中不抢答。"""
    if state.get("return_flow", "idle") != "idle":
        return None, state
    if state.get("refund_flow", "idle") != "idle":
        return None, state
    if state.get("invoice_flow", "idle") == "awaiting_clarify":
        return None, state
    if state.get("address_flow", "idle") == "awaiting_clarify":
        return None, state
    if state.get("cancel_flow", "idle") != "idle":
        return None, state
    if state.get("exchange_flow", "idle") != "idle":
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

    logistics = state.get("logistics_flow", "idle")
    category = state.get("return_reason_category")

    def pack(**kwargs: Any) -> dict[str, Any]:
        base = {
            "return_flow": "idle",
            "return_reason_category": category,
            "refund_flow": "idle",
            "logistics_flow": logistics,
            "invoice_flow": "idle",
            "address_flow": "idle",
            "cancel_flow": "idle",
            "exchange_flow": "idle",
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

    if logistics == "awaiting_clarify":
        if _contains_any(text, TRANSFER_KEYWORDS):
            return suggest_transfer_reply(), pack(logistics_flow="idle")
        if _contains_any(text, SHIPPED_KEYWORDS):
            return tracking_reply(), pack(logistics_flow="idle")
        if _contains_any(text, NOT_SHIPPED_KEYWORDS):
            return not_shipped_reply(), pack(logistics_flow="idle")
        return clarify_reply(), pack(logistics_flow="awaiting_clarify")

    if _contains_any(text, ASK_LOGISTICS_KEYWORDS):
        # 直达：已发货／催发货关键词可跳过澄清
        if _contains_any(text, SHIPPED_KEYWORDS):
            return tracking_reply(), pack(logistics_flow="idle")
        if _contains_any(text, NOT_SHIPPED_KEYWORDS):
            return not_shipped_reply(), pack(logistics_flow="idle")
        return clarify_reply(), pack(logistics_flow="awaiting_clarify")

    return None, state
