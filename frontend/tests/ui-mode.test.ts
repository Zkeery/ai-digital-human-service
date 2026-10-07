import { describe, expect, it } from "vitest";

import {
  guestHiddenControls,
  isControlVisible,
  parseUiMode,
} from "../features/session/mode";

describe("ui mode", () => {
  it("defaults to guest", () => {
    expect(parseUiMode(null)).toBe("guest");
    expect(parseUiMode("junk")).toBe("guest");
    expect(parseUiMode("lab")).toBe("lab");
  });

  it("hides lab-only controls in guest", () => {
    for (const id of guestHiddenControls()) {
      expect(isControlVisible("guest", id)).toBe(false);
      expect(isControlVisible("lab", id)).toBe(true);
    }
    expect(isControlVisible("guest", "start-consult")).toBe(true);
  });
});
