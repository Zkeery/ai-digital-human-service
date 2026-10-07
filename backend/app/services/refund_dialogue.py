from __future__ import annotations

from typing import Any

from app.services import return_dialogue as rd

# 退款多轮：泛问退款 → 澄清 → 进度说明／转入退货探因

ASK_REFUND_KEYWORDS = ("退款", "退钱", "退费")
PROGRESS_KEYWORDS = ("退款进度", "退款到账", "钱怎么还没退", "查退款进度", "退款进度怎么看")
WAITING_KEYWORDS = ("已经寄回", "寄回等退款", "等退款", "在等退款", "已经寄回等退款")
NEED_RETURN_KEYWORDS = ("还没办理退货", "还没退货", "没有退货", "先退货", "要先退货")


def _contains_any(text: str, keywords: tuple[str, ...]) -> bool:
    t = text.strip().lower()
    return any(k.lower() in t for k in keywords)


def clarify_reply() -> dict[str, Any]:
    return rd._reply(
        "退款这边：您是已经寄回在等钱，还是还没办退货？说一下，我告诉您下一步。",
        "faq:refund_general",
        action="none",
    )


def progress_reply() -> dict[str, Any]:
    return rd._reply(
        "如果货已经寄回，退款进度多半在订单详情里。需要人工就带订单号，我可以建议您转人工。",
        "faq:refund_progress",
        action="none",
        suggest_transfer=True,
    )


def try_refund_dialogue(
    text: str,
    state: dict[str, Any],
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    """退货多轮进行中不抢答；返回 (reply, new_state) 或 (None, state)。"""
    if state.get("return_flow", "idle") != "idle":
        return None, state
    if state.get("logistics_flow", "idle") == "awaiting_clarify":
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

    refund = state.get("refund_flow", "idle")
    category = state.get("return_reason_category")

    def pack(**kwargs: Any) -> dict[str, Any]:
        base = {
            "return_flow": "idle",
            "return_reason_category": category,
            "refund_flow": refund,
            "logistics_flow": "idle",
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

    # 进度类优先（含 idle 直达）
    if _contains_any(text, PROGRESS_KEYWORDS) or (
        refund == "awaiting_clarify" and _contains_any(text, WAITING_KEYWORDS)
    ):
        return progress_reply(), pack(refund_flow="idle")

    if refund == "awaiting_clarify":
        if _contains_any(text, NEED_RETURN_KEYWORDS) or _contains_any(text, rd.ASK_RETURN_KEYWORDS):
            return rd.ask_reason_reply(), pack(
                return_flow="awaiting_reason",
                return_reason_category=None,
                refund_flow="idle",
            )
        if _contains_any(text, WAITING_KEYWORDS):
            return progress_reply(), pack(refund_flow="idle")
        return clarify_reply(), pack(refund_flow="awaiting_clarify")

    if _contains_any(text, ASK_REFUND_KEYWORDS):
        return clarify_reply(), pack(refund_flow="awaiting_clarify")

    return None, state
