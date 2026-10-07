from __future__ import annotations

from typing import Any

from app.services import return_dialogue as rd

# 支付／扣款：澄清类型 → 重试／留证转人工／看订单（不查真流水）

ASK_PAYMENT_KEYWORDS = (
    "支付问题",
    "支付失败",
    "付款失败",
    "付不了款",
    "重复扣款",
    "扣了两次",
    "多扣了",
    "扣款失败",
)
FAILED_KEYWORDS = ("支付失败", "付款失败", "付不了", "扣款失败", "没付成功", "付不上")
DUPLICATE_KEYWORDS = ("重复扣款", "扣了两次", "多扣了", "扣两次", "重复扣")
HELD_KEYWORDS = ("已扣款未发货", "扣了没发", "钱扣了", "扣款了没发货", "扣了款没发")
TRANSFER_KEYWORDS = ("转人工", "人工客服", "找人工")


def _contains_any(text: str, keywords: tuple[str, ...]) -> bool:
    t = text.strip().lower()
    return any(k.lower() in t for k in keywords)


def clarify_reply() -> dict[str, Any]:
    return rd._reply(
        "支付这边卡在哪了？点一下，或直接说就行。",
        "faq:payment_clarify",
        action="none",
    )


def failed_reply() -> dict[str, Any]:
    return rd._reply(
        "先换个支付方式再试，顺手看下余额和限额。还不行就把订单号发我，点「转人工」。",
        "faq:payment_failed",
        action="none",
        suggest_transfer=True,
    )


def duplicate_reply() -> dict[str, Any]:
    return rd._reply(
        "先把扣款截图留着。多半会自动退回；过一天还没有，点「转人工」帮您查。",
        "faq:payment_duplicate",
        action="none",
        suggest_transfer=True,
    )


def held_reply() -> dict[str, Any]:
    return rd._reply(
        "先打开订单看一眼，或回「查物流」。一直没动静，把订单号发我并点「转人工」。",
        "faq:payment_held",
        action="none",
        suggest_transfer=True,
    )


def suggest_transfer_reply() -> dict[str, Any]:
    return rd._reply(
        "行，您点一下「转人工」，我帮您叫同事。",
        "faq:payment_suggest_transfer",
        action="transfer_announce",
        suggest_transfer=True,
    )


def try_payment_dialogue(
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
    if state.get("exchange_flow", "idle") != "idle":
        return None, state
    if state.get("complaint_flow", "idle") != "idle":
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

    payment = state.get("payment_flow", "idle")
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
            "exchange_flow": "idle",
            "complaint_flow": "idle",
            "payment_flow": payment,
            "coupon_flow": "idle",
            "warranty_flow": "idle",
            "points_flow": "idle",
            "price_protect_flow": "idle",
            "stock_flow": "idle",
        }
        base.update(kwargs)
        return base

    if payment == "awaiting_clarify":
        if _contains_any(text, TRANSFER_KEYWORDS):
            return suggest_transfer_reply(), pack(payment_flow="idle")
        if _contains_any(text, DUPLICATE_KEYWORDS):
            return duplicate_reply(), pack(payment_flow="idle")
        if _contains_any(text, HELD_KEYWORDS):
            return held_reply(), pack(payment_flow="idle")
        if _contains_any(text, FAILED_KEYWORDS):
            return failed_reply(), pack(payment_flow="idle")
        return clarify_reply(), pack(payment_flow="awaiting_clarify")

    if _contains_any(text, ASK_PAYMENT_KEYWORDS):
        if _contains_any(text, TRANSFER_KEYWORDS):
            return suggest_transfer_reply(), pack(payment_flow="idle")
        if _contains_any(text, DUPLICATE_KEYWORDS):
            return duplicate_reply(), pack(payment_flow="idle")
        if _contains_any(text, HELD_KEYWORDS):
            return held_reply(), pack(payment_flow="idle")
        if _contains_any(text, FAILED_KEYWORDS):
            return failed_reply(), pack(payment_flow="idle")
        return clarify_reply(), pack(payment_flow="awaiting_clarify")

    return None, state
