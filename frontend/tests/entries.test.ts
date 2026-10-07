import { describe, expect, it } from "vitest";

import {
  effectiveAgentPreview,
  resolveSessionEntryId,
  safeAccent,
  safeLogoUrl,
  showEntryAdminControls,
  welcomeTextForEntry,
} from "../features/session/entries";

const entries = [
  {
    id: "entry_pilot_001",
    label: "通用金融咨询",
    welcome_text: "通用欢迎",
    theme: "default",
    accent: "#0f766e",
    logo_url: "",
    agent_enabled: false,
  },
  {
    id: "entry_credit_001",
    label: "信用卡专窗",
    welcome_text: "信用卡欢迎",
    theme: "ink",
    accent: "#0e7490",
    logo_url: "",
    agent_enabled: true,
  },
];

describe("multi entry helpers", () => {
  it("guest always uses pilot entry", () => {
    expect(
      resolveSessionEntryId({
        mode: "guest",
        pilotEntryId: "entry_pilot_001",
        selectedEntryId: "entry_credit_001",
        entries,
      }),
    ).toBe("entry_pilot_001");
  });

  it("lab uses selected whitelist entry", () => {
    expect(
      resolveSessionEntryId({
        mode: "lab",
        pilotEntryId: "entry_pilot_001",
        selectedEntryId: "entry_credit_001",
        entries,
      }),
    ).toBe("entry_credit_001");
  });

  it("hides entry admin on guest shell", () => {
    expect(showEntryAdminControls("guest")).toBe(false);
    expect(showEntryAdminControls("lab")).toBe(true);
  });

  it("picks welcome text by entry", () => {
    expect(welcomeTextForEntry(entries, "entry_credit_001", "fallback")).toBe("信用卡欢迎");
    expect(welcomeTextForEntry(entries, "missing", "fallback")).toBe("fallback");
  });

  it("effective agent needs global and entry", () => {
    expect(effectiveAgentPreview(true, entries[1])).toBe(true);
    expect(effectiveAgentPreview(false, entries[1])).toBe(false);
    expect(effectiveAgentPreview(true, entries[0])).toBe(false);
  });

  it("sanitizes accent and logo url", () => {
    expect(safeAccent("#0e7490")).toBe("#0e7490");
    expect(safeAccent("red")).toBe("#0f766e");
    expect(safeLogoUrl("/entries/credit.svg")).toBe("/entries/credit.svg");
    expect(safeLogoUrl("https://evil.example/x.png")).toBe("");
    expect(safeLogoUrl("/entries/../secret")).toBe("");
  });
});
