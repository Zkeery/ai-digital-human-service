from __future__ import annotations

from typing import Any

from app.services import finance_followup as ff
from app.services import return_dialogue as rd

# 登录／密码／验证码：短澄清 → 分支答后保留选项并追问

ASK_AUTH_KEYWORDS = (
    "登录不上",
    "登陆不上",
    "登不上",
    "登录失败",
    "登陆失败",
    "进不去",
    "忘记密码",
    "找回密码",
    "改密码",
    "重置密码",
    "验证码",
    "收不到验证码",
    "验证码没来",
    "账号锁定",
    "密码锁定",
    "登录问题",
    "登陆问题",
    "密码问题",
)
LOGIN_KEYWORDS = (
    "登录不上",
    "登陆不上",
    "登不上",
    "登录失败",
    "登陆失败",
    "进不去",
    "登不进去",
)
PASSWORD_KEYWORDS = ("忘记密码", "找回密码", "改密码", "重置密码", "密码忘了")
OTP_KEYWORDS = ("收不到验证码", "验证码没来", "验证码收不到", "没收到验证码")

TOPIC_LABELS = {
    "login": "登录不上",
    "password": "忘记密码",
    "otp": "收不到验证码",
}
TOPIC_ORDER = ("login", "password", "otp")

_BUSY = (
    "account_flow",
    "transfer_flow",
    "card_flow",
    "credit_flow",
    "wealth_flow",
    "branch_flow",
    "complaint_flow",
)


def clarify_reply() -> dict[str, Any]:
    return rd._reply(
        "请问是登录失败、忘记密码，还是收不到验证码？请点下方选项。",
        "faq:auth_clarify",
        action="none",
    )


def done_reply() -> dict[str, Any]:
    return rd._reply(
        "好的。如还有登录或密码问题，可随时再问；需要同事协助请点「转人工」。",
        "faq:auth_done",
        action="none",
        suggest_transfer=True,
    )


def login_body() -> str:
    return (
        "请核对：登录账号是否正确、网络是否正常、密码输入法是否切换正确；也可改用短信验证码登录。"
        "若仍无法进入，请点「转人工」。请勿将密码发送给客服。"
    )


def password_body() -> str:
    return (
        "请打开 App 或网银登录页，选择「忘记密码」或「找回密码」，按页面完成身份验证后重置。"
        "若无该入口或身份验证失败，请点「转人工」。请勿将密码发送给客服。"
    )


def otp_body() -> str:
    return (
        "请核对：手机号是否正确、信号是否正常、短信是否被拦截；可等待约一至两分钟后重发。"
        "若仍收不到验证码，请点「转人工」。请勿将验证码发送给客服。"
    )


def suggest_transfer_reply() -> dict[str, Any]:
    return rd._reply(
        "好的，请点「转人工」，我帮您接通同事。",
        "faq:auth_suggest_transfer",
        action="transfer_announce",
        suggest_transfer=True,
    )


def _topic_reply(topic: str, seen: set[str]) -> tuple[dict[str, Any], set[str]]:
    bodies = {"login": login_body, "password": password_body, "otp": otp_body}
    graphics = {
        "login": "faq:auth_login",
        "password": "faq:auth_password",
        "otp": "faq:auth_otp",
    }
    new_seen = set(seen)
    new_seen.add(topic)
    spoken = bodies[topic]() + ff.follow_up(
        new_seen,
        TOPIC_LABELS,
        TOPIC_ORDER,
        closing="如仍无法登录，请点「转人工」，或直接说其他问题。",
    )
    return (
        rd._reply(spoken, graphics[topic], action="none", suggest_transfer=True),
        new_seen,
    )


def try_auth_dialogue(
    text: str,
    state: dict[str, Any],
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    for key in _BUSY:
        if state.get(key, "idle") != "idle":
            return None, state

    auth = state.get("auth_flow", "idle")
    seen = ff.parse_seen(state.get("auth_seen"), TOPIC_LABELS)

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
            "transfer_flow": "idle",
            "transfer_seen": "",
            "card_flow": "idle",
            "card_seen": "",
            "auth_flow": auth,
            "auth_seen": ff.dump_seen(seen, TOPIC_ORDER),
            "credit_flow": "idle",
            "credit_seen": "",
            "wealth_flow": "idle",
            "wealth_seen": "",
            "branch_flow": "idle",
            "branch_seen": "",
        }
        base.update(kwargs)
        if "auth_seen" in kwargs and isinstance(kwargs["auth_seen"], set):
            base["auth_seen"] = ff.dump_seen(kwargs["auth_seen"], TOPIC_ORDER)
        return base

    def answer(topic: str) -> tuple[dict[str, Any], dict[str, Any]]:
        reply, new_seen = _topic_reply(topic, seen)
        if len(new_seen) >= len(TOPIC_ORDER):
            return reply, pack(auth_flow="idle", auth_seen="")
        return reply, pack(auth_flow="awaiting_clarify", auth_seen=new_seen)

    if auth == "awaiting_clarify":
        if ff.contains_any(text, ff.HUMAN_KEYWORDS):
            return suggest_transfer_reply(), pack(auth_flow="idle", auth_seen="")
        if ff.contains_any(text, ff.DONE_KEYWORDS):
            return done_reply(), pack(auth_flow="idle", auth_seen="")
        if ff.contains_any(text, OTP_KEYWORDS) or (
            ff.contains_any(text, ("验证码",))
            and ff.contains_any(text, ("收不到", "没来", "没有"))
        ):
            return answer("otp")
        if ff.contains_any(text, PASSWORD_KEYWORDS):
            return answer("password")
        if ff.contains_any(text, LOGIN_KEYWORDS):
            return answer("login")
        if ff.should_keep_clarify_lock(text):
            return clarify_reply(), pack(auth_flow="awaiting_clarify", auth_seen=seen)
        # 未命中本场景：释放澄清态，避免换话题仍被同一句锁死
        return None, pack(auth_flow="idle", auth_seen="")

    if ff.contains_any(text, ASK_AUTH_KEYWORDS):
        if ff.contains_any(text, ff.HUMAN_KEYWORDS):
            return suggest_transfer_reply(), pack(auth_flow="idle", auth_seen="")
        if ff.contains_any(text, OTP_KEYWORDS) or (
            ff.contains_any(text, ("验证码",))
            and ff.contains_any(text, ("收不到", "没来", "没有"))
        ):
            return answer("otp")
        if ff.contains_any(text, PASSWORD_KEYWORDS):
            return answer("password")
        if ff.contains_any(text, LOGIN_KEYWORDS):
            return answer("login")
        return clarify_reply(), pack(auth_flow="awaiting_clarify", auth_seen="")

    return None, state
