// Desk Yantra does not send product analytics to an upstream service.
const OPT_OUT_KEY = "omb-analytics-opt-out";

export function analyticsEnabled(): boolean {
  return false;
}

export type OptAction = "init" | "opt-in" | "opt-out" | "none";
export function optAction(enabled: boolean, running: boolean): OptAction {
  if (!enabled) return running ? "opt-out" : "none";
  return running ? "opt-in" : "init";
}

export function setAnalyticsEnabled(_enabled: boolean): void {
  try { localStorage.setItem(OPT_OUT_KEY, "1"); } catch {}
  void globalThis.window?.ogb?.desktopAnalytics?.set?.(false).catch(() => {});
}

export function initAnalytics(): Promise<void> {
  return Promise.resolve();
}

export function analyticsSurface(): "local" | "server" {
  return globalThis.window?.ogb?.environments ? "local" : "server";
}

export function track(_event: string, _props?: Record<string, unknown>): void {}

const GATE_KEY = "omb-email-gate";
export function emailGateDone(): boolean {
  return Boolean(localStorage.getItem(GATE_KEY));
}
export function setEmailGateDone(status: "submitted" | "skipped"): void {
  localStorage.setItem(GATE_KEY, status);
}
