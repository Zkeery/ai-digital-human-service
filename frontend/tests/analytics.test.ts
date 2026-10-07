import { describe, expect, it, beforeEach } from "vitest";

import {
  clearDhEvents,
  dhEventLabel,
  listDhEvents,
  resetDhEventsForTests,
  trackDh,
} from "../features/session/analytics";

describe("dh analytics skeleton", () => {
  beforeEach(() => {
    resetDhEventsForTests();
  });

  it("tracks and lists newest first", () => {
    trackDh("dh_guide_show", { sessionId: "abc" });
    trackDh("dh_init_success", { sessionId: "abc", detail: "room-1" });
    const list = listDhEvents();
    expect(list).toHaveLength(2);
    expect(list[0].key).toBe("dh_init_success");
    expect(list[1].key).toBe("dh_guide_show");
    expect(dhEventLabel("dh_transfer_human")).toContain("转人工");
  });

  it("clears buffer", () => {
    trackDh("dh_rate", { detail: "5" });
    clearDhEvents();
    expect(listDhEvents()).toHaveLength(0);
  });
});
