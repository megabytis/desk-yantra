import { createInterface } from "node:readline";
import { existsSync, realpathSync } from "node:fs";
import { dirname, isAbsolute, relative, resolve } from "node:path";
import { homedir } from "node:os";
import { spawn } from "node:child_process";
import { HOST_FILE_TOOLS, hostFileRelay } from "./host-file-tools.ts";

const rootValue = process.env.DESK_YANTRA_LOCAL_WORKSPACE;
if (!rootValue || !isAbsolute(rootValue) || !existsSync(rootValue)) {
  process.stderr.write("Desk Yantra local workspace needs an existing absolute directory.\n");
  process.exit(2);
}
const root = realpathSync(rootValue);
const requestedRoot = resolve(rootValue);
const files = hostFileRelay(homedir());
const RUN_TOOL = {
  name: "run_command",
  description: "Run a shell command in the shared local workspace. Only that directory is writable; networking and the desktop are unavailable. Output is capped at 64 KB and time at 60 seconds.",
  inputSchema: { type: "object", properties: {
    command: { type: "string", description: "Shell command to run inside /workspace." },
    timeout_seconds: { type: "integer", minimum: 1, maximum: 60 },
  }, required: ["command"], additionalProperties: false },
} as const;

function inside(target: string): boolean {
  const offset = relative(root, target);
  return offset === "" || (offset !== ".." && !offset.startsWith("../") && !isAbsolute(offset));
}

function safePath(raw: unknown): string | null {
  if (typeof raw !== "string" || !isAbsolute(raw)) return null;
  try {
    const target = resolve(raw);
    const requestedOffset = relative(requestedRoot, target);
    if (requestedOffset === ".." || requestedOffset.startsWith("../") || isAbsolute(requestedOffset)) return null;
    let existing = target;
    while (!existsSync(existing)) {
      const parent = dirname(existing);
      if (parent === existing) return null;
      existing = parent;
    }
    const canonical = resolve(realpathSync(existing), relative(existing, target));
    return inside(canonical) ? canonical : null;
  } catch {
    return null;
  }
}

function answer(id: unknown, result: unknown): void {
  process.stdout.write(`${JSON.stringify({ jsonrpc: "2.0", id, result })}\n`);
}

const refused = (message: string) => ({ isError: true, content: [{ type: "text", text: message }] });
type ToolResult = { content: Array<{ type: string; text: string }>; isError?: boolean };

async function runCommand(args: Record<string, unknown>) {
  if (process.platform !== "linux") return refused("Local workspace commands currently require Linux.");
  if (typeof args.command !== "string" || !args.command.trim() || args.command.includes("\0") || args.command.length > 16_000 ||
    (args.timeout_seconds !== undefined && (!Number.isInteger(args.timeout_seconds) || Number(args.timeout_seconds) < 1 || Number(args.timeout_seconds) > 60))) {
    return refused("Give a nonempty command and a timeout from 1 to 60 seconds.");
  }
  const timeout = Number(args.timeout_seconds ?? 30) * 1_000;
  const argv = [
    "--ro-bind", "/usr", "/usr", "--ro-bind", "/etc", "/etc",
    "--symlink", "usr/lib", "/lib", "--symlink", "usr/lib", "/lib64", "--symlink", "usr/bin", "/bin",
    "--bind", root, "/workspace", "--proc", "/proc", "--dev", "/dev", "--tmpfs", "/tmp",
    "--chdir", "/workspace", "--unshare-net", "--unshare-pid", "--unshare-ipc", "--unshare-uts", "--new-session", "--cap-drop", "ALL", "--die-with-parent",
    "--setenv", "HOME", "/workspace", "--setenv", "PATH", "/usr/bin:/bin", "--setenv", "LANG", "C.UTF-8",
    "--", "/usr/bin/bash", "-c", args.command,
  ];
  return await new Promise<ToolResult>((resolveResult) => {
    const child = spawn("/usr/bin/bwrap", argv, { shell: false, env: { PATH: "/usr/bin:/bin" }, stdio: ["ignore", "pipe", "pipe"] });
    let output = "";
    let clipped = false;
    let timedOut = false;
    const timer = setTimeout(() => { timedOut = true; child.kill("SIGKILL"); }, timeout);
    const collect = (chunk: Buffer) => {
      if (output.length >= 64 * 1024) { clipped = true; return; }
      output += chunk.toString("utf8").slice(0, 64 * 1024 - output.length);
      if (output.length >= 64 * 1024) clipped = true;
    };
    child.stdout.on("data", collect);
    child.stderr.on("data", collect);
    child.on("error", error => { clearTimeout(timer); resolveResult(refused(error.message)); });
    child.on("close", code => {
      clearTimeout(timer);
      const text = `${output}${clipped ? "\n[output truncated]" : ""}\nExit code: ${timedOut ? "timed out" : code}`;
      resolveResult(code === 0 && !timedOut ? { content: [{ type: "text", text }] } : refused(text));
    });
  });
}

createInterface({ input: process.stdin, crlfDelay: Infinity }).on("line", async line => {
  let frame: any;
  try { frame = JSON.parse(line); } catch { return; }
  if (frame?.id === undefined) return;
  if (frame.method === "initialize") {
    answer(frame.id, { protocolVersion: "2025-03-26", capabilities: { tools: {} }, serverInfo: { name: "desk-yantra-local-workspace", version: "1.0.0" } });
    return;
  }
  if (frame.method === "ping") { answer(frame.id, {}); return; }
  if (frame.method === "tools/list") { answer(frame.id, { tools: [...HOST_FILE_TOOLS, RUN_TOOL] }); return; }
  if (frame.method !== "tools/call") {
    process.stdout.write(`${JSON.stringify({ jsonrpc: "2.0", id: frame.id, error: { code: -32601, message: "Unknown method" } })}\n`);
    return;
  }
  const name = frame.params?.name;
  const args = frame.params?.arguments;
  if (!(HOST_FILE_TOOLS.some(tool => tool.name === name) || name === RUN_TOOL.name) || !args || typeof args !== "object" || Array.isArray(args)) {
    answer(frame.id, refused("Unknown local workspace tool or invalid arguments."));
    return;
  }
  if (name === RUN_TOOL.name) { answer(frame.id, await runCommand(args)); return; }
  const target = safePath(args.path ?? (name === "list_files" ? root : undefined));
  if (!target) { answer(frame.id, refused(`Path must stay inside ${root}.`)); return; }
  try {
    const result = await files({ name, arguments: { ...args, path: target } });
    answer(frame.id, result ?? refused("Unknown local workspace tool."));
  } catch (error) {
    answer(frame.id, refused(error instanceof Error ? error.message : String(error)));
  }
});
