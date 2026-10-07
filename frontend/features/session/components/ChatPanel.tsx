"use client";

import { useEffect, useRef, useState } from "react";

import type { HistoryItem, MessageReply, QuickReply } from "@/lib/api/session";
import { copyTextToClipboard } from "@/lib/clipboard";
import { chatScrollBehavior } from "../chatScroll";
import { emptyChatState } from "../bannerView";
import type { UiMode } from "../mode";
import { isControlVisible } from "../mode";
import {
  sessionStatusLabel,
  shouldShowReplyMeta,
  showComposer,
  showEndedCard,
  canStartConsult,
  showPendingReply,
  composerBusyHint,
  isReplyLocked,
  shouldAutoFocusComposer,
  latestAssistantText,
  copyReplyButtonLabel,
  formatTranscript,
  copyTranscriptButtonLabel,
  COPY_FAIL_HINT,
  type BusyKind,
  type StatusCue,
} from "../guestView";
import { emptyHintAction } from "../bannerView";
import { resolveDisplayedQuickReplies } from "../quickReplies";

type Props = {
  mode: UiMode;
  sessionId: string | null;
  status: string;
  history: HistoryItem[];
  lastReply: MessageReply | null;
  input: string;
  busy: boolean;
  busyLabel: BusyKind;
  statusCue?: StatusCue;
  canChat: boolean;
  onStartConsult: () => void;
  onGuide: () => void;
  onAskTransfer: () => void;
  onInputChange: (v: string) => void;
  onSend: (text?: string) => void;
  onEmptyHint: (text: string) => void;
  onSpecial: (id: string) => void;
};

