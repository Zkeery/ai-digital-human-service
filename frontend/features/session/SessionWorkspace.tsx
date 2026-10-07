"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { ApiError } from "@/lib/api/client";
import { formatApiError } from "@/lib/api/errors";
import {
  api,
  type ConfigView,
  type HistoryItem,
  type MessageReply,
  type SessionEvent,
} from "@/lib/api/session";

import { trackDh } from "./analytics";
import { AvatarPanel } from "./components/AvatarPanel";
import { AnalyticsPanel } from "./components/AnalyticsPanel";
import { ChatPanel } from "./components/ChatPanel";
import { ConfigBar } from "./components/ConfigBar";
import { EventsPanel } from "./components/EventsPanel";
import { StatsPanel } from "./components/StatsPanel";
import { WalkthroughPanel } from "./components/WalkthroughPanel";
import { isWalkthroughTransfer, walkthroughSendText } from "./walkthrough";
import { TransferConfirm } from "./components/TransferConfirm";
import { RatingModal } from "./components/RatingModal";
import { GuestTipBanner } from "./components/GuestTipBanner";
import { StatusBanner } from "./components/StatusBanner";
import { autoDismissMs, errorBanner, shouldAnnounceSuccess, type Banner } from "./bannerView";
import { sortEventsNewestFirst } from "./eventsView";
import {
  DEFAULT_GUIDE_TEXT,
  avatarStatusHint,
  MIN_STATUS_CUE_MS,
  parseStoredSessionId,
  parseTheme,
  remainingHoldMs,
  waitForPaint,
  statusCueLabel,
  dismissGuestTip,
  shouldShowGuestTip,
  workspaceShellClass,
  followUpSendText,
  SESSION_KEY,
  THEME_KEY,
  type BusyKind,
  type StatusCue,
} from "./guestView";
import {
  LOCAL_SPEECH_KEY,
  isLocalSpeechEnabledForMode,
  cancelLocalSpeech,
  parseLocalSpeechEnabled,
  shouldSpeakWelcomeOnStart,
  speakLocalText,
} from "./localSpeech";
import {
  findEntry,
  resolveSessionEntryId,
  safeAccent,
  safeLogoUrl,
  welcomeTextForEntry,
} from "./entries";
import { applyLocalUserEchoes, applyWelcomeBubble } from "./historyMerge";
import { parseUiMode, UI_MODE_KEY, type UiMode } from "./mode";

