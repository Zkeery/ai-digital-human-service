import { describe, expect, it } from "vitest";

import { applyLocalUserEchoes, applyWelcomeBubble } from "../features/session/historyMerge";

describe("applyLocalUserEchoes", () => {
  it("keeps original typed card number when server history is masked", () => {
    const items = [
      { role: "assistant" as const, text: "欢迎", created_at: "1" },
      { role: "user" as const, text: "卡号****怎么绑", created_at: "2" },
      { role: "assistant" as const, text: "请打开 App 绑卡", created_at: "3" },
    ];
    const out = applyLocalUserEchoes(items, ["卡号6222021234567890123怎么绑"]);
    expect(out[1].text).toBe("卡号6222021234567890123怎么绑");
    expect(out[2].text).toBe("请打开 App 绑卡");
  });

  it("aligns from the end when echoes outnumber visible user rows", () => {
    const items = [{ role: "user" as const, text: "****", created_at: "1" }];
    const out = applyLocalUserEchoes(items, ["旧的一句", "最新一句"]);
    expect(out[0].text).toBe("最新一句");
  });
});

describe("applyWelcomeBubble", () => {
  const welcome =
    "您好，我是零售金融数字人客服。可咨询账户、转账、卡片、登录密码问题、信用卡、理财说明书、网点或投诉。请直接说明问题；查账、转账、改密等需本人在官方渠道办理。";

  it("does not label post-user greeting reply as welcome even if text matches", () => {
    const items = [
      { role: "user" as const, text: "客服你好", created_at: "1" },
      { role: "assistant" as const, text: welcome, created_at: "2" },
    ];
    const out = applyWelcomeBubble(items, welcome);
    expect(out[0].kind).toBe("welcome");
    expect(out[0].text).toBe(welcome);
    expect(out[1].role).toBe("user");
    expect(out[2].kind).toBe("chat");
    expect(out[2].text).toBe(welcome);
  });

  it("marks only the pre-user matching assistant as welcome", () => {
    const items = [
      { role: "assistant" as const, text: welcome, created_at: "1" },
      { role: "user" as const, text: "你好", created_at: "2" },
      { role: "assistant" as const, text: welcome, created_at: "3" },
    ];
    const out = applyWelcomeBubble(items, welcome);
    expect(out).toHaveLength(3);
    expect(out[0].kind).toBe("welcome");
    expect(out[2].kind).toBe("chat");
  });
});
