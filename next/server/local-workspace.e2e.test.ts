import { createServer } from "node:http";
import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";
import { expect, it } from "vitest";
import { launchVerificationServer, runControlOmb } from "../scripts/control-omb.ts";
import { isTitleCall } from "./testing/title-call.ts";

it("asks before an OpenAI-compatible bot writes into the explicitly shared workspace", async () => {
  const requests: any[] = [];
  let target = "";
  const provider = createServer(async (req, res) => {
    if (req.url === "/v1/models") {
      res.setHeader("content-type", "application/json");
      res.end(JSON.stringify({ data: [{ id: "fixture-model" }] }));
      return;
    }
    let raw = "";
    for await (const chunk of req) raw += chunk;
    if (!raw) { res.writeHead(404).end(); return; }
    const body = JSON.parse(raw);
    if (isTitleCall(body)) { res.writeHead(500).end(); return; }
    requests.push(body);
    const result = body.messages.find((message: any) => message.role === "tool");
    const tool = body.tools?.find((entry: any) => entry.function.name.includes("desk_local_workspace") && entry.function.name.includes("write_file"));
    const event = (delta: unknown, finish_reason: string) => `data: ${JSON.stringify({ choices: [{ index: 0, delta, finish_reason }] })}\n\ndata: [DONE]\n\n`;
    res.writeHead(200, { "content-type": "text/event-stream" });
    if (result) res.end(event({ content: "The file was saved." }, "stop"));
    else if (tool) res.end(event({ tool_calls: [{ index: 0, id: "local-write", type: "function", function: { name: tool.function.name, arguments: JSON.stringify({ path: target, content: "print('game')\n" }) } }] }, "tool_calls"));
    else res.end(event({ content: "The local workspace tool was not offered." }, "stop"));
  });
  await new Promise<void>(resolve => provider.listen(0, "127.0.0.1", resolve));
  const address = provider.address();
  if (!address || typeof address === "string") throw new Error("fixture provider address missing");
  const fixture = await launchVerificationServer({ ...process.env, OMB_TEST_LOCAL_WORKSPACE: "1" });
  target = join(fixture.info.dataDir, "shared-local-workspace", "desk-temp", "game.py");
  const control = (args: string[]) => runControlOmb([...args, "--url", fixture.info.url]) as Promise<any>;
  const api = async (method: string, path: string, body?: unknown) => {
    const response = await fetch(`${fixture.info.url}${path}`, {
      method, headers: { "content-type": "application/json", origin: fixture.info.url },
      ...(body === undefined ? {} : { body: JSON.stringify(body) }),
    });
    const data = await response.json() as any;
    expect(response.ok, JSON.stringify(data)).toBe(true);
    return data;
  };
  try {
    await api("PATCH", "/api/config", { openaiCompat: { key: "synthetic-fixture-key", url: `http://127.0.0.1:${address.port}/v1`, model: "fixture-model" } });
    const { bot } = await control(["new-bot", "--name", "Workspace fixture"]);
    await control(["set-model", "--bot", bot.id, "--instance", "openaiCompat", "--model", "fixture-model"]);
    await api("PATCH", `/api/bots/${bot.id}`, { approvalMode: "ask", description: "Local workspace verification bot" });
    await control(["send", "--bot", bot.id, "--task", bot.activeTaskId, "--text", "Create the game file in my shared local workspace."]);
    expect((await control(["wait", "--bot", bot.id, "--task", bot.activeTaskId, "--timeout", "20"])).status).toBe("needs-user");
    expect(existsSync(target)).toBe(false);
    const bots = await api("GET", "/api/bots");
    const current = bots.bots.find((entry: any) => entry.id === bot.id);
    const card = current.messages.find((message: any) => message.card?.requestId && !message.card.answered)?.card;
    expect(card?.requestId).toBeTruthy();
    await api("POST", `/api/bots/${bot.id}/respond`, { threadId: bot.activeTaskId, requestId: card.requestId, behavior: "allow" });
    expect((await control(["wait", "--bot", bot.id, "--task", bot.activeTaskId, "--timeout", "20"])).status).toBe("settled");
    expect(readFileSync(target, "utf8")).toBe("print('game')\n");
    expect(requests.some(request => request.tools?.some((tool: any) => tool.function.name.includes("desk_local_workspace")))).toBe(true);
  } finally {
    await fixture.close();
    provider.closeAllConnections();
    await new Promise<void>(resolve => provider.close(() => resolve()));
  }
}, 120_000);
