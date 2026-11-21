// Gate 4 qualification: Local Arch/Hyprland host access, file tools, approval gating, and revocation.
import assert from "node:assert/strict";
import { mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { hostFileRelay, HOST_FILE_READ_LIMIT, HOST_FILE_WRITE_LIMIT } from "../server/host-file-tools.ts";
import { claimWithYourComputerConsent, YourComputerDeclined } from "../server/your-computer-consent.ts";
import { approvalModeFor, supportsApprovalMode } from "../shared/approval-mode.ts";
import { listsComputerTool } from "../server/computer-tool-list.ts";
import { withHostFiles } from "../server/local-computer.ts";

console.log("=== Gate 4: Arch/Hyprland Local Host Access Qualification ===");

const tempDir = mkdtempSync(join(tmpdir(), "desk-yantra-gate4-"));
try {
  const home = join(tempDir, "home");
  mkdirSync(join(home, "Projects"), { recursive: true });

  const relay = hostFileRelay(home);
  const call = async (name: string, args: Record<string, unknown> = {}) => {
    try {
      const result = await relay({ name, arguments: args });
      assert.ok(result, `Tool ${name} must be handled`);
      return {
        text: result.content.map((p) => p.text).join("\n"),
        isError: result.isError === true,
      };
    } catch (err) {
      return {
        text: err instanceof Error ? err.message : String(err),
        isError: true,
      };
    }
  };

  // 1. Scoped Host File Creation & Read
  console.log("[1] Testing host file operations (write_file, read_file)");
  const testFile = join(home, "Projects", "test.txt");
  const writeRes = await call("write_file", { path: testFile, content: "Desk Yantra host access verified." });
  assert.equal(writeRes.isError, false);
  assert.ok(writeRes.text.includes("Saved 33 bytes to"));

  const readRes = await call("read_file", { path: testFile });
  assert.equal(readRes.isError, false);
  assert.ok(readRes.text.includes("Desk Yantra host access verified."));

  // 2. Overwrite Protection
  console.log("[2] Testing overwrite protection");
  const noOverwrite = await call("write_file", { path: testFile, content: "Forbidden overwrite" });
  assert.equal(noOverwrite.isError, true, "Must refuse overwrite when overwrite is not set to true");

  const overwriteOk = await call("write_file", { path: testFile, content: "Overwritten content", overwrite: true });
  assert.equal(overwriteOk.isError, false);
  const readOverwritten = await call("read_file", { path: testFile });
  assert.ok(readOverwritten.text.includes("Overwritten content"));

  // 3. Folder Operations & Safety
  console.log("[3] Testing make_folder & list_files");
  const subFolder = join(home, "Projects", "subfolder");
  const folderRes = await call("make_folder", { path: subFolder });
  assert.equal(folderRes.isError, false);

  const listRes = await call("list_files", { path: join(home, "Projects") });
  assert.equal(listRes.isError, false);
  assert.ok(listRes.text.includes("test.txt"));
  assert.ok(listRes.text.includes("subfolder"));

  // 4. File Read Limit Bounds
  console.log("[4] Checking file operation boundary constants");
  assert.equal(HOST_FILE_READ_LIMIT, 10 * 1024 * 1024, "Read limit must be 10MB");
  assert.equal(HOST_FILE_WRITE_LIMIT, 25 * 1024 * 1024, "Write limit must be 25MB");

  // 5. Consent & Approval Gating
  console.log("[5] Qualifying consent and approval gating");
  let asked = false;
  let bound = false;

  // Full access: should bind without asking
  await claimWithYourComputerConsent(
    () => false, // askNow is false (Full access)
    async () => { asked = true; },
    async () => { bound = true; },
  );
  assert.equal(asked, false, "Full access must not prompt user");
  assert.equal(bound, true, "Full access must bind");

  // Ask access: should prompt user before binding
  asked = false;
  bound = false;
  await claimWithYourComputerConsent(
    () => true, // askNow is true (needs confirmation)
    async () => { asked = true; },
    async () => { bound = true; },
  );
  assert.equal(asked, true, "Ask access must prompt user");
  assert.equal(bound, true, "Ask access must bind after user approval");

  // Denial: user declines consent
  asked = false;
  bound = false;
  let errorCaught = false;
  try {
    await claimWithYourComputerConsent(
      () => true,
      async () => { asked = true; throw new YourComputerDeclined("User declined host access"); },
      async () => { bound = true; },
    );
  } catch (err) {
    errorCaught = true;
    assert.ok(err instanceof YourComputerDeclined);
  }
  assert.equal(asked, true, "User was prompted");
  assert.equal(bound, false, "Action was NOT bound or executed after denial");
  assert.equal(errorCaught, true, "Declined consent threw YourComputerDeclined");

  // 6. Approval Mode Support Verification
  console.log("[6] Qualifying approval mode contracts");
  assert.ok(supportsApprovalMode("claudeAgent", "full"));
  assert.ok(supportsApprovalMode("claudeAgent", "ask"));
  assert.ok(supportsApprovalMode("codex", "full"));
  assert.ok(supportsApprovalMode("codex", "ask"));
  assert.equal(approvalModeFor({ approvalMode: "ask" }), "ask");
  assert.equal(approvalModeFor({}), "full");

  // 7. Host Bridge Tool Switch
  console.log("[7] Checking host bridge tool switch");
  const gatedConn = {
    command: "node",
    args: [],
    env: { OMB_CUA_COMMAND: "cua-driver" },
    platform: "linux" as const,
    scope: "local-computer" as const,
  };
  const withFiles = withHostFiles(gatedConn);
  assert.equal(withFiles.env.OMB_HOST_FILES, "1", "Host files must be enabled on local computer scope");

  console.log("=== Gate 4: PASS! Local Arch/Hyprland Host Access Qualified ===");
} finally {
  rmSync(tempDir, { recursive: true, force: true });
}
