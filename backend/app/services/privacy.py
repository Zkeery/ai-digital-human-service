"""敏感信息脱敏（D8）：落库／事件不保留完整卡号、证件号、密码、验证码。

占位只用星号。口播里的「密码、信用卡」列举不得误伤——密码／验证码须带明确赋值分隔符。
"""

from __future__ import annotations

import re

_ID18 = re.compile(r"(?<!\d)\d{17}[\dXx](?!\d)")
_ID15 = re.compile(r"(?<!\d)\d{15}(?!\d)")
# 13～19 位数字串（可夹空格／短横），覆盖卡号等
_CARD = re.compile(r"(?<!\d)(?:\d[ \-]?){13,19}\d(?!\d)")
# 必须出现「是／为／=／:」等赋值，避免「密码、信用卡」列举被吃掉
_PASSWORD = re.compile(
    r"((?:密码|口令|passwd|password)\s*[是为:=：]\s*)\S+",
    re.IGNORECASE,
)
_OTP = re.compile(
    r"((?:验证码|校验码|动态码)\s*[是为:=：]\s*)\d{4,8}",
    re.IGNORECASE,
)


def redact_sensitive(text: str | None) -> str:
    if not text:
        return ""
    out = text
    out = _PASSWORD.sub(r"\1****", out)
    out = _OTP.sub(r"\1****", out)
    out = _ID18.sub("****", out)
    out = _ID15.sub("****", out)
    out = _CARD.sub("****", out)
    return out


def redact_payload(payload: dict) -> dict:
    def walk(value):
        if isinstance(value, str):
            return redact_sensitive(value)
        if isinstance(value, dict):
            return {k: walk(v) for k, v in value.items()}
        if isinstance(value, list):
            return [walk(v) for v in value]
        return value

    return walk(dict(payload))
