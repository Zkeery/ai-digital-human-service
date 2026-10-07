import { describe, expect, it } from "vitest";

import { ApiError, apiBase } from "../lib/api/client";
import { formatApiError } from "../lib/api/errors";

describe("api helpers", () => {
  it("defaults api base to local backend", () => {
    expect(apiBase()).toContain("8050");
  });

  it("formats ApiError with code in lab", () => {
    const msg = formatApiError(new ApiError(409, "SESSION_NOT_ACTIVE", "会话不可用"));
    expect(msg).toContain("SESSION_NOT_ACTIVE");
    expect(msg).toContain("会话不可用");
  });

  it("uses plain language for guest", () => {
    const msg = formatApiError(new ApiError(409, "SESSION_NOT_ACTIVE", "会话不可用"), {
      audience: "guest",
    });
    expect(msg).toContain("重新开始咨询");
    expect(msg).not.toContain("SESSION_NOT_ACTIVE");

    const net = formatApiError(new TypeError("Failed to fetch"), { audience: "guest" });
    expect(net).toContain("连不上客服");
    expect(net).not.toContain("Failed to fetch");
  });
});
