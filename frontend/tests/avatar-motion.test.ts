import { describe, expect, it } from "vitest";

import {
  avatarFrameClass,
  avatarMotionPhase,
  avatarSpokenCaption,
  showSpeechWave,
} from "../features/session/avatarMotion";

describe("avatarMotion", () => {
  it("maps cues to idle / thinking / speaking", () => {
    expect(avatarMotionPhase(null, null)).toBe("idle");
    expect(avatarMotionPhase("send", null)).toBe("thinking");
    expect(avatarMotionPhase(null, "replying")).toBe("thinking");
    expect(avatarMotionPhase(null, "speaking")).toBe("speaking");
    expect(avatarMotionPhase("send", "speaking")).toBe("speaking");
  });

  it("builds frame class names", () => {
    expect(avatarFrameClass("idle")).toBe("avatar-frame is-idle");
    expect(avatarFrameClass("thinking")).toBe("avatar-frame is-busy is-thinking");
    expect(avatarFrameClass("speaking")).toBe("avatar-frame is-busy is-speaking");
  });

  it("shows wave only while speaking", () => {
    expect(showSpeechWave("speaking")).toBe(true);
    expect(showSpeechWave("idle")).toBe(false);
    expect(showSpeechWave("thinking")).toBe(false);
  });

  it("clips spoken caption during speaking", () => {
    expect(avatarSpokenCaption("已就绪", "", "speaking")).toBe("已就绪");
    expect(avatarSpokenCaption("已就绪", "查额度请打开 App", "idle")).toBe("已就绪");
    expect(avatarSpokenCaption("已就绪", "查额度请打开 App", "speaking")).toBe(
      "查额度请打开 App",
    );
    const long = "一二三四五六七八九十一二三四五六七八九十一二三四五六七八九十超出";
    const clipped = avatarSpokenCaption("底", long, "speaking", 10);
    expect(clipped.endsWith("…")).toBe(true);
    expect(clipped.length).toBe(11);
  });
});
