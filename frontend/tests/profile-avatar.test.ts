import { describe, expect, it } from "vitest";

import {
  normalizeProfileKey,
  profileAvatarAlt,
  profileAvatarSrc,
} from "../features/session/profileAvatar";

describe("profileAvatar", () => {
  it("normalizes profile keys", () => {
    expect(normalizeProfileKey("002")).toBe("002");
    expect(normalizeProfileKey("999")).toBe("001");
    expect(normalizeProfileKey("")).toBe("001");
  });

  it("builds static avatar paths", () => {
    expect(profileAvatarSrc("003")).toBe("/avatars/003.svg");
    expect(profileAvatarSrc("bad")).toBe("/avatars/001.svg");
  });

  it("builds alt text", () => {
    expect(profileAvatarAlt("001")).toBe("形象 001");
    expect(profileAvatarAlt("002", "信用卡专窗")).toBe("信用卡专窗 · 形象 002");
  });
});