export function SessionWorkspace() {
  const [mode, setMode] = useState<UiMode>("guest");
  const [config, setConfig] = useState<ConfigView | null>(null);
  const [selectedEntryId, setSelectedEntryId] = useState("");
  const [entryAccent, setEntryAccent] = useState("#0f766e");
  const [entryLogo, setEntryLogo] = useState("");
  const [activeEntryLabel, setActiveEntryLabel] = useState("");
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [status, setStatus] = useState("idle");
  const [profile, setProfile] = useState("001");
  const [theme, setTheme] = useState<"default" | "ink">("default");
  const [input, setInput] = useState("");
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [localUserEchoes, setLocalUserEchoes] = useState<string[]>([]);
  const [welcomeText, setWelcomeText] = useState<string | null>(null);
  const [lastReply, setLastReply] = useState<MessageReply | null>(null);
  const [lastCommandId, setLastCommandId] = useState<number | null>(null);
  const [roomHint, setRoomHint] = useState("未初始化");
  const [fallbackOn, setFallbackOn] = useState(false);
  const [busy, setBusy] = useState(false);
  const [busyKind, setBusyKind] = useState<BusyKind>(null);
  const [statusCue, setStatusCue] = useState<StatusCue>(null);
  const [localSpeechOn, setLocalSpeechOn] = useState(true);
  const [speakingLine, setSpeakingLine] = useState("");
  const statusCueTimer = useRef<number | null>(null);
  const lastSendRef = useRef<string>("");
  const pendingSpeechRef = useRef<string | null>(null);
  const bannerRetryRef = useRef<"start" | "send" | null>(null);
  const [guestTipRev, setGuestTipRev] = useState(0);
  const [banner, setBanner] = useState<Banner | null>(null);
  const [transferOpen, setTransferOpen] = useState(false);
  const [ratingOpen, setRatingOpen] = useState(false);
  const [ratingScore, setRatingScore] = useState(5);
  const [events, setEvents] = useState<SessionEvent[]>([]);
  const [statsTick, setStatsTick] = useState(0);

  const bumpLabStats = () => {
    if (mode === "lab") setStatsTick((n) => n + 1);
  };

  const changeMode = (next: UiMode) => {
    setMode(next);
    sessionStorage.setItem(UI_MODE_KEY, next);
  };

  const changeTheme = (next: string) => {
    const t = parseTheme(next);
    setTheme(t);
    localStorage.setItem(THEME_KEY, t);
  };

  const changeLocalSpeech = (enabled: boolean) => {
    setLocalSpeechOn(enabled);
    localStorage.setItem(LOCAL_SPEECH_KEY, enabled ? "1" : "0");
    if (!enabled) cancelLocalSpeech();
  };

  const clearSpeakingUi = useCallback(() => {
    setStatusCue((prev) => (prev === "speaking" ? null : prev));
    setRoomHint((prev) => (prev === "本地口播中" ? "已就绪" : prev));
    setSpeakingLine("");
  }, []);

  const skipLocalSpeech = () => {
    cancelLocalSpeech();
    if (statusCueTimer.current) {
      window.clearTimeout(statusCueTimer.current);
      statusCueTimer.current = null;
    }
    clearSpeakingUi();
    trackDh("dh_local_speech", { sessionId: sessionId || undefined, detail: "skip" });
  };

  const speechOn = isLocalSpeechEnabledForMode(mode, localSpeechOn);

  const playLocalSpeech = useCallback(
    (text: string) => {
      if (!isLocalSpeechEnabledForMode(mode, localSpeechOn)) return;
      const spoken = (text || "").trim();
      if (!spoken) return;
      if (statusCueTimer.current) {
        window.clearTimeout(statusCueTimer.current);
        statusCueTimer.current = null;
      }
      // 不等浏览器 onstart：排队成功即显示「本地口播中／跳过口播」与本地动效
      setStatusCue("speaking");
      setRoomHint("本地口播中");
      setSpeakingLine(spoken);
      const ok = speakLocalText(spoken, {
        onStart: () => {
          trackDh("dh_local_speech", { sessionId: sessionId || undefined, detail: "start" });
        },
        onEnd: () => {
          clearSpeakingUi();
          trackDh("dh_local_speech", { sessionId: sessionId || undefined, detail: "end" });
        },
        onUnsupported: () => {
          clearSpeakingUi();
          trackDh("dh_local_speech", {
            sessionId: sessionId || undefined,
            detail: "unsupported",
          });
        },
        onError: (reason) => {
          trackDh("dh_local_speech", {
            sessionId: sessionId || undefined,
            detail: reason.slice(0, 40),
          });
        },
      });
      if (!ok) {
        clearSpeakingUi();
      }
    },
    [clearSpeakingUi, localSpeechOn, mode, sessionId],
  );

  const applyEntryAppearance = useCallback(
    (entryId: string, entries = config?.entries) => {
      const entry = findEntry(entries, entryId);
      if (!entry) return;
      const nextTheme = parseTheme(entry.theme);
      setTheme(nextTheme);
      localStorage.setItem(THEME_KEY, nextTheme);
      setEntryAccent(safeAccent(entry.accent));
      setEntryLogo(safeLogoUrl(entry.logo_url));
      setActiveEntryLabel(entry.label);
    },
    [config?.entries],
  );

  useEffect(() => {
    const root = document.documentElement;
    root.classList.remove("theme-ink", "theme-default");
    root.classList.add(theme === "ink" ? "theme-ink" : "theme-default");
    root.style.setProperty("--accent", entryAccent);
    return () => {
      root.classList.remove("theme-ink", "theme-default");
    };
  }, [theme, entryAccent]);

  const rememberSession = (sid: string | null) => {
    if (sid) sessionStorage.setItem(SESSION_KEY, sid);
    else sessionStorage.removeItem(SESSION_KEY);
  };

  const errorText = (err: unknown, audience: "guest" | "lab" = mode === "guest" ? "guest" : "lab") =>
    formatApiError(err, { audience });

  const refreshConfig = useCallback(async () => {
    const cfg = await api.getConfig();
    setConfig(cfg);
    setSelectedEntryId((prev) => {
      const next =
        prev && cfg.entries?.some((e) => e.id === prev) ? prev : cfg.pilot_entry_id;
      const entry = findEntry(cfg.entries, next);
      if (entry) {
        setEntryAccent(safeAccent(entry.accent));
        setEntryLogo(safeLogoUrl(entry.logo_url));
        setActiveEntryLabel(entry.label);
        const nextTheme = parseTheme(entry.theme);
        setTheme(nextTheme);
        localStorage.setItem(THEME_KEY, nextTheme);
      }
      return next;
    });
    return cfg;
  }, []);

  const refreshEvents = useCallback(async (sid: string | null) => {
    if (!sid) {
      setEvents([]);
      return;
    }
    const list = await api.events(sid);
    setEvents(sortEventsNewestFirst(Array.isArray(list) ? list : []));
  }, []);

  const mergeHistory = useCallback(async (sid: string, welcome: string | null, echoes: string[] = []) => {
    const res = await api.history(sid);
    let items: HistoryItem[] = (res.items || []).map((i) => ({ ...i, kind: "chat" as const }));
    items = applyLocalUserEchoes(items, echoes);
    items = applyWelcomeBubble(items, welcome);
    setHistory(items);
  }, []);

  useEffect(() => {
    const uiMode = parseUiMode(sessionStorage.getItem(UI_MODE_KEY));
    setMode(uiMode);
    setTheme(parseTheme(localStorage.getItem(THEME_KEY)));
    setLocalSpeechOn(parseLocalSpeechEnabled(localStorage.getItem(LOCAL_SPEECH_KEY)));
    refreshConfig().catch((e) =>
      setBanner(errorBanner(e, uiMode === "guest" ? "guest" : "lab")),
    );

    const storedId = parseStoredSessionId(sessionStorage.getItem(SESSION_KEY));
    if (!storedId) return;

    let cancelled = false;
    (async () => {
      try {
        const sess = await api.getSession(storedId);
        if (cancelled) return;
        setSessionId(sess.session_id);
        setStatus(sess.status);
        setLocalUserEchoes([]);
        setLastReply(sess.status === "active" && sess.last_reply ? sess.last_reply : null);
        setRatingOpen(false);
        const welcome = uiMode === "guest" ? DEFAULT_GUIDE_TEXT : null;
        setWelcomeText(welcome);
        setRoomHint(sess.status === "active" ? "已恢复" : "未初始化");
        await mergeHistory(sess.session_id, welcome);
        if (cancelled) return;
        if (uiMode === "lab") await refreshEvents(sess.session_id);
        if (!cancelled) {
          setBanner({
            kind: "ok",
            text: sess.status === "transferred" ? "已恢复上次转人工会话" : "已恢复上次咨询",
          });
        }
      } catch (e) {
        if (cancelled) return;
        rememberSession(null);
        if (e instanceof ApiError && (e.status === 404 || e.code === "SESSION_NOT_FOUND")) {
          return;
        }
        setBanner({
          kind: "warn",
          text:
            uiMode === "guest"
              ? "未能恢复上次咨询，请重新开始。"
              : `未能恢复上次咨询：${formatApiError(e, { audience: "lab" })}`,
        });
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [mergeHistory, refreshConfig, refreshEvents]);

  useEffect(() => {
    if (!banner) return;
    const ms = autoDismissMs(banner.kind, banner.tone);
    if (ms == null) return;
    const timer = window.setTimeout(() => setBanner(null), ms);
    return () => window.clearTimeout(timer);
  }, [banner]);

  useEffect(() => {
    return () => {
      if (statusCueTimer.current) window.clearTimeout(statusCueTimer.current);
      cancelLocalSpeech();
    };
  }, []);

  async function run(
    label: string,
    fn: () => Promise<void>,
    kind: BusyKind = null,
    opts?: { keepBusy?: boolean },
  ) {
    const startedAt = Date.now();
    setBusy(true);
    setBusyKind(kind);
    setBanner(null);
    if (kind === "send") {
      setStatusCue("replying");
      // 先画出「客服回复中」，再请求；本地规则秒回时否则会被合并成一次渲染。
      await waitForPaint(550);
    } else if (kind === "start") {
      setStatusCue("starting");
      await waitForPaint(200);
    }
    try {
      await fn();
      if (shouldAnnounceSuccess(mode, label)) {
        setBanner({ kind: "ok", text: `${label}成功` });
      }
      if (kind === "send") {
        // 本地秒回时仍保持「回复播报中」+ 输入锁定，至少满最短展示
        const holdReplying = remainingHoldMs(startedAt, MIN_STATUS_CUE_MS);
        if (holdReplying > 0) await waitForPaint(holdReplying);
        setStatusCue("replied");
        if (statusCueTimer.current) window.clearTimeout(statusCueTimer.current);
        statusCueTimer.current = window.setTimeout(() => {
          setStatusCue(null);
          statusCueTimer.current = null;
        }, 1400);
      } else if (kind === "start") {
        setStatusCue(null);
      }
    } catch (e) {
      const retry = kind === "start" || kind === "send" ? kind : undefined;
      bannerRetryRef.current = retry ?? null;
      setBanner(errorBanner(e, mode === "guest" ? "guest" : "lab", retry));
      setStatusCue(null);
      // 失败时必须释放 busy，即使 keepBusy
      setBusy(false);
      setBusyKind(null);
      return false;
    }
    if (!opts?.keepBusy) {
      setBusy(false);
      setBusyKind(null);
    }
    return true;
  }

  const canChat = status === "active" && !!sessionId;
  const themeClass = theme === "ink" ? "theme-ink" : "theme-default";
  const cueText = statusCueLabel(statusCue);
  const showGuestTip = guestTipRev >= 0 && shouldShowGuestTip(mode, status, sessionId);

  async function startConsult(thenSend?: string) {
    // 按钮 onClick 会传入事件对象，不能当成要发送的文本
    const followUp = followUpSendText(thenSend);
    let createdId: string | null = null;
    let welcome: string | null = null;
    pendingSpeechRef.current = null;
    cancelLocalSpeech();
    const startedOk = await run(
      mode === "guest" ? "开始咨询" : "创建会话",
      async () => {
        const cfg = config || (await refreshConfig());
        const entryId = resolveSessionEntryId({
          mode,
          pilotEntryId: cfg.pilot_entry_id,
          selectedEntryId,
          entries: cfg.entries,
        });
        applyEntryAppearance(entryId, cfg.entries);
        const sess = await api.createSession(entryId);
        createdId = sess.session_id;
        setSessionId(sess.session_id);
        rememberSession(sess.session_id);
        setStatus(sess.status);
        setLastReply(null);
        setLastCommandId(null);
        setFallbackOn(false);
        setRoomHint("未初始化");
        setWelcomeText(null);
        setLocalUserEchoes([]);
        setEvents([]);
        setRatingOpen(false);
        setRatingScore(5);
        trackDh("dh_entry_selected", { sessionId: sess.session_id, detail: entryId });
        welcome = welcomeTextForEntry(cfg.entries, entryId, DEFAULT_GUIDE_TEXT);
        setWelcomeText(welcome);
        if (mode === "guest") {
          await api.guide(sess.session_id);
          trackDh("dh_guide_show", { sessionId: sess.session_id });
          // 先立刻写入本地欢迎气泡，避免历史接口为空时对话区仍空白
          setHistory([
            {
              role: "assistant",
              text: welcome,
              created_at: new Date().toISOString(),
              kind: "welcome",
            },
          ]);
          try {
            const initRes = await api.initDh(sess.session_id, profile);
            setRoomHint(String(initRes.room_id || "已初始化"));
            trackDh("dh_init_success", {
              sessionId: sess.session_id,
              detail: String(initRes.room_id || "ok"),
            });
            // 欢迎指令保持 queued：若 mark stream-started，事件会挡住后续 NLP 推流／应答口播。
            const welcomeCmd = initRes.welcome_command_id;
            if (typeof welcomeCmd === "number") {
              setLastCommandId(welcomeCmd);
              setRoomHint(`指令 ${welcomeCmd} · queued`);
            }
            if (
              shouldSpeakWelcomeOnStart({
                mode,
                localSpeechOn,
                followUp,
              })
            ) {
              pendingSpeechRef.current = welcome || "";
            }
          } catch (e) {
            trackDh("dh_init_fail", {
              sessionId: sess.session_id,
              detail: e instanceof Error ? e.message.slice(0, 80) : "fail",
            });
            throw e;
          }
          await mergeHistory(sess.session_id, welcome);
        } else {
          setHistory([
            {
              role: "assistant",
              text: welcome,
              created_at: new Date().toISOString(),
              kind: "welcome",
            },
          ]);
        }
        if (mode === "lab") {
          await refreshEvents(sess.session_id);
        }
      },
      "start",
      { keepBusy: Boolean(followUp) },
    );
    if (followUp && createdId && startedOk) {
      pendingSpeechRef.current = null;
      await sendText(followUp, createdId, welcome ?? DEFAULT_GUIDE_TEXT, []);
    } else if (followUp && !startedOk) {
      setBusy(false);
      setBusyKind(null);
    } else if (startedOk) {
      const speech = pendingSpeechRef.current;
      pendingSpeechRef.current = null;
      if (speech) playLocalSpeech(speech);
      if (mode === "lab") {
        // 仅建会话：结束后刷一次，避免与连发请求互相覆盖
        setStatsTick((n) => n + 1);
      }
    }
  }

  async function sendText(
    text: string,
    sid: string,
    welcome: string | null = welcomeText,
    echoesBase?: string[],
  ) {
    const trimmed = text.trim();
    if (!trimmed) return;
    if (trimmed === "转人工" || trimmed === "人工客服" || trimmed === "找人工") {
      setTransferOpen(true);
      return;
    }
    lastSendRef.current = trimmed;
    pendingSpeechRef.current = null;
    cancelLocalSpeech();
    const ok = await run(
      "发送",
      async () => {
        const nextEchoes = [...(echoesBase ?? localUserEchoes), trimmed];
        setLocalUserEchoes(nextEchoes);
        const reply = await api.sendMessage(sid, trimmed);
        setLastReply(reply);
        trackDh(reply.agent_used ? "dh_agent_used" : "dh_agent_skipped", {
          sessionId: sid,
          detail: reply.source,
        });
        setInput("");
        await mergeHistory(sid, welcome, nextEchoes);
        if (mode === "lab") {
          await refreshEvents(sid);
          setStatsTick((n) => n + 1);
        }
        if (speechOn) {
          pendingSpeechRef.current = reply.spoken_text || "";
        }
        if (mode === "guest") {
          try {
            const pushed = await api.push(sid);
            setLastCommandId(pushed.command_db_id);
            setRoomHint(`指令 ${pushed.command_db_id} · ${pushed.status}`);
            await api.streamStarted(sid, pushed.command_db_id);
            setRoomHint(`指令 ${pushed.command_db_id} · started`);
          } catch (e) {
            // 推流失败仍保留本地口播；文字已出齐。
            setBanner({
              kind: "warn",
              text:
                mode === "guest"
                  ? "回复已显示；数字人播报暂未跟上，可继续文字咨询。"
                  : `口播已出，推流未成功：${errorText(e, "lab")}`,
            });
          }
        }
      },
      "send",
    );
    if (ok) {
      const speech = pendingSpeechRef.current;
      pendingSpeechRef.current = null;
      if (speech) playLocalSpeech(speech);
    }
  }

  function retryBannerAction() {
    const retry = bannerRetryRef.current;
    setBanner(null);
    if (retry === "start") {
      void startConsult();
      return;
    }
    if (retry === "send") {
      const text = lastSendRef.current;
      const sid = sessionId;
      if (text && sid) void sendText(text, sid);
    }
  }

  return (
    <div
      className={workspaceShellClass(mode, themeClass)}
      style={{ ["--accent" as string]: entryAccent }}
      data-entry-label={activeEntryLabel || undefined}
    >
      {cueText ? (
        <div className={`status-cue status-cue-${statusCue || "idle"}`} role="status" aria-live="assertive">
          <span>{cueText}</span>
          {statusCue === "speaking" ? (
            <button type="button" className="status-cue-skip" onClick={skipLocalSpeech}>
              跳过口播
            </button>
          ) : null}
        </div>
      ) : null}
      {banner ? (
        <StatusBanner
          banner={banner}
          onDismiss={() => {
            bannerRetryRef.current = null;
            setBanner(null);
          }}
          onRetry={banner.retry ? retryBannerAction : undefined}
        />
      ) : null}
      {fallbackOn ? (
        <StatusBanner
          banner={{
            kind: "warn",
            text: "数字人播报暂时跟不上，已为您切换文字说明（咨询仍可继续）。",
          }}
          onDismiss={() => setFallbackOn(false)}
        />
      ) : null}

      <ConfigBar
        mode={mode}
        onModeChange={changeMode}
        config={config}
        selectedEntryId={selectedEntryId || config?.pilot_entry_id || ""}
        onEntryChange={(id) => {
          setSelectedEntryId(id);
          applyEntryAppearance(id);
        }}
        theme={theme}
        onThemeChange={changeTheme}
        busy={busy}
        onRefresh={() => run("刷新状态", async () => { await refreshConfig(); })}
        onAgent={(enabled) =>
          run(enabled ? "打开总闸 Agent" : "关闭总闸 Agent", async () => {
            const cfg = await api.putConfig({ agent_enabled: enabled });
            setConfig(cfg);
          })
        }
        onRag={(enabled) =>
          run(enabled ? "打开 RAG" : "关闭 RAG", async () => {
            const cfg = await api.putConfig({ rag_enabled: enabled });
            setConfig(cfg);
          })
        }
        localSpeechOn={localSpeechOn}
        onLocalSpeechChange={changeLocalSpeech}
      />

      {showGuestTip ? (
        <GuestTipBanner
          onDismiss={() => {
            dismissGuestTip(sessionId);
            setGuestTipRev((n) => n + 1);
          }}
        />
      ) : null}

      <div className="stage">
        <AvatarPanel
          mode={mode}
          profile={profile}
          roomHint={avatarStatusHint(
            mode === "guest" && canChat ? "已就绪" : roomHint,
            busyKind,
            statusCue,
          )}
          logoUrl={entryLogo}
          entryLabel={activeEntryLabel}
          busy={busy}
          busyKind={busyKind}
          statusCue={statusCue}
          spokenLine={speakingLine}
          canChat={canChat}
          hasLastReply={!!lastReply}
          hasCommand={lastCommandId != null}
          onProfileChange={setProfile}
          onInit={() =>
            run("初始化数字人", async () => {
              if (!sessionId) return;
              try {
                const res = await api.initDh(sessionId, profile);
                setRoomHint(String(res.room_id || "已初始化"));
                trackDh("dh_init_success", {
                  sessionId,
                  detail: String(res.room_id || "ok"),
                });
              } catch (e) {
                trackDh("dh_init_fail", {
                  sessionId,
                  detail: e instanceof Error ? e.message.slice(0, 80) : "fail",
                });
                throw e;
              }
            })
          }
          onPush={() =>
            run("推流", async () => {
              if (!sessionId) return;
              const res = await api.push(sessionId);
              setLastCommandId(res.command_db_id);
              setRoomHint(`指令 ${res.command_db_id} · ${res.status}`);
            })
          }
          onStarted={() =>
            run("开始展示", async () => {
              if (!sessionId || lastCommandId == null) return;
              await api.streamStarted(sessionId, lastCommandId);
              setRoomHint(`指令 ${lastCommandId} · started`);
              if (speechOn && lastReply?.spoken_text) {
                playLocalSpeech(lastReply.spoken_text);
              }
            })
          }
          onCheckSync={() =>
            run("检查同步", async () => {
              if (!sessionId) return;
              const res = await api.checkSync(sessionId);
              if (res.fallback) {
                setFallbackOn(true);
                trackDh("dh_sync_fallback_2s", { sessionId, detail: res.reason });
              } else setBanner({ kind: "ok", text: `未降级：${res.reason}` });
            })
          }
          onSimulateFallback={() =>
            run("模拟降级", async () => {
              if (!sessionId) return;
              await api.fallback(sessionId);
              setFallbackOn(true);
              trackDh("dh_sync_fallback_2s", { sessionId, detail: "simulate" });
              if (mode === "lab") await refreshEvents(sessionId);
            })
          }
        />

        <ChatPanel
          mode={mode}
          sessionId={sessionId}
          status={status}
          history={history}
          lastReply={lastReply}
          input={input}
          busy={busy}
          busyLabel={busyKind}
          statusCue={statusCue}
          canChat={canChat}
          onStartConsult={startConsult}
          onGuide={() =>
            run("展示引导", async () => {
              if (!sessionId) return;
              await api.guide(sessionId);
              trackDh("dh_guide_show", { sessionId });
            })
          }
          onAskTransfer={() => setTransferOpen(true)}
          onInputChange={setInput}
          onSend={(override) => {
            if (!sessionId) return;
            void sendText(override ?? input, sessionId);
          }}
          onEmptyHint={(hint) => {
            if (sessionId && status === "active") {
              void sendText(hint, sessionId);
              return;
            }
            void startConsult(hint);
          }}
          onSpecial={(id) =>
            run(`特殊指令 ${id}`, async () => {
              if (!sessionId) return;
              await api.special(sessionId, id);
              if (mode === "lab") await refreshEvents(sessionId);
            })
          }
        />
      </div>

      {mode === "lab" ? (
        <div className="lab-dock" aria-label="验收辅助区">
          <StatsPanel
            refreshKey={statsTick}
            activeEntryId={selectedEntryId || config?.pilot_entry_id || ""}
          />
          <WalkthroughPanel
            busy={busy}
            canChat={canChat}
            onRun={(item) => {
              if (isWalkthroughTransfer(item)) {
                setTransferOpen(true);
                return;
              }
              const text = walkthroughSendText(item);
              if (!text) return;
              if (sessionId && status === "active") {
                void sendText(text, sessionId);
                return;
              }
              void startConsult(text);
            }}
          />
          <EventsPanel
            events={events}
            busy={busy}
            hasSession={!!sessionId}
            onRefresh={() =>
              run("刷新事件", async () => {
                await refreshEvents(sessionId);
              })
            }
          />
          <AnalyticsPanel />
        </div>
      ) : null}

      <TransferConfirm
        open={transferOpen}
        busy={busy}
        onCancel={() => setTransferOpen(false)}
        onConfirm={() => {
          setTransferOpen(false);
          run("转人工", async () => {
            if (!sessionId) return;
            const res = await api.transfer(sessionId);
            setStatus(res.status);
            trackDh("dh_transfer_human", { sessionId });
            setRatingOpen(true);
            if (mode === "lab") {
              await refreshEvents(sessionId);
              setStatsTick((n) => n + 1);
            }
          });
        }}
      />

      <RatingModal
        open={ratingOpen}
        busy={busy}
        score={ratingScore}
        onScoreChange={setRatingScore}
        onSkip={() => setRatingOpen(false)}
        onSubmit={() => {
          run("提交评价", async () => {
            if (!sessionId) return;
            await api.rating(sessionId, ratingScore, "前端试点");
            trackDh("dh_rate", { sessionId, detail: String(ratingScore) });
            bumpLabStats();
            setRatingOpen(false);
          });
        }}
      />
    </div>
  );
}
