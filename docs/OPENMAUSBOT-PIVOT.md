# Desk Yantra product pivot: OpenMausBot base

**Decision date:** 2026-11-21. **Owner:** megabytis. **Recorded by:** OpenAI Codex (GPT-6).

## Decision

Build the next Desk Yantra product from the open-source edition of OpenMausBot, starting at local revision `4e22b4d9b` in `/home/megabytis/Github/Agent-repos/OpenMausBot`. Stop extending the current Python/React workbench as the primary product. Keep it runnable and its private `.state/` untouched during the transition; use its tested host approval and Arch/Hyprland behavior as reference. There is no automatic migration of the saved OpenAI key or old fixture records.

The Apache-2.0 core may be copied and modified with its required license, copyright and notice files. Exclude `enterprise/` (separate license), upstream names/mascot/brand assets, and any third-party component whose terms have not been checked. Use the repository's `LICENSING.md`, `NOTICE` and `third_party/` inventory when selecting the import. Record the exact upstream revision and keep future updates traceable.

## Product target

A useful personal bot app on the owner's Arch Linux/Hyprland desktop: browser chat with bots, a working OpenAI route, durable conversations, optional authorized local computer access, action evidence and recovery. A polished local first experience comes before hosted service, enterprise/team features, or broad platform claims. “Like Muse” is a product direction, not a claim of feature parity.

## Execution plan and acceptance gates

| Gate | Work | Evidence required |
| --- | --- | --- |
| 1. Baseline | Run the exact upstream OSS checkout in an isolated state, with fake engine. Record dependencies, startup commands, UI, behavior and Linux limitations. Do not connect the owner's real account or key to tests. | Clean install/build, isolated fixture conversation and browser UI check; actual results in `docs/ACCEPTANCE.md`. |
| 2. Fork | Import the OSS core into a dedicated product branch or repository path without replacing the old workbench or private state. Preserve notices; remove enterprise code and upstream branding. Set the product name and maintain an upstream revision/patch ledger. | Reproducible build from imported source, license/notice audit, source diff and no secret leakage. |
| 3. First useful bot | Make a new user able to start the app, connect OpenAI or a local engine, create/select a bot, send a task, view progress and return to the conversation. Use a clean profile, not fixture data. | One end-to-end task with a real provider, real UI and verified answer; fake-engine test for repeatability. |
| 4. Local computer and safety | Qualify file, shell, browser and desktop actions on Arch/Hyprland. Preserve explicit grants and approval for effects. Close any gap against Desk Yantra's existing safety contract before enabling the feature. | Denial/revocation/stop and real approved effect tests on this OS; independent review before remote exposure. |
| 5. Release | Provide clean install/update/rollback, responsive UX, state backup, diagnostics, CI and a distribution artifact. | Fresh-machine or clean-user install, recovery check, release smoke and owner acceptance. |

Work in coherent batches. A build or scripted fixture does not prove a real bot task. Do not run verification against the owner's live service. Use OpenMausBot's `AGENTS.md` and `docs/verification/README.md` for imported code. Keep test state isolated and remove its temporary workspaces.

## Handoff for Antigravity and other agents

1. Read this file first, then `PLANNING.md`, `docs/ACCEPTANCE.md`, upstream `AGENTS.md`, `LICENSING.md`, `NOTICE` and `docs/verification/README.md`.
2. Current active repository is `/home/megabytis/Github/personal/desk-yantra`; upstream checkout is read-only reference at `/home/megabytis/Github/Agent-repos/OpenMausBot`, revision `4e22b4d9b`. Coordinate before changing shared files. Do not edit the upstream checkout without an explicit fork decision.
3. Do not import `enterprise/`, copy branding, copy provider secrets, or delete `.state/`. The untracked `imp.md` belongs to the owner and must stay untouched.
4. Gate 1 is the immediate work. Report exactly which commands passed and what remains blocked. Then import the OSS base as one reviewable change; avoid new features in the old workbench.
