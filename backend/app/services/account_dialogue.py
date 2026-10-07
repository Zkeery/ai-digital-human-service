from __future__ import annotations

from typing import Any

from app.services import finance_followup as ff
from app.services import return_dialogue as rd

# 账户／余额／流水：短澄清 → 分支答后保留选项并追问

ASK_ACCOUNT_KEYWORDS = (
    "查余额",
    "看余额",
    "账户余额",
    "余额查询",
    "查流水",
    "看流水",
    "交易明细",
    "账单明细",
    "账户查询",
    "查账户",
    "余额",
    "流水",
    "余额对不上",
)
BALANCE_KEYWORDS = ("查余额", "看余额", "账户余额", "余额查询", "怎么查余额")
LEDGER_KEYWORDS = ("查流水", "看流水", "交易明细", "账单明细", "怎么查流水")
MISMATCH_KEYWORDS = ("余额对不上", "金额不对", "少了一笔", "多扣了", "流水不对")

TOPIC_LABELS = {
    "balance": "查余额",
    "ledger": "查流水",
    "mismatch": "余额对不上",
}
TOPIC_ORDER = ("balance", "ledger", "mismatch")

_BUSY = (
    "transfer_flow",
    "card_flow",
    "auth_flow",
    "credit_flow",
    "wealth_flow",
    "branch_flow",
    "complaint_flow",
)


def clarify_reply() -> dict[str, Any]:
    return rd._reply(
        "请问您要查余额、查流水，还是余额有出入？请点下方选项。",
        "faq:account_clarify",
        action="none",
    )


def done_reply() -> dict[str, Any]:
    return rd._reply(
        "好的。如还有账户问题，可随时再问；需要同事协助请点「转人工」。",
        "faq:account_done",
        action="none",
        suggest_transfer=True,
    )


def balance_body() -> str:
    return (
        "请打开 App 或网银，进入「账户」或「我的资产」，页面会显示账户余额。"
        "若无该入口或无法登录，请点「转人工」。"
    )


def ledger_body() -> str:
    return (
        "请打开 App 或网银，进入「账户明细」或「交易记录」，可按日期筛选流水。"
        "若找不到某笔交易或页面报错，请记录交易时间与金额后点「转人工」。"
    )


def mismatch_body() -> str:
    return (
        "请先截取余额页或对应流水截图，并记下有出入的时间与金额。"
        "本客服无法查询银行核心账务，请点「转人工」由同事核对。"
    )


def suggest_transfer_reply() -> dict[str, Any]:
    return rd._reply(
        "好的，请点「转人工」，我帮您接通同事。",
        "faq:account_suggest_transfer",
        action="transfer_announce",
        suggest_transfer=True,
    )


def _topic_reply(topic: str, seen: set[str]) -> tuple[dict[str, Any], set[str]]:
    bodies = {"balance": balance_body, "ledger": ledger_body, "mismatch": mismatch_body}
    graphics = {
        "balance": "faq:account_balance",
        "ledger": "faq:account_ledger",
        "mismatch": "faq:account_mismatch",
    }
    new_seen = set(seen)
    new_seen.add(topic)
    spoken = bodies[topic]() + ff.follow_up(
        new_seen,
        TOPIC_LABELS,
        TOPIC_ORDER,
        closing="如还需核对账务，请点「转人工」，或直接说其他问题。",
    )
    return (
        rd._reply(spoken, graphics[topic], action="none", suggest_transfer=True),
        new_seen,
    )


def try_account_dialogue(
    text: str,
    state: dict[str, Any],
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    for key in _BUSY:
        if state.get(key, "idle") != "idle":
            return None, state

    account = state.get("account_flow", "idle")
    seen = ff.parse_seen(state.get("account_seen"), TOPIC_LABELS)

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
            "account_flow": account,
            "account_seen": ff.dump_seen(seen, TOPIC_ORDER),
            "transfer_flow": "idle",
            "transfer_seen": "",
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
        if "account_seen" in kwargs and isinstance(kwargs["account_seen"], set):
            base["account_seen"] = ff.dump_seen(kwargs["account_seen"], TOPIC_ORDER)
        return base

    def answer(topic: str) -> tuple[dict[str, Any], dict[str, Any]]:
        reply, new_seen = _topic_reply(topic, seen)
        if len(new_seen) >= len(TOPIC_ORDER):
            return reply, pack(account_flow="idle", account_seen="")
        return reply, pack(account_flow="awaiting_clarify", account_seen=new_seen)

    if account == "awaiting_clarify":
        if ff.contains_any(text, ff.HUMAN_KEYWORDS):
            return suggest_transfer_reply(), pack(account_flow="idle", account_seen="")
        if ff.contains_any(text, ff.DONE_KEYWORDS):
            return done_reply(), pack(account_flow="idle", account_seen="")
        if ff.contains_any(text, MISMATCH_KEYWORDS):
            return answer("mismatch")
        if ff.contains_any(text, LEDGER_KEYWORDS):
            return answer("ledger")
        if ff.contains_any(text, BALANCE_KEYWORDS) or ff.contains_any(text, ("余额",)):
            return answer("balance")
        if ff.should_keep_clarify_lock(text):
            return clarify_reply(), pack(account_flow="awaiting_clarify", account_seen=seen)
        # 未命中本场景：释放澄清态，避免换话题仍被同一句锁死
        return None, pack(account_flow="idle", account_seen="")

    if ff.contains_any(text, ASK_ACCOUNT_KEYWORDS):
        if ff.contains_any(text, ff.HUMAN_KEYWORDS):
            return suggest_transfer_reply(), pack(account_flow="idle", account_seen="")
        if ff.contains_any(text, MISMATCH_KEYWORDS):
            return answer("mismatch")
        if ff.contains_any(text, LEDGER_KEYWORDS) and not ff.contains_any(text, ("余额",)):
            return answer("ledger")
        if ff.contains_any(text, BALANCE_KEYWORDS):
            return answer("balance")
        return clarify_reply(), pack(account_flow="awaiting_clarify", account_seen="")

    return None, state
