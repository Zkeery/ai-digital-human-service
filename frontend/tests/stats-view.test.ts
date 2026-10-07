import { describe, expect, it } from "vitest";

import type { StatsView } from "../lib/api/session";
import { formatEntryStatsLine, formatStatsSummary } from "../features/session/statsView";

const sample: StatsView = {
  sessions_total: 3,
  sessions_active: 2,
  sessions_transferred: 1,
  transfer_events: 1,
  agent_used: 2,
  agent_skipped: 4,
  messages_replied: 5,
  ratings: 1,
  by_entry: [
    {
      entry_id: "entry_pilot_001",
      label: "通用金融咨询",
      sessions: 2,
      transferred: 0,
      agent_used: 0,
      agent_skipped: 3,
    },
  ],
};

describe("lab stats view", () => {
  it("formats summary and entry lines", () => {
    expect(formatStatsSummary(sample)).toContain("会话 3");
    expect(formatStatsSummary(sample)).toContain("Agent 使用 2");
    expect(formatEntryStatsLine(sample.by_entry[0])).toContain("通用金融咨询");
    expect(formatEntryStatsLine(sample.by_entry[0])).toContain("跳过 3");
  });
});
