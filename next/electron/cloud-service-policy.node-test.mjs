import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import { cloudServiceAvailable } from "./cloud-service-policy.mjs";

test("packaged desktop cannot restore or offer the imported Cloud service", () => {
  assert.equal(cloudServiceAvailable(), false);
  const main = readFileSync(new URL("./main.mjs", import.meta.url), "utf8");
  assert.match(main, /if \(!cloudServiceAvailable\(\)\) throw new Error\("Desk Yantra Cloud is not configured/);
  assert.match(main, /if \(app\.isPackaged && !desktopRemoteAccess && cloudServiceAvailable\(\)\) \{\s+cloudAccountRestoring = true;/);
  assert.match(main, /allowed: \(\) => app\.isPackaged && !desktopRemoteAccess && cloudServiceAvailable\(\)/);
  assert.match(main, /return cloudServiceAvailable\(\) && app\.isPackaged && !desktopRemoteAccess && brandedBuild === false;/);
});
