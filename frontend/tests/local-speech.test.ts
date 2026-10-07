import { describe, expect, it, vi } from "vitest";

import {
  canUseLocalSpeech,
  clipSpokenText,
  isLocalSpeechEnabledForMode,
  parseLocalSpeechEnabled,
  shouldSpeakWelcomeOnStart,
  showSkipLocalSpeech,
  speakLocalText,
  cancelLocalSpeech,
} from "../features/session/localSpeech";

class FakeUtterance {
  text: string;
  lang = "";
  voice: SpeechSynthesisVoice | null = null;
  rate = 1;
  onstart: ((ev: SpeechSynthesisEvent) => void) | null = null;
  onend: ((ev: SpeechSynthesisEvent) => void) | null = null;
  onerror: ((ev: SpeechSynthesisErrorEvent) => void) | null = null;
  constructor(text: string) {
    this.text = text;
  }
}

describe("localSpeech", () => {
  it("defaults local speech to on", () => {
    expect(parseLocalSpeechEnabled(null)).toBe(true);
    expect(parseLocalSpeechEnabled("")).toBe(true);
    expect(parseLocalSpeechEnabled("1")).toBe(true);
    expect(parseLocalSpeechEnabled("0")).toBe(false);
    expect(parseLocalSpeechEnabled("off")).toBe(false);
  });

  it("keeps guest speech always on; lab follows stored switch", () => {
    expect(isLocalSpeechEnabledForMode("guest", false)).toBe(true);
    expect(isLocalSpeechEnabledForMode("guest", true)).toBe(true);
    expect(isLocalSpeechEnabledForMode("lab", false)).toBe(false);
    expect(isLocalSpeechEnabledForMode("lab", true)).toBe(true);
  });

  it("speaks welcome only for guest start without follow-up", () => {
    expect(
      shouldSpeakWelcomeOnStart({ mode: "guest", localSpeechOn: true, followUp: "" }),
    ).toBe(true);
    expect(
      shouldSpeakWelcomeOnStart({ mode: "guest", localSpeechOn: true, followUp: "查余额" }),
    ).toBe(false);
    expect(
      shouldSpeakWelcomeOnStart({ mode: "lab", localSpeechOn: true, followUp: "" }),
    ).toBe(false);
    // 访客播报固定开：即使本地开关记为关，欢迎口播仍播
    expect(
      shouldSpeakWelcomeOnStart({ mode: "guest", localSpeechOn: false, followUp: "" }),
    ).toBe(true);
  });

  it("shows skip only while speaking cue is active", () => {
    expect(showSkipLocalSpeech("speaking")).toBe(true);
    expect(showSkipLocalSpeech("replying")).toBe(false);
    expect(showSkipLocalSpeech(null)).toBe(false);
  });

  it("clips long spoken text", () => {
    expect(clipSpokenText("  查余额  ")).toBe("查余额");
    expect(clipSpokenText("")).toBe("");
    const long = "啊".repeat(400);
    const clipped = clipSpokenText(long, 20);
    expect(clipped.length).toBeLessThanOrEqual(20);
    expect(clipped.endsWith("…")).toBe(true);
  });

  it("reports unsupported when synth missing", () => {
    expect(canUseLocalSpeech(null, FakeUtterance as unknown as typeof SpeechSynthesisUtterance)).toBe(
      false,
    );
    const unsupported = vi.fn();
    const ended = vi.fn();
    expect(
      speakLocalText(
        "你好",
        { onUnsupported: unsupported, onEnd: ended },
        null,
        FakeUtterance as unknown as typeof SpeechSynthesisUtterance,
      ),
    ).toBe(false);
    expect(unsupported).toHaveBeenCalled();
    expect(ended).toHaveBeenCalled();
  });

  it("queues utterance when synth available", () => {
    vi.useFakeTimers();
    const speak = vi.fn();
    const cancel = vi.fn();
    const synth = {
      cancel,
      speak,
      getVoices: () => [{ lang: "zh-CN", name: "Tingting" } as SpeechSynthesisVoice],
    };
    const started = vi.fn();
    const ok = speakLocalText(
      "网点营业时间",
      { onStart: started },
      synth,
      FakeUtterance as unknown as typeof SpeechSynthesisUtterance,
    );
    expect(ok).toBe(true);
    expect(cancel).toHaveBeenCalled();
    expect(speak).not.toHaveBeenCalled();
    vi.runAllTimers();
    expect(speak).toHaveBeenCalledTimes(1);
    expect(started).toHaveBeenCalledTimes(1);
    const utter = speak.mock.calls[0][0] as FakeUtterance;
    expect(utter.text).toContain("网点");
    expect(utter.lang).toBe("zh-CN");
    utter.onstart?.(null as unknown as SpeechSynthesisEvent);
    expect(started).toHaveBeenCalledTimes(1);
    cancelLocalSpeech(synth);
    expect(cancel).toHaveBeenCalledTimes(2);
    vi.useRealTimers();
  });
});
