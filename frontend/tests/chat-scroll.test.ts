import { describe, expect, it } from "vitest";

import { chatScrollBehaviorFromReducedMotion } from "../features/session/chatScroll";

describe("chatScrollBehaviorFromReducedMotion", () => {
  it("uses smooth scroll when motion is allowed", () => {
    expect(chatScrollBehaviorFromReducedMotion(false)).toBe("smooth");
  });

  it("uses auto when reduced motion preferred", () => {
    expect(chatScrollBehaviorFromReducedMotion(true)).toBe("auto");
  });
});
