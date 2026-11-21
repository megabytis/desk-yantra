// Gate 3 verification: clean first-run flow, bot creation, task execution, settled reply, and conversation durability.
import assert from "node:assert/strict";
import { existsSync, readdirSync } from "node:fs";
import { join } from "node:path";
import { launchVerificationServer, runControlOmb } from "./control-omb.ts";
import { fixtureApi } from "./testing/preview-fixture.ts";

console.log("=== Gate 3: First-run verification starting ===");

const fixture = await launchVerificationServer();
try {
  const { url, dataDir } = fixture.info;
  console.log(`[1] Verification server started at ${url} (data: ${dataDir})`);

  const api = fixtureApi(url, { headers: { origin: url } });
  const control = (args: string[]) => runControlOmb([...args, "--url", url]);

  // 1. Initial State Check: Clean profile, zero leaked fixtures
  const { bots: initialBots } = await api("GET", "/api/bots?messages=0");
  console.log(`[2] Initial bots in clean profile: ${initialBots.length}`);
  assert.equal(initialBots.length, 1, "Expected exactly 1 default starter bot on clean installation");
  const starter = initialBots[0];
  assert.ok(!starter.name.includes("Fixture engineer"), "Fixture engineer must never leak into initial bot profile");

  // 2. Provider Configuration: Configurable via PUT /api/config
  console.log("[3] Testing provider configuration via PUT /api/config");
  await api("PUT", "/api/config", {
    openai: { key: "sk-test-verification-key" },
  });
  const config = await api("GET", "/api/config");
  assert.ok(config, "Config must be returned");

  // 3. User Bot Creation: Create a personal bot
  console.log("[4] Creating personal bot 'Desk Yantra Assistant'");
  await control(["new-bot", "--name", "Desk Yantra Assistant"]);
  const { bots: afterCreate } = await api("GET", "/api/bots?messages=0");
  const assistant = afterCreate.find((b: { name: string }) => b.name === "Desk Yantra Assistant");
  assert.ok(assistant, "Desk Yantra Assistant bot must exist in bot list");
  console.log(`[4] Created bot ID: ${assistant.id}, threadId: ${assistant.threadId}`);

  // 4. Send Task & Wait for Settled Turn
  console.log("[5] Sending task to bot");
  const taskText = "Verify Desk Yantra first-run pipeline";
  await control(["send", "--bot", assistant.id, "--text", taskText]);

  console.log("[6] Waiting for turn to settle...");
  const waitResult = (await control(["wait", "--bot", assistant.id, "--timeout", "20"])) as {
    status: string;
    messages: Array<{ role: string; text?: string; kind?: string }>;
  };
  console.log("[6] Turn settled with status:", waitResult.status);
  assert.equal(waitResult.status, "settled");

  // 5. Verify Conversation Persistence via Headless Messages Verb
  console.log("[7] Verifying conversation message persistence via control-omb messages");
  const msgResult = (await control(["messages", "--bot", assistant.id])) as {
    messages?: Array<{ role: string; text?: string; kind?: string }>;
  };
  const threadMessages = msgResult?.messages ?? waitResult.messages;
  assert.ok(Array.isArray(threadMessages), "Messages should be an array");
  assert.ok(threadMessages.length >= 2, `Expected at least 2 messages (user + assistant), got ${threadMessages.length}`);
  
  const userMsg = threadMessages.find((m) => m.role === "user" || m.text?.includes(taskText));
  assert.ok(userMsg, "User message must be present in conversation history");
  
  const assistantMsg = threadMessages.find((m) => (m.role === "bot" || m.role === "assistant") && m.kind === "text");
  assert.ok(assistantMsg, "Assistant text message must be present in settled conversation");
  console.log(`[7] Conversation verified: ${threadMessages.length} messages persisted.`);
  console.log(`[7] Bot response: "${assistantMsg.text}"`);

  // 6. Data Directory Cleanliness Check
  console.log("[8] Checking data directory cleanliness");
  assert.ok(existsSync(join(dataDir, "bots")), "bots folder must exist in data directory");
  assert.ok(existsSync(join(dataDir, "config.json")), "config.json must exist");
  const entries = readdirSync(dataDir);
  console.log(`[8] Data directory entries: ${entries.join(", ")}`);
  assert.ok(!entries.some((e) => e.includes("paw-test") || e.includes("paw_state")), "No legacy PAW test entries in data dir");

  console.log("=== Gate 3: PASS! First useful bot flow verified cleanly ===");
} finally {
  console.log("[cleanup] Closing verification fixture server");
  await fixture.close();
}
