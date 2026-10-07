from __future__ import annotations

from typing import Any

from app.services import return_dialogue as rd

# 取消订单：澄清发货状态 → 未发货可自助取消；已发货先挽留，坚持再说明拒收／退货

ASK_CANCEL_KEYWORDS = ("取消订单", "撤单", "取消这个订单", "订单取消")
NOT_SHIPPED_KEYWORDS = ("还没发货", "未发货", "没发货")
SHIPPED_KEYWORDS = ("已经发货", "已发货", "发出去了")
TRANSFER_KEYWORDS = ("转人工", "人工客服", "找人工")
INSIST_CANCEL_KEYWORDS = ("还是要取消", "一定要取消", "坚持取消", "非取消不可", "就要取消")
PROBLEM_KEYWORDS = ("商品有问题", "质量", "破损", "发错", "坏了")
WAIT_KEYWORDS = ("先等等看", "再等等", "可以等等", "等等看", "先不取消")


def _contains_any(text: str, keywords: tuple[str, ...]) -> bool:
    t = text.strip().lower()
    return any(k.lower() in t for k in keywords)


def clarify_reply() -> dict[str, Any]:
    return rd._reply(
        "取消订单这块：这笔是还没发货，还是已经发了？两种处理不一样。",
        "faq:cancel_clarify",
        action="none",
    )


def not_shipped_reply() -> dict[str, Any]:
    return rd._reply(
        "还没发的话，多半能在订单详情里点「取消订单」。按钮灰了或取消失败，把订单号发我并回「转人工」。",
        "faq:cancel_not_shipped",
        action="none",
    )


def retain_shipped_reply() -> dict[str, Any]:
    return rd._reply(
        "货已经发了，硬取消会比较麻烦。方便说下原因吗？商品有疑虑我们可以核对；只是拿不准，也可以先等等看包裹。",
        "faq:cancel_retain",
        action="none",
    )


def insist_after_shipped_reply() -> dict[str, Any]:
    return rd._reply(
        "理解，您还是想取消。货发出后一般不能直接撤单：没签收可联系拒收，签收了再走退货。要帮忙就带订单号点「转人工」；要退货也可回「怎么退货」。",
        "faq:cancel_shipped_insist",
        action="none",
        suggest_transfer=True,
    )


def problem_retain_reply() -> dict[str, Any]:
    return rd._reply(
        "要是商品本身有问题，先留好照片，到货走售后往往更稳。可回「怎么退货」，或点「转人工」。",
        "faq:cancel_retain_problem",
        action="none",
        suggest_transfer=True,
    )


def wait_retain_reply() -> dict[str, Any]:
    return rd._reply(
        "好，那就先等等包裹，物流在订单详情能看。到手有问题随时来；中途还想取消，再说一声就行。",
        "faq:cancel_retain_wait",
        action="none",
    )


def suggest_transfer_reply() -> dict[str, Any]:
    return rd._reply(
        "行，您点一下「转人工」，同事帮您处理。",
        "faq:cancel_suggest_transfer",
        action="transfer_announce",
        suggest_transfer=True,
    )


def try_cancel_dialogue(
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

    cancel = state.get("cancel_flow", "idle")
    category = state.get("return_reason_category")

    def pack(**kwargs: Any) -> dict[str, Any]:
        base = {
            "return_flow": "idle",
            "return_reason_category": category,
            "refund_flow": "idle",
            "logistics_flow": "idle",
            "invoice_flow": "idle",
            "address_flow": "idle",
            "cancel_flow": cancel,
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

    if cancel == "retaining":
        if _contains_any(text, TRANSFER_KEYWORDS):
            return suggest_transfer_reply(), pack(cancel_flow="idle")
        if _contains_any(text, INSIST_CANCEL_KEYWORDS):
            return insist_after_shipped_reply(), pack(cancel_flow="idle")
        if _contains_any(text, PROBLEM_KEYWORDS):
            return problem_retain_reply(), pack(cancel_flow="idle")
        if _contains_any(text, WAIT_KEYWORDS):
            return wait_retain_reply(), pack(cancel_flow="idle")
        # 未识别：再挽留一次
        return retain_shipped_reply(), pack(cancel_flow="retaining")

    if cancel == "awaiting_clarify":
        if _contains_any(text, TRANSFER_KEYWORDS):
            return suggest_transfer_reply(), pack(cancel_flow="idle")
        if _contains_any(text, NOT_SHIPPED_KEYWORDS):
            return not_shipped_reply(), pack(cancel_flow="idle")
        if _contains_any(text, SHIPPED_KEYWORDS):
            return retain_shipped_reply(), pack(cancel_flow="retaining")
        return clarify_reply(), pack(cancel_flow="awaiting_clarify")

    if _contains_any(text, ASK_CANCEL_KEYWORDS):
        if _contains_any(text, NOT_SHIPPED_KEYWORDS):
            return not_shipped_reply(), pack(cancel_flow="idle")
        if _contains_any(text, SHIPPED_KEYWORDS):
            return retain_shipped_reply(), pack(cancel_flow="retaining")
        return clarify_reply(), pack(cancel_flow="awaiting_clarify")

    return None, state
