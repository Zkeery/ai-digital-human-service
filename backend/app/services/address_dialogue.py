from __future__ import annotations

from typing import Any

from app.services import return_dialogue as rd

# 改地址多轮：泛问改址 → 澄清 → 未发货自助／已发货建议转人工

ASK_ADDRESS_KEYWORDS = ("改地址", "修改地址", "收货地址", "换地址", "改收货地址")
NOT_SHIPPED_KEYWORDS = ("还没发货", "未发货", "没发货")
SHIPPED_KEYWORDS = ("已经发货", "已发货", "发出去了")
TRANSFER_KEYWORDS = ("转人工", "人工客服", "找人工")


def _contains_any(text: str, keywords: tuple[str, ...]) -> bool:
    t = text.strip().lower()
    return any(k.lower() in t for k in keywords)


def clarify_reply() -> dict[str, Any]:
    return rd._reply(
        "改地址这块：订单是还没发货，还是已经发了？两种能改的方式不一样。",
        "faq:address_clarify",
        action="none",
    )


def not_shipped_reply() -> dict[str, Any]:
    return rd._reply(
        "还没发的话，多半能在订单详情里直接改收货地址。没有「修改地址」入口，把订单号发我并回「转人工」。",
        "faq:address_not_shipped",
        action="none",
    )


def shipped_reply() -> dict[str, Any]:
    return rd._reply(
        "已经发了一般不能直接改原地址，可能要拦截改派或退回再发，看物流进度。准备好订单号，点「转人工」更稳。",
        "faq:address_shipped",
        action="none",
        suggest_transfer=True,
    )


def suggest_transfer_reply() -> dict[str, Any]:
    return rd._reply(
        "行，您点一下「转人工」，同事帮您改地址。",
        "faq:address_suggest_transfer",
        action="transfer_announce",
        suggest_transfer=True,
    )


def try_address_dialogue(
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

    address = state.get("address_flow", "idle")
    category = state.get("return_reason_category")

    def pack(**kwargs: Any) -> dict[str, Any]:
        base = {
            "return_flow": "idle",
            "return_reason_category": category,
            "refund_flow": "idle",
            "logistics_flow": "idle",
            "invoice_flow": "idle",
            "address_flow": address,
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

    if address == "awaiting_clarify":
        if _contains_any(text, TRANSFER_KEYWORDS):
            return suggest_transfer_reply(), pack(address_flow="idle")
        if _contains_any(text, NOT_SHIPPED_KEYWORDS):
            return not_shipped_reply(), pack(address_flow="idle")
        if _contains_any(text, SHIPPED_KEYWORDS):
            return shipped_reply(), pack(address_flow="idle")
        return clarify_reply(), pack(address_flow="awaiting_clarify")

    if _contains_any(text, ASK_ADDRESS_KEYWORDS):
        if _contains_any(text, NOT_SHIPPED_KEYWORDS):
            return not_shipped_reply(), pack(address_flow="idle")
        if _contains_any(text, SHIPPED_KEYWORDS):
            return shipped_reply(), pack(address_flow="idle")
        return clarify_reply(), pack(address_flow="awaiting_clarify")

    return None, state
