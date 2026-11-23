import { describe, expect, it } from "vitest";

import { cliCommand, cliPrefix } from "./cli-invocation.ts";
import { usage } from "./cli-usage.ts";

describe("cliPrefix", () => {
  it("prints container setup help with the container command", () => {
    const help = usage("docker compose exec omb desk-yantra");
    expect(help).toContain("In the container, run `desk-yantra`");
    expect(help).not.toContain("From this source checkout");
  });

  it("prints commands the way the CLI was started", () => {
    expect(cliPrefix({}, "/home/me/.npm/_npx/1a2b/node_modules/desk-yantra/dist-server/openmausbot.js")).toBe("npx desk-yantra");
    expect(cliPrefix({ npm_command: "exec" }, "/repo/node_modules/vitest/vitest.mjs"), "another tool run by npx").toBe("desk-yantra");
    expect(cliPrefix({ npm_lifecycle_event: "omb" }, "/repo/server/openmausbot.ts")).toBe("pnpm omb");
    expect(cliPrefix({ OMB_CLI_PREFIX: "docker compose exec omb desk-yantra" }, "/app/dist-server/openmausbot.js")).toBe("docker compose exec omb desk-yantra");
    expect(cliPrefix({}, "/usr/lib/node_modules/desk-yantra/dist-server/openmausbot.js")).toBe("desk-yantra");
    expect(cliCommand("pair", {}, "C:\\Users\\me\\AppData\\Local\\npm-cache\\_npx\\9\\node_modules\\desk-yantra\\x.js")).toBe("npx desk-yantra pair");
  });
});
