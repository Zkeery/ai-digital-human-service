import { describe, expect, it } from "vitest";

import { ApiError } from "../lib/api/client";
import {
  autoDismissMs,
  bannerClassName,
  emptyChatState,
  emptyHintAction,
  errorBanner,
  shouldAnnounceSuccess,
} from "../features/session/bannerView";

describe("banner view", () => {
  it("auto-dismisses ok and warn, keeps err", () => {
    expect(autoDismissMs("ok")).toBe(3200);
    expect(autoDismissMs("warn")).toBe(8000);
    expect(autoDismissMs("warn", "rate")).toBe(10000);
    expect(autoDismissMs("err")).toBeNull();
  });

  it("quiets guest send and start success", () => {
    expect(shouldAnnounceSuccess("guest", "发送")).toBe(false);
    expect(shouldAnnounceSuccess("guest", "开始咨询")).toBe(false);
    expect(shouldAnnounceSuccess("guest", "转人工")).toBe(true);
    expect(shouldAnnounceSuccess("lab", "发送")).toBe(true);
  });

  it("maps rate limit and network to banner tones", () => {
    const rate = errorBanner(new ApiError(429, "RATE_LIMITED", "too many"), "guest");
    expect(rate.kind).toBe("warn");
    expect(rate.tone).toBe("rate");
    expect(rate.text).toContain("稍后再试");
    expect(bannerClassName(rate)).toContain("banner-tone-rate");

    const net = errorBanner(new TypeError("Failed to fetch"), "guest", "start");
    expect(net.kind).toBe("err");
    expect(net.tone).toBe("network");
    expect(net.text).toContain("连不上客服");
    expect(net.retry).toBe("start");
  });

  it("builds empty chat copy for idle / ready / loading", () => {
    const idle = emptyChatState({ sessionId: null, busyStart: false });
    expect(idle.title).toContain("开始");
    expect(idle.body).toContain("示例问题");
    expect(idle.loading).toBe(false);
    expect(idle.hints.length).toBeGreaterThan(0);

    const ready = emptyChatState({ sessionId: "s1", busyStart: false });
    expect(ready.title).toContain("问题");
    expect(ready.hints).toContain("查余额");

    const loading = emptyChatState({ sessionId: null, busyStart: true });
    expect(loading.loading).toBe(true);
    expect(loading.title).toContain("准备");
  });

  it("routes empty hint clicks before / during / after consult", () => {
    expect(emptyHintAction(null, "idle")).toBe("start_then_send");
    expect(emptyHintAction("s1", "active")).toBe("send");
    expect(emptyHintAction("s1", "transferred")).toBe("none");
  });
});
