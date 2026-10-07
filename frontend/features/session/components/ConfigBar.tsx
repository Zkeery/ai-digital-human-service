"use client";

import type { ConfigView } from "@/lib/api/session";
import { effectiveAgentPreview, findEntry, showEntryAdminControls } from "../entries";
import type { UiMode } from "../mode";
import { ModeSwitch } from "./ModeSwitch";

type Props = {
  mode: UiMode;
  onModeChange: (mode: UiMode) => void;
  config: ConfigView | null;
  selectedEntryId: string;
  onEntryChange: (entryId: string) => void;
  theme: string;
  onThemeChange: (theme: string) => void;
  busy: boolean;
  onRefresh: () => void;
  onAgent: (enabled: boolean) => void;
  onRag: (enabled: boolean) => void;
  localSpeechOn?: boolean;
  onLocalSpeechChange?: (enabled: boolean) => void;
};

export function ConfigBar({
  mode,
  onModeChange,
  config,
  selectedEntryId,
  onEntryChange,
  theme,
  onThemeChange,
  busy,
  onRefresh,
  onAgent,
  onRag,
  localSpeechOn = true,
  onLocalSpeechChange,
}: Props) {
  const labAdmin = showEntryAdminControls(mode);
  const selected =
    findEntry(config?.entries, selectedEntryId) ||
    findEntry(config?.entries, config?.pilot_entry_id || "");
  const effectiveOn = effectiveAgentPreview(Boolean(config?.agent_enabled), selected);
  const meta = labAdmin
    ? config
      ? `入口 ${selected?.label || config.pilot_entry_id} · 总闸 ${
          config.agent_enabled ? "开" : "关"
        } · 本入口 Agent 默认 ${selected?.agent_enabled ? "开" : "关"} · 实际 ${
          effectiveOn ? "会启用" : "不启用"
        } · RAG ${config.rag_enabled ? "开" : "关"} · 同步 ${config.sync_hold_ms}ms`
      : "配置加载中…"
    : "可咨询账户、转账、卡片、密码、信用卡、理财说明书、网点与投诉";

  return (
    <header className={mode === "guest" ? "hero guest-compact" : "hero"}>
      <div className="hero-top">
        <p className="eyebrow">{mode === "guest" ? "零售金融客服" : "AI数字人客服 · 验收配置"}</p>
        <ModeSwitch mode={mode} onChange={onModeChange} />
      </div>
      {mode === "guest" ? (
        <h1>数字人客服</h1>
      ) : (
        <>
          <h1>数字人客服</h1>
          <p className="lede">{meta}</p>
          <p className="hint">入口、Agent 总闸与 RAG 仅验收可见，访客壳不会出现这些控件。</p>
        </>
      )}
      {mode === "guest" ? null : (
        <div className="chip-row">
          <button type="button" className="btn ghost" disabled={busy} onClick={onRefresh}>
            刷新状态
          </button>
          {config?.entries?.length ? (
            <label className="inline-label">
              本地入口
              <select
                value={selectedEntryId || config.pilot_entry_id}
                onChange={(e) => onEntryChange(e.target.value)}
                disabled={busy}
              >
                {config.entries.map((entry) => (
                  <option key={entry.id} value={entry.id}>
                    {entry.label}
                  </option>
                ))}
              </select>
            </label>
          ) : null}
          <button type="button" className="btn" disabled={busy || !config} onClick={() => onAgent(true)}>
            打开总闸 Agent
          </button>
          <button type="button" className="btn ghost" disabled={busy || !config} onClick={() => onAgent(false)}>
            关闭总闸 Agent
          </button>
          <button type="button" className="btn" disabled={busy || !config} onClick={() => onRag(true)}>
            打开 RAG
          </button>
          <button type="button" className="btn ghost" disabled={busy || !config} onClick={() => onRag(false)}>
            关闭 RAG
          </button>
          {config ? <span className="hint">llm_mock：{config.llm_mock ? "是" : "否"}</span> : null}
          {onLocalSpeechChange ? (
            <>
              <button
                type="button"
                className="btn"
                disabled={busy || localSpeechOn}
                onClick={() => onLocalSpeechChange(true)}
              >
                打开本地口播
              </button>
              <button
                type="button"
                className="btn ghost"
                disabled={busy || !localSpeechOn}
                onClick={() => onLocalSpeechChange(false)}
              >
                关闭本地口播
              </button>
              <span className="hint">
                本地口播：{localSpeechOn ? "开" : "关"}（仅验收可关；访客固定开）
              </span>
            </>
          ) : null}
          <label className="inline-label">
            换肤
            <select value={theme} onChange={(e) => onThemeChange(e.target.value)} disabled={busy}>
              <option value="default">浅色</option>
              <option value="ink">深色</option>
            </select>
          </label>
        </div>
      )}
    </header>
  );
}
