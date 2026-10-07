"use client";

import { useEffect, useState } from "react";

import {
  clearDhEvents,
  dhEventLabel,
  listDhEvents,
  subscribeDhEvents,
  type DhEvent,
} from "../analytics";

export function AnalyticsPanel() {
  const [events, setEvents] = useState<DhEvent[]>([]);

  useEffect(() => {
    const sync = () => setEvents(listDhEvents());
    sync();
    return subscribeDhEvents(sync);
  }, []);

  return (
    <section className="analytics-panel" aria-label="埋点骨架">
      <div className="analytics-head">
        <h2>埋点骨架（本地）</h2>
        <button type="button" className="btn ghost tiny" onClick={() => clearDhEvents()}>
          清空
        </button>
      </div>
      {events.length === 0 ? (
        <p className="hint">尚无埋点。走一遍引导／初始化／发送／转人工／评价后会出现。</p>
      ) : (
        <ul className="analytics-list">
          {events.map((ev) => (
            <li key={`${ev.key}-${ev.at}`}>
              <code>
                {ev.key} · {dhEventLabel(ev.key)}
                {ev.detail ? ` · ${ev.detail}` : ""}
                {ev.sessionId ? ` · ${ev.sessionId.slice(0, 8)}…` : ""}
              </code>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
