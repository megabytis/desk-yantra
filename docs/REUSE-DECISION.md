# Runtime reuse decision — 2026-11-21

Author: OpenAI Codex (GPT-6), under owner direction. This is a source review and implementation decision for the current single-user, loopback Desk Yantra. It is not a security certification or a claim that the other projects have been exhaustively audited. No external source or assets were copied.

## Decision

Keep the released `openhands-sdk==1.62.0` as the sole model/agent loop. Desk Yantra already delegates inference, tool iteration, and conversation events to it in `workbench/worker.py`. Keep the local companion as the only effectful tool executor: the companion verifies current grants and consumes exact approvals at execution time. Build larger feature batches around this seam, using focused ideas and independently licensed components from reference projects where they fit. Do not embed a second full agent loop beside OpenHands.

| Candidate | What was inspected | Reuse decision | Reason |
| --- | --- | --- | --- |
| Desk Yantra + released OpenHands SDK | `pyproject.toml`, `workbench/worker.py`, `workbench/companion.py`, `workbench/server.py`, `docs/ARCHITECTURE.md` | **Keep** as core | Already has working model calls, focused tool schemas, event capture and local-model tests. The companion is the policy boundary. |
| Hermes Agent `32dbc1dcda` (MIT) | `agent/turn_facade.py`, `agent/tool_executor.py`, `tools/approval.py`, README and LICENSE | **Mine specific patterns; do not transplant runtime** | Its own conversation loop, tool dispatcher, session lease, gateway queues and approval modes are coupled. Its in-memory/session allowlists and YOLO mode do not directly satisfy Desk Yantra's exact, one-use companion approvals. Useful focused references include tool-result spillover/budgets, failure recovery and session operations. Copying a component requires dependency, test and notice review. |
| OpenMausBot `4e22b4d9b` (Apache-2.0 outside `enterprise/`) | README, `DESIGN.md`, `LICENSING.md`, `server/agents-turn.ts`, `server/agent-tool-policy.ts`, `packages/phone-protocol/src/approval-mode.ts` | **Use product/UX patterns; evaluate isolated adapters later** | Its chat roster and bot identity are useful for the live UI. Its server orchestrates external engine drivers and has `full` as the default approval mode. Desk Yantra's current exact-approval contract and Arch/Hyprland host goals differ. `enterprise/` has a separate license; branding and mascot are not reusable. |
| OpenCode | Not present in `/home/megabytis/Github/Agent-repos` during this audit | **No decision** | A future local checkout can be compared against the same execution and licensing criteria. |

## What to build next as one batch

1. Bring the approved product-preview layout into the live browser app: bot roster, one conversation surface, workspace/approval/result evidence panels. Keep existing API, SDK runtime, grants and exact approval checks. The preview remains a sample until owner feedback settles the layout.
2. Add one useful bot capability with a clear boundary, such as durable project memory or better long-run context handling, after inspecting the relevant Hermes and OpenHands modules. The capability must use the existing run identity and companion for effects.
3. Run a single end-to-end verification pass for that batch: first-run fixture, real approved file/command task, denial and recovery, frontend build and CI. Keep live provider/Desktop prerequisites separately labelled.

## Reuse rule

Before importing source, record the exact upstream path/revision, license and notices; identify its transitive dependencies; prove it cannot bypass companion authorization; and retain a regression against the real effect. Reading a design or adapting an idea requires no copied-source attribution, but is still recorded here for provenance. Existing OpenMausBot and Hermes trademarks, artwork and enterprise code are outside this plan.
