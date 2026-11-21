// Gate 5 qualification: Service installation plans, systemd units, packaging descriptors, and Arch Linux PKGBUILD.
import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";
import { servicePlan, systemdUnit, SYSTEMD_UNIT_NAME, LAUNCHD_LABEL } from "../server/service-unit.ts";

console.log("=== Gate 5: Packaging & Service Verification ===");

// 1. Service naming and unit naming
console.log("[1] Verifying service unit names");
assert.equal(SYSTEMD_UNIT_NAME, "desk-yantra.service");
assert.equal(LAUNCHD_LABEL, "com.deskyantra.serve");

// 2. Linux service plan
console.log("[2] Verifying Linux systemd service plan");
const plan = servicePlan("linux", "/home/test/.desk-yantra", "/home/test");
assert.ok(plan, "Linux service plan must be generated");
assert.equal(plan.installed, "/etc/systemd/system/desk-yantra.service");
assert.ok(plan.activate.some((line) => line.includes("systemctl enable --now desk-yantra")));
assert.ok(plan.deactivate.some((line) => line.includes("systemctl disable --now desk-yantra")));

// 3. Rendered systemd unit
console.log("[3] Verifying rendered systemd unit contents");
const unit = systemdUnit({
  node: "/usr/bin/node",
  script: "/usr/lib/desk-yantra/server/openmausbot.ts",
  serveArgs: ["--port", "8799", "--data-dir", "/home/test/.desk-yantra"],
  dataDir: "/home/test/.desk-yantra",
  user: "testuser",
  home: "/home/test",
  bindsLowPorts: false,
  label: "arch-node",
});
assert.ok(unit.includes("Description=Desk Yantra (arch-node)"));
assert.ok(unit.includes("User=testuser"));
assert.ok(unit.includes("Environment=OMB_DATA_DIR=/home/test/.desk-yantra"));
assert.ok(unit.includes("Restart=always"));
assert.ok(unit.includes("WantedBy=multi-user.target"));

// 4. Arch packaging files check
console.log("[4] Verifying Arch packaging artifacts");
const root = join(import.meta.dirname, "../..");
const archPkg = join(root, "packaging", "arch", "PKGBUILD");
const archService = join(root, "packaging", "arch", "desk-yantra.service");
const archDesktop = join(root, "packaging", "arch", "desk-yantra.desktop");
const archLauncher = join(root, "packaging", "arch", "desk-yantra-launcher.sh");

assert.ok(existsSync(archPkg), "PKGBUILD must exist");
assert.ok(existsSync(archService), "desk-yantra.service must exist");
assert.ok(existsSync(archDesktop), "desk-yantra.desktop must exist");
assert.ok(existsSync(archLauncher), "desk-yantra-launcher.sh must exist");

const pkgContent = readFileSync(archPkg, "utf8");
assert.ok(pkgContent.includes("pkgname=desk-yantra"));
assert.ok(pkgContent.includes("license=('Apache-2.0')"));
assert.ok(pkgContent.includes("depends=('nodejs>=24'"));
assert.ok(pkgContent.includes('dist-server/openmausbot.js'));
assert.ok(!pkgContent.includes('2>/dev/null || true'));
const launcher = readFileSync(archLauncher, "utf8");
assert.ok(launcher.includes('node server/openmausbot.js'));
assert.ok(launcher.includes('OMB_STATIC_DIR'));

console.log("=== Gate 5: PASS! Packaging & Service Verified Cleanly ===");

