import { execFileSync } from "node:child_process";
import { mkdtempSync, readFileSync, rmSync, symlinkSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { expect, it } from "vitest";
import { probeMcpServer } from "./mcp-probe.ts";

it("answers the bot's MCP handshake with scoped tools", async () => {
  const root = mkdtempSync(join(tmpdir(), "desk-local-workspace-probe-"));
  try {
    const result = await probeMcpServer({
      command: process.execPath,
      args: ["--experimental-strip-types", join(import.meta.dirname, "local-workspace-mcp.ts")],
      env: { DESK_YANTRA_LOCAL_WORKSPACE: root }, enabled: true,
    }, 5_000);
    expect(result).toMatchObject({ ok: true });
    if (result.ok) expect(result.tools.map(tool => tool.name)).toEqual(["list_files", "read_file", "write_file", "make_folder", "run_command"]);
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

it("writes only inside the opted-in workspace and refuses an outside path", () => {
  const root = mkdtempSync(join(tmpdir(), "desk-local-workspace-test-"));
  try {
    const target = join(root, "desk-temp", "game.py");
    symlinkSync("/etc/passwd", join(root, "outside-link"));
    const request = (id: number, name: string, args: Record<string, unknown>) => JSON.stringify({
      jsonrpc: "2.0", id, method: "tools/call", params: { name, arguments: args },
    });
    const output = execFileSync(process.execPath, ["--experimental-strip-types", join(import.meta.dirname, "local-workspace-mcp.ts")], {
      env: { PATH: process.env.PATH, HOME: process.env.HOME, DESK_YANTRA_LOCAL_WORKSPACE: root },
      input: [
        request(1, "write_file", { path: target, content: "print('game')\n" }),
        request(2, "write_file", { path: join(root, "..", "outside.py"), content: "bad" }),
        request(3, "read_file", { path: "/etc/passwd" }),
        request(4, "run_command", { command: "pwd && test ! -e /home" }),
        request(5, "read_file", { path: join(root, "outside-link") }),
      ].join("\n") + "\n",
      encoding: "utf8",
    });
    const results = new Map(output.trim().split("\n").map(line => {
      const frame = JSON.parse(line);
      return [frame.id, frame.result] as const;
    }));
    expect(results.size).toBe(5);
    expect(results.get(1).isError).toBeUndefined();
    expect(readFileSync(target, "utf8")).toBe("print('game')\n");
    expect(results.get(2).isError).toBe(true);
    expect(results.get(3).isError).toBe(true);
    expect(results.get(4).isError).toBeUndefined();
    expect(results.get(4).content[0].text).toContain("/workspace");
    expect(results.get(5).isError).toBe(true);
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});
