import assert from "node:assert/strict";
import test from "node:test";
import { createLaunchAnalytics, desktopLaunchAnalytics, launchAnalyticsAllowed } from "./launch-analytics.mjs";

test("desktop launch hooks never send telemetry, including when an old analytics choice is on", () => {
  const sent = [];
  const fetch = (...args) => { sent.push(args); throw new Error("telemetry must stay off"); };
  for (const choice of [true, false, null]) {
    assert.equal(launchAnalyticsAllowed({ choice, packaged: true, env: {} }), false);
    const hooks = createLaunchAnalytics({ fetch, choice: () => choice, packaged: true, env: {} });
    hooks.stage("started");
    hooks.stage("server_failed", { reason: "timeout" });
    hooks.serverFailed("timeout");
    hooks.crashed({ kind: "renderer", surface: "main-window", reason: "crashed" });
  }
  const desktop = desktopLaunchAnalytics({
    app: { isPackaged: true, getVersion: () => "1.0.0", getPath: () => "/unused" },
    session: { defaultSession: { fetch } }, prefs: { analytics: () => true },
  });
  desktop.stage("window_shown");
  assert.deepEqual(sent, []);
});
