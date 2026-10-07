"use client";

import type { SessionEvent } from "@/lib/api/session";
import { formatEventLine } from "../eventsView";

type Props = {
  events: SessionEvent[];
  busy: boolean;
  hasSession: boolean;
  onRefresh: () => void;
};

export function EventsPanel({ events, busy, hasSession, onRefresh }: Props) {
  return (
    <section className="events-panel" aria-label="会话事件">
      <div className="events-head">
        <h2>事件时间线</h2>
        <button type="button" className="btn ghost tiny" disabled={busy || !hasSession} onClick={onRefresh}>
          刷新事件
        </button>
      </div>
      {!hasSession ? (
        <p className="empty">先创建会话后再看埋点。</p>
      ) : events.length === 0 ? (
        <p className="empty">暂无事件，发一句或点刷新试试。</p>
      ) : (
        <ul className="events-list">
          {events.map((ev) => (
            <li key={ev.id}>
              <code>{formatEventLine(ev)}</code>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
