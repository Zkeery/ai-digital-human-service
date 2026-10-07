/** 本地数字人画面动效相位（非现网 RTC；仅加强体感）。 */

import type { BusyKind, StatusCue } from "./guestView";

export type AvatarMotionPhase = "idle" | "thinking" | "speaking";

export function avatarMotionPhase(
  busyKind: BusyKind = null,
  cue: StatusCue = null,
): AvatarMotionPhase {
  if (cue === "speaking") return "speaking";
  if (
    busyKind === "send" ||
    busyKind === "start" ||
    cue === "replying" ||
    cue === "starting" ||
    cue === "replied"
  ) {
    return "thinking";
  }
  return "idle";
}

export function avatarFrameClass(phase: AvatarMotionPhase): string {
  if (phase === "speaking") return "avatar-frame is-busy is-speaking";
  if (phase === "thinking") return "avatar-frame is-busy is-thinking";
  return "avatar-frame is-idle";
}

export function showSpeechWave(phase: AvatarMotionPhase): boolean {
  return phase === "speaking";
}

/** 口播时底部字幕预览；空文案则回落入口说明。 */
export function avatarSpokenCaption(
  base: string,
  spoken: string | null | undefined,
  phase: AvatarMotionPhase,
  maxLen = 36,
): string {
  if (phase !== "speaking") return base;
  const text = (spoken || "").trim().replace(/\s+/g, " ");
  if (!text) return base;
  if (text.length <= maxLen) return text;
  return `${text.slice(0, maxLen)}…`;
}
