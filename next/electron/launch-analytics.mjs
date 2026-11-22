// Keep the desktop's launch hooks inert until Desk Yantra has its own reviewed diagnostics endpoint.
export const LAUNCH_STAGES = Object.freeze([
  "started", "server_spawned", "server_ready", "server_failed", "window_shown", "page_load_failed", "page_crashed",
]);
export const LAUNCH_REASONS = Object.freeze([
  "timeout", "exited", "foreign-owner", "stuck-child", "relay",
  "painted", "crashed", "shown", "hidden",
  "abnormal-exit", "integrity-failure", "killed", "launch-failed", "oom",
]);

export function launchAnalyticsAllowed() { return false; }

export function createLaunchAnalytics() {
  return {
    stage() {},
    serverFailed() {},
    crashed() {},
  };
}

export function desktopLaunchAnalytics() {
  return createLaunchAnalytics();
}
