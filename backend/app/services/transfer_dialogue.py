from __future__ import annotations

from typing import Any

from app.services import finance_followup as ff
from app.services import return_dialogue as rd

# 转账：怎么转／失败／未到账／到账时间 — 短澄清 → 分支答后保留选项并追问

ASK_TRANSFER_KEYWORDS = (
    "转账失败",
    "转账不了",
    "转不过去",
    "没到账",
    "未到账",
    "转账没到",
    "汇款没到",
    "钱没到",
    "转账问题",
    "转账",
    "怎么转账",
    "如何转账",
    "我想转账",
    "我要转账",
    "转账怎么操作",
    "转账流程",
    "教我转账",
    "对方没收到",
    "多久能到",
)
HOW_KEYWORDS = (
    "怎么转账",
    "如何转账",
    "我想转账",
    "我要转账",
    "转账怎么操作",
    "转账流程",
    "教我转账",
)
FAIL_KEYWORDS = ("转账失败", "转账不了", "转不过去", "转不出", "提示失败")
MISSING_KEYWORDS = ("对方没收到", "没到账", "未到账", "转账没到", "汇款没到", "钱没到", "对方说没到")
ETA_KEYWORDS = ("多久能到", "什么时候到", "几时到账", "要多久", "多久到账")

TOPIC_LABELS = {
    "howto": "怎么转账",
    "fail": "转账失败",
    "missing": "对方没收到",
    "eta": "多久能到",
}
TOPIC_ORDER = ("howto", "fail", "missing", "eta")

_BUSY = (
    "account_flow",
    "card_flow",
    "auth_flow",
    "credit_flow",
    "wealth_flow",
    "branch_flow",
    "complaint_flow",
)


def clarify_reply() -> dict[str, Any]:
    return rd._reply(
        "请问您要了解怎么转账、转账失败、对方未收到，还是询问到账时间？请点下方选项。",
        "faq:transfer_clarify",
        action="none",
    )


def done_reply() -> dict[str, Any]:
    return rd._reply(
        "好的。如还有转账问题，可随时再问；需要同事协助请点「转人工」。",
        "faq:transfer_done",
        action="none",
        suggest_transfer=True,
    )


def howto_body() -> str:
    return (
        "请打开 App，进入「转账」或「转账汇款」，按页面填写收款账号、户名与金额，核对无误后提交。"
        "本客服不能代您发起转账，请勿发送完整账号、密码或验证码。"
        "若页面报错、不确定限额，或需要核对某一笔状态，请点「转人工」。"
    )


def fail_body() -> str:
    return (
        "请按页面提示逐项核对：账户余额是否充足、收款账号与户名是否正确、是否超出限额。"
        "若仍提示失败，请保留失败截图与操作时间，点「转人工」。"
    )


def missing_body() -> str:
    return (
        "请先在「账户明细／交易记录」确认该笔是否已扣款成功，并记录交易时间与金额。"
        "本客服无法查询银行核心账务，请点「转人工」核对到账状态。"
    )


def eta_body() -> str:
    return (
        "本客服无法查询或承诺具体到账时刻；请以转账凭证及流水状态为准。"
        "若已超过渠道提示时效仍未到账，请携带凭证点「转人工」。"
    )


def suggest_transfer_reply() -> dict[str, Any]:
    return rd._reply(
        "好的，请点「转人工」，我帮您接通同事。",
        "faq:transfer_suggest_transfer",
        action="transfer_announce",
        suggest_transfer=True,
    )


def _topic_reply(topic: str, seen: set[str]) -> tuple[dict[str, Any], set[str]]:
    bodies = {
        "howto": howto_body,
        "fail": fail_body,
        "missing": missing_body,
        "eta": eta_body,
    }
    graphics = {
        "howto": "faq:transfer_howto",
        "fail": "faq:transfer_fail",
        "missing": "faq:transfer_missing",
        "eta": "faq:transfer_eta",
    }
    new_seen = set(seen)
    new_seen.add(topic)
    spoken = bodies[topic]() + ff.follow_up(
        new_seen,
        TOPIC_LABELS,
        TOPIC_ORDER,
        closing="如还需核对转账，请点「转人工」，或直接说其他问题。",
    )
    return (
        rd._reply(spoken, graphics[topic], action="none", suggest_transfer=True),
        new_seen,
    )


def try_transfer_dialogue(
    text: str,
    state: dict[str, Any],
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    for key in _BUSY:
        if state.get(key, "idle") != "idle":
            return None, state

    transfer = state.get("transfer_flow", "idle")
    seen = ff.parse_seen(state.get("transfer_seen"), TOPIC_LABELS)

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
            "complaint_flow": "idle",
            "complaint_seen": "",
            "payment_flow": "idle",
            "coupon_flow": "idle",
            "warranty_flow": "idle",
            "points_flow": "idle",
            "price_protect_flow": "idle",
            "stock_flow": "idle",
            "account_flow": "idle",
            "account_seen": "",
            "transfer_flow": transfer,
            "transfer_seen": ff.dump_seen(seen, TOPIC_ORDER),
            "card_flow": "idle",
            "card_seen": "",
            "auth_flow": "idle",
            "auth_seen": "",
            "credit_flow": "idle",
            "credit_seen": "",
            "wealth_flow": "idle",
            "wealth_seen": "",
            "branch_flow": "idle",
            "branch_seen": "",
        }
        base.update(kwargs)
        if "transfer_seen" in kwargs and isinstance(kwargs["transfer_seen"], set):
            base["transfer_seen"] = ff.dump_seen(kwargs["transfer_seen"], TOPIC_ORDER)
        return base

    def answer(topic: str) -> tuple[dict[str, Any], dict[str, Any]]:
        reply, new_seen = _topic_reply(topic, seen)
        if len(new_seen) >= len(TOPIC_ORDER):
            return reply, pack(transfer_flow="idle", transfer_seen="")
        return reply, pack(transfer_flow="awaiting_clarify", transfer_seen=new_seen)

    if transfer == "awaiting_clarify":
        if ff.contains_any(text, ff.HUMAN_KEYWORDS):
            return suggest_transfer_reply(), pack(transfer_flow="idle", transfer_seen="")
        if ff.contains_any(text, ff.DONE_KEYWORDS):
            return done_reply(), pack(transfer_flow="idle", transfer_seen="")
        if ff.contains_any(text, ETA_KEYWORDS):
            return answer("eta")
        if ff.contains_any(text, MISSING_KEYWORDS):
            return answer("missing")
        if ff.contains_any(text, FAIL_KEYWORDS):
            return answer("fail")
        if ff.contains_any(text, HOW_KEYWORDS):
            return answer("howto")
        if ff.should_keep_clarify_lock(text):
            return clarify_reply(), pack(transfer_flow="awaiting_clarify", transfer_seen=seen)
        # 未命中本场景：释放澄清态，避免换话题仍被同一句锁死
        return None, pack(transfer_flow="idle", transfer_seen="")

    if ff.contains_any(text, ASK_TRANSFER_KEYWORDS):
        if ff.contains_any(text, ff.HUMAN_KEYWORDS):
            return suggest_transfer_reply(), pack(transfer_flow="idle", transfer_seen="")
        if ff.contains_any(text, ETA_KEYWORDS):
            return answer("eta")
        if ff.contains_any(text, MISSING_KEYWORDS):
            return answer("missing")
        if ff.contains_any(text, FAIL_KEYWORDS):
            return answer("fail")
        if ff.contains_any(text, HOW_KEYWORDS):
            return answer("howto")
        return clarify_reply(), pack(transfer_flow="awaiting_clarify", transfer_seen="")

    return None, state
