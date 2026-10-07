"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { api, type StatsView } from "@/lib/api/session";

import { formatEntryStatsLine, formatStatsSummary } from "../statsView";

type Props = {
  /** 验收侧建会话／发消息／转人工后递增，自动拉最新汇总 */
  refreshKey?: number;
  /** 高亮当前选中的入口行，避免换到信用卡专窗后看错行 */
  activeEntryId?: string;
};

export function StatsPanel({ refreshKey = 0, activeEntryId = "" }: Props) {
  const [stats, setStats] = useState<StatsView | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const reqSeq = useRef(0);

  const refresh = useCallback(async () => {
    const seq = ++reqSeq.current;
    setLoading(true);
    setError("");
    try {
      const next = await api.stats();
      // 只采纳最后一次请求，避免通用／信用卡连点时旧结果覆盖新结果
      if (seq !== reqSeq.current) return;
      setStats(next);
    } catch (e) {
      if (seq !== reqSeq.current) return;
      setError(e instanceof Error ? e.message : "统计加载失败");
    } finally {
      if (seq === reqSeq.current) setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh, refreshKey]);

  return (
    <section className="stats-panel" aria-label="本地统计">
      <div className="analytics-head">
        <h2>本地统计（验收）</h2>
        <button
          type="button"
          className="btn ghost tiny"
          disabled={loading}
          onClick={() => void refresh()}
        >
          {loading ? "刷新中…" : "刷新统计"}
        </button>
      </div>
      <p className="hint">汇总本机库里的会话与事件；访客模式不显示。不是现网运营大盘。</p>
      {error ? <p className="hint">{error}</p> : null}
      {!stats && !error ? <p className="hint">加载中…</p> : null}
      {stats ? (
        <>
          <p className="stats-summary">{formatStatsSummary(stats)}</p>
          <ul className="stats-list">
            {stats.by_entry.map((row) => {
              const active = Boolean(activeEntryId && row.entry_id === activeEntryId);
              return (
                <li key={row.entry_id} className={active ? "is-active-entry" : undefined}>
                  <code>
                    {active ? "▸ " : ""}
                    {formatEntryStatsLine(row)}
                  </code>
                </li>
              );
            })}
          </ul>
          <p className="hint soft">
            转人工事件 {stats.transfer_events} · 已回复消息 {stats.messages_replied}
          </p>
        </>
      ) : null}
    </section>
  );
}
