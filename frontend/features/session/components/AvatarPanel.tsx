"use client";

import {
  avatarFrameClass,
  avatarMotionPhase,
  avatarSpokenCaption,
  showSpeechWave,
} from "../avatarMotion";
import { speakingBadgeLabel, type BusyKind, type StatusCue } from "../guestView";
import type { UiMode } from "../mode";
import { isControlVisible } from "../mode";
import { profileAvatarAlt, profileAvatarSrc } from "../profileAvatar";

const PROFILES = [
  { id: "001", label: "形象 001" },
  { id: "002", label: "形象 002" },
  { id: "003", label: "形象 003" },
  { id: "004", label: "形象 004" },
];

type Props = {
  mode: UiMode;
  profile: string;
  roomHint: string;
  logoUrl?: string;
  entryLabel?: string;
  busy: boolean;
  busyKind?: BusyKind;
  statusCue?: StatusCue;
  /** 当前本地口播原文，用于底部字幕预览（非现网）。 */
  spokenLine?: string;
  canChat: boolean;
  hasLastReply: boolean;
  hasCommand: boolean;
  onProfileChange: (id: string) => void;
  onInit: () => void;
  onPush: () => void;
  onStarted: () => void;
  onCheckSync: () => void;
  onSimulateFallback: () => void;
};

export function AvatarPanel({
  mode,
  profile,
  roomHint,
  logoUrl = "",
  entryLabel = "",
  busy,
  busyKind = null,
  statusCue = null,
  spokenLine = "",
  canChat,
  hasLastReply,
  hasCommand,
  onProfileChange,
  onInit,
  onPush,
  onStarted,
  onCheckSync,
  onSimulateFallback,
}: Props) {
  const phase = avatarMotionPhase(busyKind, statusCue);
  const frameClass = avatarFrameClass(phase);
  const waveOn = showSpeechWave(phase);
  const badge = speakingBadgeLabel(busyKind, statusCue);
  const showLabActions = mode === "lab";
  const captionBase =
    mode === "guest"
      ? `${entryLabel || "金融咨询数字人"} · ${roomHint}`
      : `${entryLabel ? `${entryLabel} · ` : ""}形象 ${profile} · ${roomHint}`;
  const caption = avatarSpokenCaption(captionBase, spokenLine, phase);
  const figureSrc = profileAvatarSrc(profile);
  const figureAlt = profileAvatarAlt(profile, entryLabel);
  return (
    <section className="avatar-panel" aria-label="数字人画面">
      <div className={frameClass} aria-busy={phase !== "idle" || busy}>
        <div className="avatar-glow" />
        {badge ? (
          <p className="avatar-speaking-badge" role="status">
            {badge}
          </p>
        ) : null}
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img className="avatar-figure" src={figureSrc} alt={figureAlt} />
        {waveOn ? (
          <div className="avatar-speech-wave" aria-hidden="true">
            <span />
            <span />
            <span />
            <span />
            <span />
          </div>
        ) : null}
        {logoUrl ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img className="avatar-entry-badge" src={logoUrl} alt={entryLabel || "入口标识"} />
        ) : null}
        <p className="avatar-caption">{caption}</p>
      </div>
      {showLabActions ? (
        <div className="panel-actions">
          <label className="inline-label">
            形象
            <select
              value={profile}
              onChange={(e) => onProfileChange(e.target.value)}
              disabled={busy || !canChat}
            >
              {PROFILES.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.label}
                </option>
              ))}
            </select>
          </label>
          <button type="button" className="btn" disabled={busy || !canChat} onClick={onInit}>
            初始化数字人
          </button>
          {isControlVisible(mode, "push") ? (
            <button type="button" className="btn ghost" disabled={busy || !canChat || !hasLastReply} onClick={onPush}>
              推流最近应答
            </button>
          ) : null}
          {isControlVisible(mode, "stream-started") ? (
            <button type="button" className="btn ghost" disabled={busy || !canChat || !hasCommand} onClick={onStarted}>
              开始展示
            </button>
          ) : null}
          {isControlVisible(mode, "check-sync") ? (
            <button type="button" className="btn ghost" disabled={busy || !canChat} onClick={onCheckSync}>
              检查同步降级
            </button>
          ) : null}
          {isControlVisible(mode, "simulate-fallback") ? (
            <button type="button" className="btn ghost" disabled={busy || !canChat} onClick={onSimulateFallback}>
              模拟 2s 降级
            </button>
          ) : null}
        </div>
      ) : null}
    </section>
  );
}
