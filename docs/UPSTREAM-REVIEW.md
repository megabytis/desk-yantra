# Upstream review — 2026-11-19

No upstream application source was copied. These checkouts are references; the released OpenHands SDK remains the runtime dependency.

| Project | Revision | License inspected | Paths inspected |
| --- | --- | --- | --- |
| OpenHands/OpenHands | `7c49747da2860bdce4620b0fb4810ae19456c676` | MIT, root LICENSE | README.md, package.json, src/api/conversation-service/agent-server-conversation-service.api.ts, src/api/conversation-workspace.ts, __tests__/api/docker-conversation-boundaries.test.ts |
| aaif-goose/goose | `bf074d6d114690de6cbe7edc925cb26efdf6f16a` | Apache-2.0, root LICENSE | crates/goose/src/providers/provider_registry.rs, crates/goose/src/session/session_manager.rs |
| openclaw/openclaw | `307d9c45fb2548d300276c473ccb7c5cab4768bc` | MIT, root LICENSE | docs/gateway/security/index.md |

OpenHands Canvas 1.42.0 consumes the SDK TypeScript client at 1.62.0 and has explicit conversation-scoped workspace/file/terminal boundaries. Its default local backend permits direct machine access. Replacing our permission-aware backend with that default would not meet the requirement for independent host grants. Keep the released SDK and our companion, and use conversation-specific execution identity throughout.

Goose separates provider registration, model inventory, configuration and session persistence. Here, provider discovery should remain connection-scoped rather than a single provider-type-wide list. Run-level model selection must pin the exact connection, including follow-ups, and never rewrite the agent's saved default implicitly.

OpenClaw's security guidance separates gateway exposure/pairing from node execution permissions. Browser pairing here does not itself authorize host actions: execution-time grants and exact approvals remain in the companion.

The full OpenClaw checkout exhausted /tmp and was removed; only pinned documents were fetched afterward. OpenHands and Goose checkouts remain outside this repository. No reference source, credentials or desktop captures are included in the product patch.

Changes driven by this review: explicit model-facing execution context; operation schemas restricted to the intersection of profile/task/workspace authority; connection/model overrides pinned to each run; structured conversation history across follow-ups. These changes need regression testing through the current conversation UI, not only the older admin screens.
