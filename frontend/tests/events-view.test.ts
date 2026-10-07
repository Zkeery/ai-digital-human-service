import { describe, expect, it } from "vitest";

import { formatEventLine, sortEventsNewestFirst } from "../features/session/eventsView";

describe("events view", () => {
  it("formats a readable line", () => {
    expect(
      formatEventLine({
        id: 1,
        session_id: "s",
        event_key: "dh_message_replied",
        payload: { source: "faq", reason: "x" },
        created_at: "2026-10-02T01:02:03.000Z",
      }),
    ).toContain("dh_message_replied");
  });

  it("sorts newest first", () => {
    const sorted = sortEventsNewestFirst([
      {
        id: 1,
        session_id: "s",
        event_key: "a",
        payload: {},
        created_at: "2026-10-01T10:00:00",
      },
      {
        id: 2,
        session_id: "s",
        event_key: "b",
        payload: {},
        created_at: "2026-10-02T10:00:00",
      },
    ]);
    expect(sorted.map((e) => e.event_key)).toEqual(["b", "a"]);
  });
});
