from __future__ import annotations

from typing import Any

from app.services import return_dialogue as rd

# 发票多轮：泛问开票 → 澄清 → 电子／纸质／重开改抬头／建议转人工

ASK_INVOICE_KEYWORDS = ("发票", "开票", "开发票", "发票抬头", "要发票")
ELECTRONIC_KEYWORDS = ("电子发票", "电子票", "电票")
PAPER_KEYWORDS = ("纸质发票", "纸票", "增值税专用发票", "专票")
REISSUE_KEYWORDS = ("重开", "改抬头", "重开改抬头", "换抬头", "错抬头")
TRANSFER_KEYWORDS = ("转人工", "人工客服", "找人工")


def _contains_any(text: str, keywords: tuple[str, ...]) -> bool:
    t = text.strip().lower()
    return any(k.lower() in t for k in keywords)


def clarify_reply() -> dict[str, Any]:
    return rd._reply(
        "发票这边：要电子票、纸质票，还是重开改抬头？点一下就行。",
        "faq:invoice_clarify",
        action="none",
    )


def electronic_reply() -> dict[str, Any]:
    return rd._reply(
        "电子票多半在订单详情或「我的发票」里申请，填抬头税号提交就行。没有入口就把订单号发我并回「转人工」。",
        "faq:invoice_electronic",
        action="none",
    )


def paper_reply() -> dict[str, Any]:
    return rd._reply(
        "纸质票要在发票申请里选纸质并填邮寄地址；有的订单只支持电子票。找不到入口或要专票，带订单号回「转人工」。",
        "faq:invoice_paper",
        action="none",
        suggest_transfer=True,
    )


def reissue_reply() -> dict[str, Any]:
    return rd._reply(
        "改抬头或重开通常有次数和时效限制。准备好正确抬头、税号和订单号，点「转人工」更稳妥。",
        "faq:invoice_reissue",
        action="none",
        suggest_transfer=True,
    )


def suggest_transfer_reply() -> dict[str, Any]:
    return rd._reply(
        "行，您点一下「转人工」，同事帮您处理发票。",
        "faq:invoice_suggest_transfer",
        action="transfer_announce",
        suggest_transfer=True,
    )


def try_invoice_dialogue(
    text: str,
    state: dict[str, Any],
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    if state.get("return_flow", "idle") != "idle":
        return None, state
    if state.get("refund_flow", "idle") != "idle":
        return None, state
    if state.get("logistics_flow", "idle") != "idle":
        return None, state
    if state.get("address_flow", "idle") != "idle":
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

    invoice = state.get("invoice_flow", "idle")
    category = state.get("return_reason_category")

    def pack(**kwargs: Any) -> dict[str, Any]:
        base = {
            "return_flow": "idle",
            "return_reason_category": category,
            "refund_flow": "idle",
            "logistics_flow": "idle",
            "invoice_flow": invoice,
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

    if invoice == "awaiting_clarify":
        if _contains_any(text, TRANSFER_KEYWORDS):
            return suggest_transfer_reply(), pack(invoice_flow="idle")
        if _contains_any(text, ELECTRONIC_KEYWORDS):
            return electronic_reply(), pack(invoice_flow="idle")
        if _contains_any(text, PAPER_KEYWORDS):
            return paper_reply(), pack(invoice_flow="idle")
        if _contains_any(text, REISSUE_KEYWORDS):
            return reissue_reply(), pack(invoice_flow="idle")
        return clarify_reply(), pack(invoice_flow="awaiting_clarify")

    if _contains_any(text, ASK_INVOICE_KEYWORDS):
        if _contains_any(text, ELECTRONIC_KEYWORDS):
            return electronic_reply(), pack(invoice_flow="idle")
        if _contains_any(text, PAPER_KEYWORDS):
            return paper_reply(), pack(invoice_flow="idle")
        if _contains_any(text, REISSUE_KEYWORDS):
            return reissue_reply(), pack(invoice_flow="idle")
        return clarify_reply(), pack(invoice_flow="awaiting_clarify")

    return None, state
