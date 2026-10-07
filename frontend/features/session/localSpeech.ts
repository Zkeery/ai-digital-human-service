/** 本地口播预览（浏览器 speechSynthesis；非现网 RTC）。 */

export const LOCAL_SPEECH_KEY = "dh_local_speech";

const MAX_SPOKEN_CHARS = 280;

export type LocalSpeechHandlers = {
  onStart?: () => void;
  onEnd?: () => void;
  onUnsupported?: () => void;
  onError?: (reason: string) => void;
};

export function parseLocalSpeechEnabled(raw: string | null | undefined): boolean {
  if (raw == null || raw === "") return true;
  return raw !== "0" && raw.toLowerCase() !== "false" && raw !== "off";
}

/** 访客播报固定开启；验收模式才跟随本地开关。 */
export function isLocalSpeechEnabledForMode(
  mode: "guest" | "lab",
  storedOn: boolean,
): boolean {
  if (mode === "guest") return true;
  return storedOn;
}

/** 开场欢迎口播：仅访客、且没有连带发送时朗读（访客播报固定开）。 */
export function shouldSpeakWelcomeOnStart(opts: {
  mode: "guest" | "lab";
  localSpeechOn: boolean;
  followUp: string;
}): boolean {
  const speechOn = isLocalSpeechEnabledForMode(opts.mode, opts.localSpeechOn);
  return opts.mode === "guest" && speechOn && !opts.followUp.trim();
}

/** 本地口播进行中时可展示「跳过口播」。 */
export function showSkipLocalSpeech(statusCue: string | null | undefined): boolean {
  return statusCue === "speaking";
}

export function clipSpokenText(text: string, maxChars = MAX_SPOKEN_CHARS): string {
  const trimmed = (text || "").replace(/\s+/g, " ").trim();
  if (!trimmed) return "";
  if (trimmed.length <= maxChars) return trimmed;
  return `${trimmed.slice(0, Math.max(0, maxChars - 1))}…`;
}

export function canUseLocalSpeech(
  synth: SpeechSynthesisLike | null | undefined = defaultSynth(),
  UtteranceCtor: typeof SpeechSynthesisUtterance | undefined = defaultUtteranceCtor(),
): boolean {
  return Boolean(synth && UtteranceCtor);
}

function defaultUtteranceCtor(): typeof SpeechSynthesisUtterance | undefined {
  if (typeof SpeechSynthesisUtterance === "undefined") return undefined;
  return SpeechSynthesisUtterance;
}

type SpeechSynthesisLike = {
  cancel: () => void;
  speak: (u: SpeechSynthesisUtterance) => void;
  getVoices?: () => SpeechSynthesisVoice[];
};

function defaultSynth(): SpeechSynthesisLike | null {
  if (typeof window === "undefined") return null;
  return window.speechSynthesis ?? null;
}

function pickZhVoice(synth: SpeechSynthesisLike): SpeechSynthesisVoice | null {
  const voices = typeof synth.getVoices === "function" ? synth.getVoices() : [];
  if (!voices.length) return null;
  const zh =
    voices.find((v) => /^zh(-|_)/i.test(v.lang)) ||
    voices.find((v) => /chinese|中文|普通话/i.test(v.name));
  return zh || null;
}

let activeUtterance: SpeechSynthesisUtterance | null = null;

export function cancelLocalSpeech(
  synth: SpeechSynthesisLike | null | undefined = defaultSynth(),
): void {
  activeUtterance = null;
  try {
    synth?.cancel();
  } catch {
    /* ignore */
  }
}

/** 朗读口播文本；返回是否真正开始排队朗读。 */
export function speakLocalText(
  text: string,
  handlers: LocalSpeechHandlers = {},
  synth: SpeechSynthesisLike | null | undefined = defaultSynth(),
  UtteranceCtor: typeof SpeechSynthesisUtterance | undefined = defaultUtteranceCtor(),
): boolean {
  const spoken = clipSpokenText(text);
  if (!spoken) {
    handlers.onEnd?.();
    return false;
  }
  if (!canUseLocalSpeech(synth, UtteranceCtor) || !synth || !UtteranceCtor) {
    handlers.onUnsupported?.();
    handlers.onEnd?.();
    return false;
  }

  cancelLocalSpeech(synth);
  const utter = new UtteranceCtor(spoken);
  utter.lang = "zh-CN";
  utter.rate = 1;
  const voice = pickZhVoice(synth);
  if (voice) utter.voice = voice;

  let startedNotified = false;
  const notifyStart = () => {
    if (startedNotified) return;
    startedNotified = true;
    handlers.onStart?.();
  };

  utter.onstart = () => notifyStart();
  utter.onend = () => {
    if (activeUtterance === utter) activeUtterance = null;
    handlers.onEnd?.();
  };
  utter.onerror = () => {
    if (activeUtterance === utter) activeUtterance = null;
    handlers.onError?.("speech_error");
    handlers.onEnd?.();
  };

  activeUtterance = utter;
  // Chrome：同 tick cancel+speak 常无声／不触发 onstart；延后一拍并立刻通知 UI。
  const kick = () => {
    if (activeUtterance !== utter) return;
    try {
      const resumable = synth as SpeechSynthesisLike & { resume?: () => void };
      resumable.resume?.();
      synth.speak(utter);
      notifyStart();
    } catch {
      activeUtterance = null;
      handlers.onError?.("speak_throw");
      handlers.onEnd?.();
    }
  };
  if (typeof setTimeout === "function") setTimeout(kick, 0);
  else kick();
  return true;
}
