import { describe, expect, it, vi } from "vitest";
import { analyticsEnabled, initAnalytics, setAnalyticsEnabled, track } from "./analytics";

describe("Desk Yantra analytics policy", () => {
  it("stays disabled even when an old preference tries to enable it", async () => {
    const store = new Map<string, string>([["omb-analytics-opt-out", "0"]]);
    vi.stubGlobal("localStorage", {
      getItem: (key: string) => store.get(key) ?? null,
      setItem: (key: string, value: string) => store.set(key, value),
    });
    try {
      expect(analyticsEnabled()).toBe(false);
      setAnalyticsEnabled(true);
      await initAnalytics();
      track("should_not_leave_this_device", { content: "private" });
      expect(analyticsEnabled()).toBe(false);
      expect(store.get("omb-analytics-opt-out")).toBe("1");
    } finally {
      vi.unstubAllGlobals();
    }
  });
});