export function ChatPanel({
  mode,
  sessionId,
  status,
  history,
  lastReply,
  input,
  busy,
  busyLabel,
  statusCue = null,
  canChat,
  onStartConsult,
  onGuide,
  onAskTransfer,
  onInputChange,
  onSend,
  onEmptyHint,
  onSpecial,
}: Props) {
  const ended = showEndedCard(status);
  const composerOn = showComposer(status, sessionId);
  const displayed = resolveDisplayedQuickReplies({
    status,
    canChat,
    backendReplies: lastReply?.quick_replies,
  });
  const visibleChips: QuickReply[] = displayed.primary;
  const pending = showPendingReply(busyLabel, statusCue);
  const waitHint = composerBusyHint(busyLabel, statusCue);
  const composerLocked = isReplyLocked(busyLabel, statusCue);
  const hintAction = emptyHintAction(sessionId, status);
  const empty = emptyChatState({
    sessionId,
    busyStart: busy && busyLabel === "start",
  });
  const scrollEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const focusStateRef = useRef({ composerOn: false, locked: true });
  const copyTimerRef = useRef<number | null>(null);
  const [copyFlash, setCopyFlash] = useState<"reply" | "transcript" | null>(null);
  const [copyFail, setCopyFail] = useState(false);
  const copyText = latestAssistantText(history);
  const transcriptText = formatTranscript(history);
  const historyTail = history.length
    ? `${history.length}-${history[history.length - 1]?.role}-${history[history.length - 1]?.created_at}`
    : "empty";

  useEffect(() => {
    scrollEndRef.current?.scrollIntoView({ behavior: chatScrollBehavior(), block: "end" });
  }, [historyTail, pending, lastReply?.spoken_text]);

  useEffect(() => {
    const prev = focusStateRef.current;
    const shouldFocus = shouldAutoFocusComposer({
      composerOn,
      locked: composerLocked,
      prevComposerOn: prev.composerOn,
      prevLocked: prev.locked,
    });
    focusStateRef.current = { composerOn, locked: composerLocked };
    if (!shouldFocus) return;
    const timer = window.setTimeout(() => {
      inputRef.current?.focus({ preventScroll: true });
    }, 0);
    return () => window.clearTimeout(timer);
  }, [composerOn, composerLocked]);

  useEffect(() => {
    return () => {
      if (copyTimerRef.current) window.clearTimeout(copyTimerRef.current);
    };
  }, []);

  function flashCopy(kind: "reply" | "transcript") {
    setCopyFail(false);
    setCopyFlash(kind);
    if (copyTimerRef.current) window.clearTimeout(copyTimerRef.current);
    copyTimerRef.current = window.setTimeout(() => {
      setCopyFlash(null);
      copyTimerRef.current = null;
    }, 1600);
  }

  async function copyLatestReply() {
    if (!copyText) return;
    const ok = await copyTextToClipboard(copyText);
    if (!ok) {
      setCopyFail(true);
      return;
    }
    flashCopy("reply");
  }

  async function copyFullTranscript() {
    if (!transcriptText) return;
    const ok = await copyTextToClipboard(transcriptText);
    if (!ok) {
      setCopyFail(true);
      return;
    }
    flashCopy("transcript");
  }

  return (
    <section className={`chat-panel${composerLocked ? " is-reply-locked" : ""}`} aria-label="对话">
      {composerLocked && waitHint ? (
        <div className="reply-lock-strip" role="status" aria-live="polite">
          {waitHint}
        </div>
      ) : null}
      <div className="chat-toolbar">
        {!ended ? (
          <button type="button" className="btn" disabled={!canStartConsult(busy)} onClick={onStartConsult}>
            {busy && busyLabel === "start"
              ? "开始中…"
              : mode === "guest"
                ? "开始咨询"
                : "创建会话"}
          </button>
        ) : null}
        {mode === "lab" ? (
          <button type="button" className="btn ghost" disabled={busy || !canChat} onClick={onGuide}>
            展示引导
          </button>
        ) : null}
        <button type="button" className="btn danger" disabled={busy || !canChat} onClick={onAskTransfer}>
          转人工
        </button>
        {mode === "lab" ? (
          <span className="session-pill">{sessionStatusLabel(mode, sessionId, status)}</span>
        ) : null}
      </div>
      {mode === "guest" && !sessionId ? (
        <p className="identity-disclosure" role="note">
          数字人客服 · 资金与身份操作请走官方渠道
        </p>
      ) : null}

      {ended ? (
        <div className="ended-card" role="status">
          <h2>已转接人工客服</h2>
          <p>本轮数字人咨询已结束，下方输入框已关闭。</p>
          <button
            type="button"
            className="btn ended-restart"
            disabled={!canStartConsult(busy)}
            onClick={onStartConsult}
          >
            {busy && busyLabel === "start" ? "开始中…" : "重新开始咨询"}
          </button>
        </div>
      ) : null}

      <div className="chat-log">
        {history.length === 0 && !ended ? (
          <div className={`empty-state${empty.loading ? " is-loading" : ""}`} role="status">
            <p className="empty-title">{empty.title}</p>
            <p className="empty-body">{empty.body}</p>
            {empty.hints.length > 0 ? (
              <ul className="empty-hints" aria-label="示例问题">
                {empty.hints.map((h) => (
                  <li key={h}>
                    <button
                      type="button"
                      className="empty-hint-btn"
                      disabled={busy || hintAction === "none"}
                      onClick={() => onEmptyHint(h)}
                    >
                      {h}
                    </button>
                  </li>
                ))}
              </ul>
            ) : null}
          </div>
        ) : (
          history.map((item) => (
            <div
              key={`${item.kind || "chat"}-${item.role}-${item.created_at}-${item.text}`}
              className={`bubble ${item.role}${item.kind === "welcome" ? " welcome" : ""}`}
            >
              <span className="bubble-role">
                {item.kind === "welcome" ? "欢迎" : item.role === "user" ? "我" : "客服"}
              </span>
              <p>{item.text}</p>
            </div>
          ))
        )}
        {pending ? (
          <div className="bubble assistant pending" role="status" aria-live="polite">
            <span className="bubble-role">客服</span>
            <p>正在回复…</p>
          </div>
        ) : null}
        <div ref={scrollEndRef} className="chat-log-anchor" aria-hidden />
      </div>

      {shouldShowReplyMeta(mode) && lastReply ? (
        <div className="reply-meta">
          来源 {lastReply.source}
          {lastReply.agent_used ? " · Agent" : ""}
          {lastReply.suggest_transfer_human ? " · 建议转人工" : ""}
          {" · "}
          {lastReply.action_intent} / {lastReply.graphic_template_ref}
        </div>
      ) : null}
      {mode === "lab" && !shouldShowReplyMeta(mode) && lastReply ? (
        <div className="reply-meta soft">客服已回复</div>
      ) : null}
      {mode === "lab" && (copyText || transcriptText) ? (
        <div className="copy-reply-block">
          <div className="copy-reply-row" role="group" aria-label="复制对话">
            {copyText ? (
              <button
                type="button"
                className={`btn ghost copy-reply-btn${copyFlash === "reply" ? " is-copied" : ""}`}
                onClick={() => void copyLatestReply()}
                aria-live="polite"
              >
                {copyReplyButtonLabel(copyFlash === "reply")}
              </button>
            ) : null}
            {transcriptText ? (
              <button
                type="button"
                className={`btn ghost copy-reply-btn${copyFlash === "transcript" ? " is-copied" : ""}`}
                onClick={() => void copyFullTranscript()}
                aria-live="polite"
              >
                {copyTranscriptButtonLabel(copyFlash === "transcript")}
              </button>
            ) : null}
          </div>
          {copyFail ? (
            <p className="copy-fail-hint" role="status">
              {COPY_FAIL_HINT}
            </p>
          ) : null}
        </div>
      ) : null}

      {visibleChips.length > 0 && composerOn ? (
        <div className="chip-row quick-replies" role="group" aria-label="快捷回复">
          {visibleChips.map((chip) => (
            <button
              key={`${chip.label}-${chip.text}`}
              type="button"
              className="btn ghost"
              disabled={busy || !canChat}
              onClick={() => {
                if (chip.label === "转人工" || chip.text === "转人工") {
                  onAskTransfer();
                  return;
                }
                onSend(chip.text);
              }}
            >
              {chip.label}
            </button>
          ))}
        </div>
      ) : null}

      {composerOn ? (
        <form
          className={`composer${composerLocked ? " is-locked" : ""}`}
          onSubmit={(e) => {
            e.preventDefault();
            onSend();
          }}
        >
          <textarea
            ref={inputRef}
            value={input}
            onChange={(e) => onInputChange(e.target.value)}
            onKeyDown={(e) => {
              if (e.key !== "Enter" || e.shiftKey || e.nativeEvent.isComposing) return;
              e.preventDefault();
              if (busy || !canChat || !input.trim()) return;
              onSend();
            }}
            rows={mode === "guest" ? 2 : 3}
            placeholder="例如：查余额、办信用卡、网点营业时间…"
            disabled={busy || !canChat}
            aria-describedby={waitHint ? "composer-busy-hint" : undefined}
          />
          {waitHint ? (
            <p id="composer-busy-hint" className="composer-busy-hint" role="status">
              {waitHint}
            </p>
          ) : null}
          <button type="submit" className="btn composer-send" disabled={busy || !canChat || !input.trim()}>
            {busy && busyLabel === "send" ? "发送中…" : "发送"}
          </button>
        </form>
      ) : null}

      {isControlVisible(mode, "special-commands") ? (
        <div className="special-row">
          <span className="hint">特殊指令</span>
          {["0001", "0002", "0003", "0004", "0005"].map((id) => (
            <button
              key={id}
              type="button"
              className="btn ghost tiny"
              disabled={busy || !canChat}
              onClick={() => onSpecial(id)}
            >
              {id}
            </button>
          ))}
        </div>
      ) : null}
    </section>
  );
}
