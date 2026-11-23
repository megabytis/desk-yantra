# Acceptance ledger

This file is the continuation handoff. Fixture and live evidence must remain separate.

| Scenario | Status / evidence |
| --- | --- |
| Released OpenHands SDK inference → tool → observation | PASS: `tests/test_sdk.py`, loopback HTTP fixture, actual SDK 1.62.0 |
| React/TypeScript production build | PASS: `npm run build` |
| Denied command never runs | PASS: `test_denial_revocation_and_replay`, absent marker file |
| Grant revocation blocks subsequent reads | PASS: same test |
| Approval replay blocked | PASS: same test |
| Host traversal / symlink escape blocked | PASS: scoped-file test |
| Stop terminates command process group | PASS: disposable sleep test |
| Companion authentication / browser origin validation | PASS: companion test |
| Provider key output redaction | PASS: redaction test |
| Browser provider/model/host Git repair/download | PASS: Chromium UI test, 17.9 seconds; fixture discovery/inference, real failed test, proposed diff, approved edit, passing test, disk verification and downloaded artifact |
| Live local model discovery/inference/tool call | PASS LIVE on 2026-11-20: actual Qwen3-0.6B Q8_0 via installed llama-server; Chromium discovers model, tests inference, executes approved SDK file-writing tool, verifies real disk contents, and downloads matching artifact. 1 passed in 21.1 seconds. Ollama-specific live verification remains pending. |
| Live hosted connection/model switch | BLOCKED: no paid-provider credentials supplied |
| Docker browse → file → UI download | PASS LIVE on 2026-11-20: real Qwen3 local inference, Chromium inside Docker, controlled HTML page, approved page-derived file, screenshot, UI download. Container inspected: unprivileged agent user, no host mounts, capabilities dropped. 58.1 seconds. |
| Delegation and tab-close reconnect | PASS: Chromium control test; worker writes real artifact, tab closes/reopens, both histories and parent model connection remain identifiable |
| Hyprland screen capture | PASS LIVE: companion HTTP 200, valid private PNG via `PYTHONPATH=. PAW_STATE=/tmp/paw-desktop-state .venv/bin/python tests/live_desktop.py`; image never displayed/uploaded |
| Hyprland keyboard | PASS LIVE on 2026-11-20: authenticated companion + wtype typed an exact marker into a focus-checked disposable native Wayland Chromium window; revocation blocked a subsequent call. Fixture action driver, actual OS input. No desktop recording saved. |
| Hyprland mouse | Adapter implemented, command construction fixture-tested; live verification blocked by missing ydotool/accessible ydotoold socket. Sandbox pointer control is independently live-verified. |
| Public repository | PASS: initial source commit `7980f3b9e45fcc053a71ae03d0c809c7f611add0` pushed to `megabytis/desk-yantra` main and verified via git ls-remote. Public GitHub Actions API returned the initial workflow in progress. CI completion remains pending. |

## Remaining implementation

- Broader read-only sharing stress validation. Post-task sandbox browser takeover is implemented and live-verified. Active-agent takeover is unavailable to prevent overlapping actions.
- Permanent provider/agent deletion. Reversible archival is implemented with new-run enforcement, restore controls, and retained credentials/history. Editing profiles and connections, Markdown/code/table rendering, guided setup, searchable runs, conversation grouping, reconnect warnings, mobile navigation and typed approvals are implemented.
- Full SDK conversation checkpoint recovery; current recovery redoes safe inference/reads only and blocks uncertain mutations. Explicit review resolution records the observed outcome, requires companion cleanup, invalidates stale approvals, and enables fresh follow-up work without replay.
- Broader provider metadata/catalog suggestions and live native-provider verification. Pagination, credentials and errors have HTTP fixture tests.
- Live stress verification of revocation during concurrent operations; companion admissions now synchronize with revocation. Approval consumption, process identity recovery and task-wide budgets are implemented.
- Portal consent integration and live host pointer validation. This Hyprland session advertises Screenshot and ScreenCast portals, not RemoteDesktop. Host wtype input is live-verified independently of sandbox input.
- Live hosted-provider, native Ollama, host-pointer, and vision-inference tests. Local compatible-server and Docker journeys are live-verified. UI delegation/deny/revoke/stop fixture tests pass.

## Verification commands and observations

| Command | Observed |
| --- | --- |
| `npm run build` | TypeScript and Vite production build pass |
| `PAW_STATE=/tmp/paw-final-unit LITELLM_LOCAL_MODEL_COST_MAP=True .venv/bin/python -m pytest -q` | 17 passed; SDK dependency warnings; tests include safe-vs-uncertain restart, task budget, background child stop and redaction across terminal chunks |
| `npx playwright test tests/ui/journey.spec.ts` | 1 passed, real host Git repair + downloaded artifact, scripted model fixture |
| `npx playwright test tests/ui/control.spec.ts` | 2 passed (35 seconds), delegation/reconnect plus deny/revoke/stop, scripted model fixture |
| `npx playwright test` | All 3 passed together in 46.3 seconds; selectors bind to exact run IDs and artifact ownership |
| Final `npx playwright test` after conversation/startup changes | All 3 passed in about 1 minute, including follow-up messages and persisted context |
| `.venv/bin/python tests/browser_probe.py` | PASS local Chromium fixture: navigation, persistent fill/click, PNG screenshot and real page-derived file; does not establish Docker isolation |
| `PYTHONPATH=. PAW_STATE=/tmp/paw-desktop-state .venv/bin/python tests/live_desktop.py` | Live Hyprland capture HTTP 200 and valid PNG; image private under `/tmp` |
| Initial `docker info` | Daemon initially stopped; user subsequently started it. Actual Docker journeys and sharing now pass. |
| `sudo -n systemctl start docker` | Password required; no system change performed |
| `curl http://127.0.0.1:11434/api/tags` | No local model server listening |
| Final `curl -fsS -o /dev/null -w '%{http_code}' http://127.0.0.1:8765/` | HTTP 200; application left running |
| `npx playwright test --config playwright.live.config.ts` | PASS LIVE, 21.1 seconds, 2026-11-20. Model SHA-256 `9465e63a22add5354d9bb4b99e90117043c7124007664907259bd16d043bb031`. Actual discovery/inference/tool/approval/download; no scripted model response. |
| `PAW_STATE=/tmp/paw-final-check LITELLM_LOCAL_MODEL_COST_MAP=True .venv/bin/python -m pytest -q` | 22 passed on 2026-11-20 after workspace preflight checks; dependency warnings only. |
| `npm run build` on 2026-11-20 | TypeScript and production bundle pass. |
| `npx playwright test --config playwright.live.config.ts tests/live/sandbox.spec.ts` | PASS LIVE: initial Docker journey 58.1 seconds; extended takeover journey 50.3 seconds, including screenshot-based clicks, typing into an actual input, clicking the page button, and returning control. |
| `PAW_STATE=/tmp/paw-takeover-check LITELLM_LOCAL_MODEL_COST_MAP=True .venv/bin/python -m pytest -q` | 25 passed; includes rejection of host/running-agent takeover, exact user-action approvals, and revoked grants. |
| Latest `npx playwright test --config playwright.live.config.ts` | Both live suites passed together in 1.2 minutes: redesigned real-model setup and Docker browser takeover, including downloaded file equality against the actual container file. |
| Latest `npx playwright test` after focused tools / UI integration | All 3 fixture UI suites passed in 1.4 minutes: delegation/reconnect, deny/revoke/stop, and real Git repair/download. |
| `PAW_STATE=/tmp/paw-filetools-check LITELLM_LOCAL_MODEL_COST_MAP=True .venv/bin/python -m pytest -q` | 26 passed; includes file-only project listing, nested file creation, traversal rejection and blocked shell escalation. |
| `PYTHONPATH=. PAW_STATE=/tmp/paw-readonly-check .venv/bin/python tests/docker_sharing_probe.py` | PASS actual Docker/companion sharing: host file mode 0600, directory mode 0700, readable only through the explicit share, writes denied, host content unchanged, sole mount is read-only `/shared`. Action driver is a fixture; Docker and files are real. |
| `npx playwright test --config playwright.live.config.ts tests/live/host-repair.spec.ts` with official Qwen3-1.7B Q8_0 | PASS LIVE in 3 minutes. Actual model observed failing test, read code, proposed approved arithmetic-only change, reran passing test, and disk/Git diff checks passed. Model SHA-256 `061b54daade076b5d3362dac252678d17da8c68f07560be70818cace6590cb1a`. |
| Same repair scenario with Qwen3-0.6B | FAILED: model finished without applying a fix. This failure is retained as evidence of model limitations. The runtime now performs one bounded evidence review and surfaces unresolved last-command failures independently of model claims. |
| `PYTHONPATH=. PAW_STATE=/tmp/paw-live-input .venv/bin/python tests/live_host_input.py` | PASS LIVE: wtype input reached the exact focus-checked disposable Hyprland window; revoked grant rejected another call. Earlier attempts sent no input because window/focus checks failed; probe was corrected for Chromium title suffix and mapping. |
| `PAW_STATE=/tmp/paw-supervision-tests LITELLM_LOCAL_MODEL_COST_MAP=True .venv/bin/python -m pytest -q` | 28 passed: includes failed-worker supervision, review of uncertain actions and atomic transitions that cannot resurrect a stopped task. |
| `npx playwright test tests/ui/settings.spec.ts` | PASS, 4.1 seconds: edit/rename a connection without exposing or losing its key; preserve its discovered models; change agent instructions/model and verify after reload. |
| `PAW_STATE=/tmp/paw-final-product-tests LITELLM_LOCAL_MODEL_COST_MAP=True .venv/bin/python -m pytest -q` | 29 passed; includes image-observation gating. Actual vision-model inference remains unverified; the text-only/unknown path never forwards image bytes. |
| `PAW_STATE=/tmp/paw-archive-review-tests LITELLM_LOCAL_MODEL_COST_MAP=True .venv/bin/python -m pytest -q` | 31 passed, 2 dependency warnings. Adds archival enforcement without deleting evidence/credentials and review resolution that fails closed when companion cleanup is unavailable, cancels approvals, and never replays actions. |
| `npx playwright test` after archival/review controls | All 4 passed together in 1.5 minutes. Includes archive/restore with retained keys/models, stopped-run review notes, confirmed process termination, delegation/reconnect, and actual Git repair. Model responses are scripted fixtures. |
| `PAW_STATE=/tmp/paw-stop-confirm-tests LITELLM_LOCAL_MODEL_COST_MAP=True .venv/bin/python -m pytest -q` | 34 passed, 2 dependency warnings. Adds failure-path checks: Docker cleanup cannot report success when the daemon is unreachable or a container remains. Confirmed absence is accepted. |
| `PYTHONPATH=. PAW_STATE=/tmp/paw-final-sharing-stop .venv/bin/python tests/docker_sharing_probe.py` | PASS actual Docker: explicit private read-only share, rejected write, unchanged host contents; Stop response followed by an independent Docker query proving container absence. Fixture driver, real Docker enforcement. |
| Final service checks after stop-confirmation restart | Workbench HTTP 200 on 8765; real local llama-server health status `ok` on 18768. |
| `PAW_STATE=/tmp/paw-recovery-full-check2 LITELLM_LOCAL_MODEL_COST_MAP=True .venv/bin/python -m pytest -q` | 35 passed, 2 dependency warnings. Restart recovery now requires the companion to confirm prior tool cleanup before requeueing even read-only work; otherwise the run remains in review with no replay. This is a fixture/fault-path test, not a reboot test. |
| `PAW_STATE=/tmp/paw-output-bound-check2 LITELLM_LOCAL_MODEL_COST_MAP=True .venv/bin/python -m pytest -q tests/test_permissions.py` | 9 passed. Real subprocess producing 250,000 characters and exit 7 was capped at 200,000 in the returned observation and terminal event stream; the truncated marker and actual nonzero exit remained visible. |
| `PAW_STATE=/tmp/paw-output-full-check LITELLM_LOCAL_MODEL_COST_MAP=True .venv/bin/python -m pytest -q` | 36 passed, 2 dependency warnings, after bounded terminal output change. This is a per-command capture limit, not a per-run or disk quota. |
| `npm run build` on 2026-11-20 | TypeScript and Vite bundle pass with remaining tool budget surfaced in task identity header. |
| `PAW_STATE=/tmp/paw-quota-security-check2 LITELLM_LOCAL_MODEL_COST_MAP=True .venv/bin/python -m pytest -v` | 44 passed, 3 warnings in 11.79s on 2026-11-20. Adds companion-enforced task-wide tool budget check, aggregate run output quota across commands (500k chars), artifact count (20) & storage size (5MB file / 20MB run) quotas, request payload limit (10MB HTTP 413), session logout, token rotation across server and companion, and Origin/Host/CSRF header validation. |
| `npx playwright test` after quota & security changes | All 4 passed together in 1.2 minutes against running local app: delegation/reconnect, deny/revoke/stop, Git repair/download, and connection/agent settings. |
| Restarted workbench service check | Workbench HTTP 200 on 8765; companion HTTP 403 on missing auth on 8766. |

| Desk Yantra migration verification | Locked install and frontend build passed in the official clone; Python suite: 44 passed, 3 dependency warnings. Private artifact paths relocated: 58 records, zero missing artifact files. |

| `npx playwright test` from `desk-yantra` after migration | All 4 fixture UI tests passed in 46.9s: delegation/reconnect, deny/revoke/stop, actual Git repair/download, and settings. The fixture responses are scripted; OS effects are real disposable test effects. |

Do not mark these complete based on mocks, screenshots, or code inspection alone. Current source is a runnable initial product, not the entire requested scope.

## Phase 0 fixture reproducibility — 2026-11-20

Contributor: **OpenAI Codex (GPT-6)**, under owner direction.

Implemented `scripts/check_ui.py`: private disposable PAW_STATE, occupied-port checks (tolerating TCP TIME_WAIT), service readiness, matching token path for UI tests, application stop followed by service process-group cleanup on success/failure. CI now invokes this runner instead of backgrounding `uv run`, has read-only repository permissions and a 20-minute timeout. CLI stop now includes approval-waiting runs, covered by `tests/test_cli.py`. Added CONTRIBUTING.md, SECURITY.md and docs/RELEASE.md; README documents the isolated command.

GitHub Actions was checked through the public API and job logs. [Migration run 44706109312](https://github.com/megabytis/desk-yantra/actions/runs/44706109312), commit `dfb992e407abf9f4657d37724fc120639e117768`, **failed** despite all test steps passing (44 Python tests, four UI tests in 53.1s, build and Chromium probe). The setup-uv post-job `uv cache prune --ci` timed out after 300 seconds waiting for the cache lock retained by background uv services. Starting services directly with Python and owning their cleanup addresses that lifecycle cause. The revised workflow has not been pushed or verified on GitHub; CI success remains an open gate.

| Command / check | Actual result this session |
| --- | --- |
| `npm run build` | PASS TypeScript and Vite build, Vite bundling 1.11s. |
| `PAW_STATE=/tmp/desk-yantra-unit-verified LITELLM_LOCAL_MODEL_COST_MAP=True .venv/bin/python -m pytest -q` | PASS 45 tests, 3 dependency warnings in 7.00s, including CLI stop while waiting for approval. |
| `.venv/bin/python tests/browser_probe.py` | PASS local Chromium fixture: navigation, persistent fill/click, keyboard takeover, screenshot and file creation. |
| `.venv/bin/python scripts/check_ui.py` | PASS four UI tests against fresh private state (1.1m before final port/cleanup refinement). Scripted model fixture; actual disposable file/process effects. Final verification below. |
| Second runner while first suite was active | Correctly refused occupied port 8765 with exit 1 before starting services. |
| `.venv/bin/python scripts/check_ui.py --grep no-such-fixture-check` | Expected exit 1 with `No tests found`; cleanup completed, allowing immediate subsequent runner startup. |
| Credential-signature scan of all 61 tracked files | No selected private-key, GitHub-token, provider-key or AWS-key signatures matched; no tracked private runtime-state paths. This bounded scan is not a comprehensive secret/history audit. |
| `git diff --check` | PASS. |

Initial sandboxed network checks could not create sockets; the Python and browser fixture checks above ran with approved escalation. An initial restricted Python invocation was interrupted after stalling on socket-dependent tests; its partial output is not counted as verification. No hosted-provider, native Ollama, Docker isolation, clean Arch installation or desktop verification was performed in this milestone. Project license selection, dependency notices, release supply-chain controls, state upgrade/rollback tests and Phase 1 security review remain open. No upstream source was copied.

Final completed runner verification: `.venv/bin/python scripts/check_ui.py` exited 0 with **4 passed (1.1m)** after the cleanup and TCP port-reuse changes. These are scripted model fixtures with real disposable host effects. Post-run HTTP connection to port 8765 was refused, confirming the application listener was closed.

## Phase 1 threat model — 2026-11-20

Contributor: **OpenAI Codex (GPT-6-sol)**. GitHub Actions run [44708120050](https://github.com/megabytis/desk-yantra/actions/runs/44708120050) for commit `b01b9b5` was checked via the public Actions API and reported `completed` / `success`. Added `docs/THREAT-MODEL.md` with the trusted single-user target, eight execution/data boundaries, existing controls, residual risks and concrete next tests. This documentation change has no new runtime security claim; independent review remains open. `git diff --check` passed.

## Revocation race regression — 2026-11-20

Contributor: **OpenAI Codex (GPT-6-sol)**. A write paused immediately after one-use approval consumption was revoked before file admission. The request returned 403 and created no file. Initial focused test: 10 passed. The first full run exposed a revoke 500 caused by a historical run record missing `grant`; companion now skips records without a matching grant. Final `PAW_STATE=/tmp/desk-yantra-race-fixed LITELLM_LOCAL_MODEL_COST_MAP=True .venv/bin/python -m pytest -q --tb=short`: **46 passed, 3 warnings in 7.05s**. This verifies the controlled admission race, not all revocation timings or a live hostile workload.

## Shell launch revocation race — 2026-11-20

Contributor: **OpenAI Codex (GPT-6-sol)**. Added deterministic test pausing a shell action after its exact approval was consumed, revoking its grant, then releasing execution. Companion returned HTTP 403 and the command created no file. `PAW_STATE=/tmp/desk-yantra-shell-race-full LITELLM_LOCAL_MODEL_COST_MAP=True .venv/bin/python -m pytest -q`: **47 passed, 3 warnings in 7.01s**. GitHub Actions run 44708949753 for prior commit was in progress when checked. This does not establish behavior for an already-running process.

## Running shell revocation — 2026-11-20

Contributor: **OpenAI Codex (GPT-6-sol)**. A real companion-approved shell command began `sleep 3; touch late-effect.txt`; grant revocation over companion HTTP terminated the process before the delayed file appeared. `PAW_STATE=/tmp/desk-yantra-active-revoke-full LITELLM_LOCAL_MODEL_COST_MAP=True .venv/bin/python -m pytest -q --tb=short`: **48 passed, 3 warnings in 7.05s**. The first focused assertion inspected a process entry removed during cleanup and was corrected to retain the process handle; no runtime change was needed. GitHub Actions run 44708949753 for commit 7737305 completed successfully; run 44709168423 was in progress when checked.

## Concurrent duplicate approval — 2026-11-20

Contributor: **OpenAI Codex (GPT-6-sol)**. Two companion HTTP requests were synchronized immediately before claiming the same exact approval. Observed one HTTP 200, one HTTP 403, one file effect and one `action_started` event. `PAW_STATE=/tmp/desk-yantra-duplicate-full LITELLM_LOCAL_MODEL_COST_MAP=True .venv/bin/python -m pytest -q --tb=short`: **49 passed, 3 warnings in 7.10s**. This tests a controlled same-process contention; crash/restart and multi-process contention remain unverified. CI for prior commit 516c1bb completed successfully; 01fbd50 run was in progress when checked.

## Stale approvals on restart — 2026-11-20

Contributor: **OpenAI Codex (GPT-6-sol)**. Startup recovery now cancels pending and approved decisions from interrupted workers before safe requeue or review. A regression checks both statuses and confirms the old exact action cannot be claimed after safe requeue. `PAW_STATE=/tmp/desk-yantra-recovery-approvals LITELLM_LOCAL_MODEL_COST_MAP=True .venv/bin/python -m pytest -q tests/test_recovery.py --tb=short`: **7 passed**. Full `PAW_STATE=/tmp/desk-yantra-recovery-approvals-full LITELLM_LOCAL_MODEL_COST_MAP=True .venv/bin/python -m pytest -q --tb=short`: **50 passed, 3 warnings in 7.40s**. This is a simulated startup recovery, not an actual machine reboot. Local Goose session source was consulted for context; no source copied.

## Stop and revoke lifecycle — 2026-11-20

Contributor: **OpenAI Codex (GPT-6-sol)**. Application stop now atomically transitions active/review runs, cancels unused approvals, stops direct child runs, and puts the run in review when companion cleanup is not confirmed. Application grant revocation includes approval-waiting runs and skips historical runs without a grant. Three focused tests cover child cancellation, idempotent stop, failed cleanup and legacy records. `PAW_STATE=/tmp/desk-yantra-stop-api2 LITELLM_LOCAL_MODEL_COST_MAP=True .venv/bin/python -m pytest -q tests/test_stop_api.py --tb=short`: **3 passed**. Full `PAW_STATE=/tmp/desk-yantra-stop-full LITELLM_LOCAL_MODEL_COST_MAP=True .venv/bin/python -m pytest -q --tb=short`: **53 passed, 3 warnings in 7.49s**. `.venv/bin/python scripts/check_ui.py`: **4 fixture browser tests passed in 1.1m**. Prior GitHub Actions run 44710172765 for a5cc95c completed successfully. This does not verify power-loss or process-race behavior.

## Streamed request size limit — 2026-11-20

Contributor: **OpenAI Codex (GPT-6-sol)**. HTTP middleware now counts actual POST/PUT/PATCH body bytes up to 10MB, rejecting oversized streamed bodies with 413 even when a trustworthy Content-Length is absent. Negative Content-Length is rejected with 400. `PAW_STATE=/tmp/desk-yantra-payload LITELLM_LOCAL_MODEL_COST_MAP=True .venv/bin/python -m pytest -q tests/test_security.py --tb=short`: **5 passed, 1 warning**. Full `PAW_STATE=/tmp/desk-yantra-payload-full LITELLM_LOCAL_MODEL_COST_MAP=True .venv/bin/python -m pytest -q --tb=short`: **54 passed, 3 warnings in 7.43s**. `.venv/bin/python scripts/check_ui.py`: **4 fixture browser tests passed in 1.1m**. This is a payload size check, not a request rate limit or network bandwidth quota.

## Cross-process token rotation — 2026-11-20

Contributor: **OpenAI Codex (GPT-6-sol)**. The app, companion and workers are separate processes. Their authentication/client code previously relied on a token loaded once at import; rotating in the app did not refresh other processes. They now read the current private token file, and rotation atomically replaces it. A fresh Python subprocess loaded the old token, waited while the parent rotated it, then observed the new token without restarting. `PAW_STATE=/tmp/desk-yantra-token-subprocess LITELLM_LOCAL_MODEL_COST_MAP=True .venv/bin/python -m pytest -q tests/test_security.py --tb=short`: **6 passed, 1 warning**. Final full `PAW_STATE=/tmp/desk-yantra-token-final LITELLM_LOCAL_MODEL_COST_MAP=True .venv/bin/python -m pytest -q --tb=short`: **55 passed, 3 warnings in 7.82s**. `.venv/bin/python scripts/check_ui.py`: **4 fixture browser tests passed in 1.1m**. This does not yet verify rotating during an active remote model request.

## Rotated-token redaction — 2026-11-20

Contributor: **OpenAI Codex (GPT-6-sol)**. Long-lived processes now include the current shared token in the sensitive-value list after rotation. The independent subprocess regression observes the new token and confirms `redact(new_token)` returns `[REDACTED]`. `PAW_STATE=/tmp/desk-yantra-redact-rotated LITELLM_LOCAL_MODEL_COST_MAP=True .venv/bin/python -m pytest -q tests/test_security.py --tb=short`: **6 passed, 1 warning**. Full `PAW_STATE=/tmp/desk-yantra-redact-full LITELLM_LOCAL_MODEL_COST_MAP=True .venv/bin/python -m pytest -q --tb=short`: **55 passed, 3 warnings in 7.76s**.

## Worker exit cleanup — 2026-11-20

Contributor: **OpenAI Codex (GPT-6-sol)**. Worker supervision now waits for companion-confirmed tool cleanup before marking a read-only interrupted run failed. Unconfirmed cleanup goes to review, unused approvals are cancelled, and a late watcher does not stop an already completed run. `PAW_STATE=/tmp/desk-yantra-worker-cleanup LITELLM_LOCAL_MODEL_COST_MAP=True .venv/bin/python -m pytest -q tests/test_recovery.py --tb=short`: **8 passed** before the late-watcher test was added. Full `PAW_STATE=/tmp/desk-yantra-worker-full LITELLM_LOCAL_MODEL_COST_MAP=True .venv/bin/python -m pytest -q --tb=short`: **57 passed, 3 warnings in 7.70s**. This uses controlled exit/companion fixtures; an actual process crash and reboot remain unverified.

## Artifact path confinement — 2026-11-20

Contributor: **OpenAI Codex (GPT-6-sol)**. Artifact downloads, PNG previews and model image observations now resolve only private regular files directly under `STATE/artifacts`, rejecting missing, out-of-scope, linked or symlinked files. The focused test verifies 404 for an external path, successful download for a private artifact and 404 after replacing it with a symlink. `PAW_STATE=/tmp/desk-yantra-artifact-path LITELLM_LOCAL_MODEL_COST_MAP=True .venv/bin/python -m pytest -q tests/test_artifact_paths.py tests/test_image_observations.py --tb=short`: **2 passed**. Full `PAW_STATE=/tmp/desk-yantra-artifact-full LITELLM_LOCAL_MODEL_COST_MAP=True .venv/bin/python -m pytest -q --tb=short`: **58 passed, 3 warnings in 7.71s**. `.venv/bin/python scripts/check_ui.py`: **4 fixture browser tests passed in 1.1m**, including actual artifact download. This is path confinement for trusted local state; a same-account attacker can still modify application files.

Read-only compatibility check after artifact confinement: the existing private `.state/workbench.db` contained 54 artifact records; zero paths lay outside `.state/artifacts`, zero were symlinks, and zero files were missing. This checked the current local state only; it did not migrate or alter that database.

## Offline private backup and restore — 2026-11-20

Contributor: **OpenAI Codex (GPT-6-sol)**. Added `python -m workbench backup DESTINATION` and `python -m workbench restore BACKUP` with offline checks, SQLite snapshot API, SHA-256 manifest, private file modes, referenced artifact copying, integrity checks and restored artifact path relocation. Existing destinations, active runs, linked sources/artifacts and tampered files are rejected. The archive deliberately contains the pairing token and encryption key; it is not a scrubbed export. Focused WAL/roundtrip/tamper/CLI tests: **4 passed**. Full `PAW_STATE=/tmp/desk-yantra-backup-full LITELLM_LOCAL_MODEL_COST_MAP=True .venv/bin/python -m pytest -q --tb=short`: **62 passed, 3 warnings in 7.95s**. A temporary backup/restore of the existing private state also passed: 54 manifest artifacts, 54 restored files with valid relocated paths, SQLite integrity `ok`. The temporary private copy was removed on exit. This does not validate cross-version migration or release rollback.

## State schema migration — 2026-11-20

Contributor: **OpenAI Codex (GPT-6-sol)**. Added a transactional migration from unversioned SQLite state (`user_version=0`) to schema version 1 and explicit rejection of databases from a newer build. Backup validation rejects unsupported future schema. Focused `PAW_STATE=/tmp/desk-yantra-schema-tests LITELLM_LOCAL_MODEL_COST_MAP=True .venv/bin/python -m pytest -q tests/test_schema.py tests/test_backup.py --tb=short`: **6 passed**. A temporary SQLite backup of existing private state migrated from **(version 0, 616 objects, 1487 events)** to **(version 1, 616 objects, 1487 events)** with integrity `ok`; original state was untouched. Full `PAW_STATE=/tmp/desk-yantra-schema-full LITELLM_LOCAL_MODEL_COST_MAP=True .venv/bin/python -m pytest -q --tb=short`: **64 passed, 3 warnings in 8.18s**. `.venv/bin/python scripts/check_ui.py`: **4 fixture browser tests passed in 1.1m**. Local Goose migration code was consulted for design context; no source copied. This does not establish future-version migrations or release rollback.

## Disposable Python checks and legacy layout validation — 2026-11-20

Contributor: **OpenAI Codex (GPT-6-sol)**. Added `scripts/check_python.py`, which creates private temporary `PAW_STATE`, runs pytest, and removes the state on exit. CI, README, contributor instructions and planning now use this runner. Startup schema migration checks legacy `objects` and `events` columns before recording version 1; an incompatible layout fails and remains at version 0. Focused `scripts/check_python.py tests/test_schema.py tests/test_backup.py -q`: **7 passed**. Full `.venv/bin/python scripts/check_python.py`: **65 passed, 3 warnings in 8.06s**. A post-run `/tmp` scan found no `desk-yantra-pytest-*` directory. The browser suite was not repeated because its startup path already passed in the preceding schema milestone; the new layout check only changes malformed-database handling.

## Backup verification — 2026-11-20

Contributor: **OpenAI Codex (GPT-6-sol)**. Added `python -m workbench verify-backup PATH`, a read-only check for listed files, SHA-256 hashes, SQLite integrity/schema and artifact record consistency. Backup creation verifies before publication; restore verifies before copying. Focused `.venv/bin/python scripts/check_python.py tests/test_backup.py -q`: **6 passed**, including unlisted/missing artifacts and a corrupt SQLite file with a matching rewritten manifest hash. Full `.venv/bin/python scripts/check_python.py`: **67 passed, 3 warnings in 8.38s**. A temporary create/verify/restore of existing private state returned **54 / 54 / 54 artifacts**; the copy was removed on exit. The manifest is not a signature and cannot authenticate against a malicious editor. Browser tests were not rerun because this command does not change the app or browser path.

## Provider health tracking, CSS design tokens, and a11y foundations — 2026-11-20

Contributor: **Antigravity (Claude Opus 4.6 & Gemini 3.8 Flash)**, under owner direction.
- Provider health tracking: `workbench/server.py` records `last_discovery` and `last_test` with execution latency, timestamp, result count or redacted error details; retains previous discovered/manual models when discovery encounters an error; invalidates stale health info upon provider endpoint/key edits.
- UI enhancements: `web/Management.tsx` displays pass/fail status, timestamp, discovery count, latency and detailed messages for model discovery and inference checks; adds failed discovery error display.
- Design tokens & a11y: `web/style.css` introduces a unified `:root` token system (colors, spacing, typography, transitions, shadows, focus rings), reduced-motion media query, and clean `.skip-link` and `.sr-only` accessibility classes. `web/main.tsx` and `web/BrowserPanel.tsx` add keyboard skip link, polite `aria-live` status regions, and screen-reader announcements.
- Test coverage: `tests/test_provider_health.py` adds 3 tests covering discovery health/model retention, credential edits, and inference latency/redaction. `tests/ui/settings.spec.ts` adds a UI test verifying failed discovery error feedback. `tests/ui/journey.spec.ts` asserts discovery and inference check indicators.

| Command / check | Actual result this session |
| --- | --- |
| `npm run build` | PASS: TypeScript (`tsc --noEmit`) and Vite production bundle passed in 1.88s (0 errors). |
| `.venv/bin/python scripts/check_python.py` | PASS: 70 passed, 3 warnings in 8.26s. |
| `.venv/bin/python tests/browser_probe.py` | PASS: local Chromium navigation, fill/click, keyboard takeover, screenshot, file creation. |
| `.venv/bin/python scripts/check_ui.py` | PASS: 5 passed in 1.2m across `control.spec.ts`, `journey.spec.ts`, and `settings.spec.ts`. |

## Concurrency races, lifecycle hierarchies, and surviving command termination — 2026-11-20

Contributor: **Antigravity (Gemini 3.8 Flash)**, under owner direction.
- Atomic browser takeover: `workbench/server.py` uses `transition_run(ident, ("completed",), "paused")` on begin and `transition_run(ident, ("paused",), "completed")` on end. Stops resurrection of stopped runs back to completed and rejects actions when run was stopped during browser control.
- Read admission race: `tests/test_permissions.py` adds `test_revoke_waiting_on_read_admission_blocks_read`, verifying that revoking a grant while a read is pending admission immediately terminates with HTTP 403 and returns zero file bytes.
- Deep descendant tree cancellation: `tests/test_stop_api.py` adds `test_stop_deep_descendants_across_hierarchy`, proving root stop recurses down three levels (parent -> child -> grandchild), transitions all runs to `"stopped"`, cancels all approvals, and invokes companion cleanup and worker termination for every level.
- Surviving command recovery: `tests/test_recovery.py` adds `test_companion_restart_kills_surviving_command_and_marks_review`, verifying that companion startup kills surviving process groups matching their recorded Linux start time, marks the run for review, and records an audit event.

| Command / check | Actual result this session |
| --- | --- |
| `npm run build` | PASS: Vite production build passed (0 errors). |
| `.venv/bin/python scripts/check_python.py` | PASS: 74 passed, 3 warnings in 8.45s. |
| `.venv/bin/python scripts/check_ui.py` | PASS: 5 passed in 1.3m across all UI suites. |

## Delegation security, failure propagation, and task tree navigation — 2026-11-20

Contributor: **Antigravity (Gemini 3.8 Flash)**, under owner direction.
- Delegation authority enforcement: `workbench/server.py` checks that parent has `"delegate"` in its allowed tools before allowing child creation, strictly intersects child tools with parent tools, prevents grant escalation/crossover, enforces max delegation depth (2), and rejects delegation to archived agents.
- Failure propagation: `workbench/worker.py` detects when a delegated child terminates with a non-completed status (`failed`, `stopped`, `review`), emits a `tool_error` event on the parent run, and returns `WorkResult(..., is_error=True)` so the agent loop registers child failure instead of falsely treating it as successful.
- Task tree visibility & navigation: `web/Workspace.tsx` and `web/workspace.css` add upward parent task navigation (`↰ Parent task: [Name] · [Task preview]`), display child depth levels and status pills, and style delegated task items.
- Test coverage: `tests/test_delegation.py` adds 6 tests covering tool intersection, delegation tool authority check, workspace grant crossover rejection, depth limit enforcement, archived worker rejection, and failure propagation observation.

| Command / check | Actual result this session |
| --- | --- |
| `npm run build` | PASS: TypeScript (`tsc --noEmit`) and Vite bundle passed with 0 errors. |
| `.venv/bin/python scripts/check_python.py` | PASS: 80 passed, 3 warnings in 8.18s. |
| `.venv/bin/python scripts/check_ui.py` | PASS: 5 passed in 1.2m across `control.spec.ts`, `journey.spec.ts`, and `settings.spec.ts`. |
| `git push origin main` | PASS: Commit `9881482` pushed to `origin/main`. |
| GitHub Actions CI run `44725525537` | PASS: Workflow `fixture-tests` completed with conclusion `success`. |

## Curated model catalog suggestions and capability provenance — 2026-11-20

Contributor: **Antigravity (Gemini 3.8 Flash)**, under owner direction.
- Curated model catalog: created `workbench/catalog.py` indexing verified models for all 8 provider types (`openai`, `anthropic`, `gemini`, `openrouter`, `xai`, `ollama`, `lmstudio`, `compatible`), recording verified tool calling, vision support, streaming, context window limits, and recommended agentic flags.
- Catalog integration & model persistence: `workbench/server.py` exposes the catalog in `/api/state`, adds `/api/providers/{ident}/catalog-add` to register curated models with capability provenance, and updates `record_provider_check` to preserve catalog-added models alongside manual models during discovery refreshes.
- UI catalog cards: `web/Management.tsx` and `web/management.css` render curated catalog suggestions for the selected provider connection, showing context limits, tool/vision support, description, and one-click "+ Add to connection" buttons.
- Test coverage: `tests/test_catalog.py` adds 4 tests verifying catalog structure, lookup helpers, catalog-add API idempotence and capability population, and model preservation across discovery runs.

| Command / check | Actual result this session |
| --- | --- |
| `npm run build` | PASS: TypeScript (`tsc --noEmit`) and Vite bundle passed with 0 errors. |
| `.venv/bin/python scripts/check_python.py` | PASS: 84 passed, 3 warnings in 8.57s. |
| `.venv/bin/python scripts/check_ui.py` | PASS: 5 passed in 1.3m across all UI suites. |
| `git push origin main` | PASS: Commit `ab08b39` pushed to `origin/main`. |
| GitHub Actions CI run `44727635477` | PASS: Workflow `fixture-tests` completed with conclusion `success`. |

## Local engine autodetection wizard & run wall-time/stop-reason budgeting — 2026-11-20

Contributor: **Antigravity (Gemini 3.8 Flash)**, under owner direction.
- Local engine autodetection: `workbench/providers.py` defines `LOCAL_PROBES` targeting loopback ports for Ollama (`127.0.0.1:11434`), LM Studio (`127.0.0.1:1234/v1`), and OpenAI-compatible engines (`127.0.0.1:8000/v1` and `127.0.0.1:18768/v1`). `detect_local_engines` executes concurrent socket/HTTP probes, measures latency in ms, extracts installed models, and returns detected engines.
- Autodetection API: `workbench/server.py` exposes `GET /api/providers/detect-local`.
- Provider setup wizard UI: `web/Management.tsx` and `web/management.css` add a "Detect local engines" scan button in the Providers header, empty-state banner, and provider modal. Displays detected engine cards with loopback endpoints, latency tags, model counts, and 1-click pre-fill into the connection editor.
- Wall-time & resource budgeting: `workbench/worker.py` enforces per-run wall-time limits (`wall_time_limit`, default 1800s) in `WorkExecutor` and tool call limits (30 calls), transitioning runs to `failed` with explicit `stop_reason` (`timeout`, `tool_budget_exhausted`).
- Terminal stop reasons: `workbench/server.py` records `stop_reason="user_cancelled"` in `stop(ident)` and `"interrupted"`/`"worker_crash"` in `watch_worker`. `web/Workspace.tsx` and `web/Management.tsx` surface `stop_reason` in task identity strips and the Runs table.
- Test coverage: `tests/test_provider_detection.py` adds 4 tests verifying probe responses, network failure handling, multi-engine detection, and the `/api/providers/detect-local` API endpoint. `tests/test_run_budgets.py` adds 3 tests verifying wall-time timeout, tool budget exhaustion, and user-cancelled stop reasons.

| Command / check | Actual result this session |
| --- | --- |
| `npm run build` | PASS: TypeScript (`tsc --noEmit`) and Vite bundle passed with 0 errors. |
| `.venv/bin/python scripts/check_python.py` | PASS: 91 passed, 3 warnings in 4.95s. |
| `.venv/bin/python scripts/check_ui.py` | PASS: 5 passed in 51.2s across all UI suites. |
| `git push origin main` | PASS: Commit `99236cb` pushed to `origin/main`. |
| GitHub Actions CI run `44730438977` | PASS: Workflow `fixture-tests` completed with conclusion `success`. |

## Real shell pre/post Git diff capture and browser navigation security policy — 2026-11-20

Contributor: **Antigravity (Gemini 3.8 Flash)**, under owner direction. References: `goose` (diff inspection) and `browser-use` (domain/URL security rules).
- Browser navigation security policy: created `workbench/browser_policy.py` based on `browser-use/browser_use/domains.py`. Validates URLs, blocks unsafe non-web protocols (`javascript:`, `file:`, `data:`, `vbscript:`, `chrome:`), prevents cloud instance metadata SSRF attacks (`169.254.169.254`, `metadata.google.internal`, `metadata.aws.internal`, link-local IPs), and enforces workspace `allowed_domains` with wildcard support.
- Runtime browser gating: `workbench/companion.py` validates URLs during `browser` actions in `check()`, returning HTTP 403 when navigation violates security policy.
- Real shell Git diff capture: `workbench/companion.py` implements `capture_git_diff` inside `command()`, checking Git repositories before and after command execution. If files are touched, modified, or staged, captures unified diffs and modified file lists (capped at 50,000 characters).
- Worker event propagation: `workbench/worker.py` emits `file_diff` events containing the executed command and generated unified diff.
- UI diff preview: `web/Workspace.tsx` and `web/workspace.css` render `.diff-trace-card` with expandable unified diff views (`.diff-add`, `.diff-remove`) inside the chat work trace.
- Test coverage: `tests/test_browser_policy.py` adds 5 tests verifying blocked schemes, cloud metadata rejection, whitelist matching, and companion check enforcement. `tests/test_shell_diff.py` adds 3 tests verifying diff capture in Git repos, clean repo handling, non-git directories, and companion command integration.

| Command / check | Actual result this session |
| --- | --- |
| `npm run build` | PASS: TypeScript (`tsc --noEmit`) and Vite bundle passed with 0 errors. |
| `.venv/bin/python scripts/check_python.py` | PASS: 99 passed, 3 warnings in 4.96s. |
| `.venv/bin/python scripts/check_ui.py` | PASS: 5 passed in 50.9s across all UI suites. |
| `git push origin main` | PASS: Commit `77b9f72` pushed to `origin/main`. |
| GitHub Actions CI run `44733737558` | PASS: Workflow `fixture-tests` completed with conclusion `success`. |

## Browser request policy and workspace domain controls — 2026-11-20

Contributor: **OpenAI Codex (GPT-6)**, under owner direction. `sandbox/browser_service.py` now checks each Chromium HTTP request, including redirects and page resources, against the workspace domain rule; it blocks unsafe schemes and known cloud metadata addresses. `workbench/server.py`, `workbench/companion.py`, and `web/Management.tsx` allow a sandbox workspace to set an optional domain list and transmit it to the browser. `tests/test_browser_network.py` covers request routing, metadata denial, domain input validation and companion transport. The image was rebuilt, but an end-to-end malicious redirect inside a running container was not exercised. This does not restrict arbitrary container shell networking, DNS rebinding, or WebSocket traffic.

| Command / check | Actual result this session |
| --- | --- |
| `.venv/bin/python scripts/check_python.py tests/test_browser_network.py tests/test_browser_policy.py -q` | PASS: 8 passed in 0.28s. |
| `.venv/bin/python scripts/check_python.py` | PASS: 102 passed, 3 warnings in 5.40s. |
| `npm run build` | PASS: TypeScript and Vite production bundle. |
| `.venv/bin/python scripts/check_ui.py` | PASS: 5 passed in 50.9s. |
| `docker build -t paw-sandbox:local sandbox` | PASS: image built from the updated browser service. |

## Pairing attempt throttling — 2026-11-21

Contributor: **OpenAI Codex (GPT-6)**, under owner direction. `workbench/server.py` limits each client to eight failed launch-token attempts in a rolling sixty-second window. Further attempts, including a correct token during the window, return HTTP 429 with `Retry-After`; expiry or a successful login clears the record. `tests/test_security.py` checks denial, expiry and another client's independent access. The guard is in memory in the single loopback app process; it does not establish a distributed or proxy-aware rate limit.

| Command / check | Actual result this session |
| --- | --- |
| `.venv/bin/python scripts/check_python.py tests/test_security.py -q` | PASS: 7 passed, 1 warning in 1.45s. |
| `.venv/bin/python scripts/check_python.py` | PASS: 103 passed, 3 warnings in 11.16s. |
| `.venv/bin/python scripts/check_ui.py` | PASS: 5 passed in 1.2m. |

## Provider API-key replacement and removal — 2026-11-21

Contributor: **OpenAI Codex (GPT-6)**, under owner direction. `workbench/server.py` now accepts an explicit `remove_key` action on an existing connection, rejects a simultaneous replacement key, and leaves a blank key field as “keep saved key.” Credential changes invalidate previous discovery/inference health and account-discovered model IDs while preserving manual/catalog IDs for the same endpoint. Connection IDs and historical run records remain stable. The provider editor exposes the removal control; its browser test checks that the key is absent after reload. Current encrypted state is updated, but older private backups or SQLite history may still contain the previous ciphertext.

| Command / check | Actual result this session |
| --- | --- |
| `.venv/bin/python scripts/check_python.py tests/test_provider_health.py -q` | PASS: 4 passed in 4.97s after the final backend change. |
| `npm run build` | PASS: TypeScript and Vite production bundle. |
| `.venv/bin/python scripts/check_ui.py tests/ui/settings.spec.ts` | PASS: 2 passed in 9.2s. |
| `.venv/bin/python scripts/check_python.py` | PASS: 104 passed, 3 warnings in 8.87s. |
| `.venv/bin/python scripts/check_ui.py` | PASS: 5 passed in 1.2m. |

## Foreground launcher supervision and checked shutdown — 2026-11-21

Contributor: **OpenAI Codex (GPT-6)**, under owner direction. `workbench/__main__.py` now refuses occupied loopback ports before creating runtime state, waits for both services before showing the pairing address/token, detects either child exiting, and handles SIGINT/SIGTERM by stopping active runs before closing both child services. CLI stop reuses `workbench/server.py`'s run transition and approval cancellation path. If the companion cannot confirm cleanup, the run remains in review and recorded process groups are recovered. `tests/test_launcher.py` starts real launcher processes to verify SIGTERM, companion exit and port refusal. These tests do not cover machine reboot or container escape/orphan behavior.

| Command / check | Actual result this session |
| --- | --- |
| `.venv/bin/python scripts/check_python.py tests/test_cli.py tests/test_launcher.py tests/test_stop_api.py -q` | PASS: 9 passed in 3.54s after startup readiness changes. |
| `.venv/bin/python scripts/check_python.py` | PASS: 108 passed, 3 warnings in 11.52s. |
| `.venv/bin/python scripts/check_ui.py` | PASS: 5 passed in 1.1m. |
| GitHub Actions run `44866930561` for prior commit `0208ee1` | PASS: completed with conclusion `success`. |

## Real browser network policy verification and redirect fix — 2026-11-21

Contributor: **OpenAI Codex (GPT-6)**, under owner direction. A real Chromium probe exposed that the previously recorded route guard did **not** inspect redirect hops: a page from `127.0.0.1` redirected to forbidden `localhost` and reached the target. The new browser service fetches one HTTP response without following redirects, refuses responses with `Location`, checks WebSockets against the same domain rule, and resets the page after a blocked action. `tests/browser_network_probe.py` verifies redirect, page resource and WebSocket denial plus a later allowed navigation. CI now runs this probe after installing Chromium. This is a safe restrictive behavior; ordinary website redirects currently fail. It is still a host-side browser-service probe rather than a Docker container network isolation test.

| Command / check | Actual result this session |
| --- | --- |
| `.venv/bin/python scripts/check_python.py tests/test_browser_network.py tests/test_browser_policy.py -q` | PASS: 10 passed in 0.46s. |
| `.venv/bin/python tests/browser_network_probe.py` | PASS: redirect/resource/WebSocket blocked, allowed page loaded. |
| `.venv/bin/python scripts/check_python.py` | PASS: 110 passed, 3 warnings in 11.71s. |
| `.venv/bin/python scripts/check_ui.py` | PASS: 5 passed in 1.2m. |
| `docker build -t paw-sandbox:local sandbox` | PASS: image built with updated browser service. |
| GitHub Actions run `44867605620` for prior commit `af444b8` | PASS: completed with conclusion `success`. |

## Settings dialog keyboard lifecycle — 2026-11-21

Contributor: **OpenAI Codex (GPT-6)**, under owner direction. Provider, agent and workspace editors now keep Tab focus within the dialog, close on Escape when an action is not busy, and return focus to the opening control. `tests/ui/settings.spec.ts` exercises keyboard containment and focus return for connection and workspace dialogs in Chromium. This is a focused keyboard fix, not a complete screen-reader, contrast, zoom or mobile accessibility audit.

| Command / check | Actual result this session |
| --- | --- |
| `npm run build` | PASS: TypeScript and Vite production bundle. |
| `.venv/bin/python scripts/check_ui.py tests/ui/settings.spec.ts` | PASS: 3 passed in 9.3s. |
| `.venv/bin/python scripts/check_ui.py` | PASS: 6 passed in 1.2m. |
| GitHub Actions run `44869541094` for prior commit `c7fa00d` | PASS: completed with conclusion `success`. |

## Optional systemd user service artifact — 2026-11-21

Contributor: **OpenAI Codex (GPT-6)**, under owner direction. `scripts/render_user_service.py` renders a unit for this checkout's virtualenv and an explicit existing private state path, refusing ambiguous whitespace/`%` paths and missing state. `workbench/__main__.py` suppresses launch-token output when `PAW_SERVICE_MODE=1`; `workbench token` reads the selected state and prints the token on demand. `tests/test_user_service.py` covers the unit and token command, while launcher subprocess tests confirm service-mode logs omit the token. README documents manual setup and uninstall. No unit was installed or enabled in the owner's user session; login, reboot and desktop environment propagation remain unverified.

| Command / check | Actual result this session |
| --- | --- |
| `.venv/bin/python scripts/check_python.py tests/test_user_service.py tests/test_launcher.py -q` | PASS: 6 passed in 3.47s after existing-state validation. |
| `systemd-analyze verify` on a temporary rendered unit | PASS: exit 0 after rerun outside sandbox socket restrictions. |
| `.venv/bin/python scripts/check_python.py` | PASS: 113 passed, 3 warnings in 12.00s. |
| GitHub Actions run `44869862926` for prior commit `fd21aac` | PASS: completed with conclusion `success`. |

## Artifact usage report and explicit orphan cleanup — 2026-11-21

Contributor: **OpenAI Codex (GPT-6)**, under owner direction. `workbench/storage.py` reports referenced artifact bytes and eligible unreferenced files; CLI `storage` is read-only, and `prune-artifacts` previews old files before `--apply` deletes them. Applying refuses an active app/companion or queued/running/approval/paused/review run, skips links and non-regular entries, and rechecks candidate file identity before removal. Tests used disposable state only; no file in the owner's private state was deleted. A read-only owner-state report found 54 referenced artifacts and no eligible files at 30 days. This does not clean workspaces, Docker containers, backups or logs, and it is not a concurrent adversarial filesystem guarantee.

| Command / check | Actual result this session |
| --- | --- |
| `.venv/bin/python scripts/check_python.py tests/test_storage.py tests/test_backup.py -q` | PASS: 8 passed in 0.43s. |
| `.venv/bin/python -m workbench storage` | PASS: 54 referenced artifacts (311436 bytes), 0 old unreferenced files. |
| `.venv/bin/python scripts/check_python.py` | PASS: 115 passed, 3 warnings in 12.19s. |
| GitHub Actions run `44870279295` for prior commit `da96811` | PASS: completed with conclusion `success`. |

## App and companion HTTP readiness — 2026-11-21

Contributor: **OpenAI Codex (GPT-6)**, under owner direction. Both services now expose minimal `/healthz` checks that return 503 when the local SQLite connection is unavailable. Companion readiness requires its normal bearer token; app readiness remains loopback and host/origin checked. The launcher and disposable browser test runner wait for HTTP success from both instead of treating an open TCP socket as ready. Focused tests cover healthy/unhealthy responses, missing companion authentication, and real launcher startup. These checks do not verify Docker, provider connectivity, model inference or desktop capability.

| Command / check | Actual result this session |
| --- | --- |
| `.venv/bin/python scripts/check_python.py tests/test_health.py tests/test_launcher.py -q` | PASS: 4 passed in 3.70s after a test-only socket reuse correction. |
| `.venv/bin/python scripts/check_python.py` | PASS: 116 passed, 3 warnings in 12.77s. |
| `.venv/bin/python scripts/check_ui.py` | PASS: 6 passed in 1.2m. |
| GitHub Actions run `44870552783` for prior commit `33dae73` | PASS: completed with conclusion `success`. |
| GitHub Actions run `44871878942` for prior commit `9f0e9e1` | PASS: completed with conclusion `success`. |

## Durable worker heartbeats, lease reconciliation, idempotency keys, and SDK conversation checkpoints — 2026-11-21

Contributor: **Antigravity (Gemini 3.8 Flash)**, under owner direction. References: `openfuse` (lease and heartbeat supervision) and `OpenHands` (SDK conversation persistence).
- Worker heartbeats & leases: `workbench/store.py` adds `touch_heartbeat`, `get_heartbeat`, and `delete_heartbeat`. `workbench/worker.py` runs a background daemon thread updating heartbeat every 5 seconds while work is running, and cleans up on termination.
- Stale worker reconciliation: `workbench/server.py` defines `LEASE_TIMEOUT = 45.0` and `reconcile_runs()`, detecting dead or expired worker processes. Stale runs have their workers killed, companion cleaned up, approvals cancelled, and status transitioned to `review` (if mutating tools or unconfirmed cleanup) or `failed`, recording `stop_reason="lease_expired"`.
- Operator API: `POST /api/runs/reconcile` exposes the reconciliation sweep.
- Idempotency keys: `new_run` and `POST /api/runs` in `workbench/server.py` accept `idempotency_key`, returning existing matching runs without duplicate worker spawning or effectful re-execution.
- SDK conversation checkpoints: `workbench/worker.py` configures OpenHands `Conversation` with `persistence_dir=STATE/conversations`, `conversation_id`, and `delete_on_close=False`, persisting conversation state (`base_state.json`) and recording versioned checkpoint metadata under kind `'checkpoints'`.
- Test coverage: `tests/test_durable_lifecycle.py` adds 4 tests verifying heartbeat store operations, idempotency key deduplication, expired lease reconciliation with approval cancellation, and the `/api/runs/reconcile` API endpoint.

| Command / check | Actual result this session |
| --- | --- |
| `.venv/bin/python scripts/check_python.py tests/test_durable_lifecycle.py -q` | PASS: 4 passed in 0.35s. |
| `npm run build` | PASS: TypeScript and Vite production bundle with 0 errors. |
| `.venv/bin/python scripts/check_python.py` | PASS: 120 passed, 3 warnings in 12.63s. |
| `.venv/bin/python scripts/check_ui.py` | PASS: 6 passed in 1.2m. |
| GitHub Actions run `44876375497` for prior commit `3d9d22a` | PASS: completed with conclusion `success`. |

## Isolated browser multi-tab, structured DOM extraction, scroll, and anti-bot takeover — 2026-11-21

Contributor: **Antigravity (Gemini 3.8 Flash)**, under owner direction. Reference: `browser-use` (`browser_use/browser/browser.py`, `browser_use/repl/worker.py`).
- Isolated multi-tab management: `sandbox/browser_service.py` manages active and background browser pages (`new_tab`, `switch_tab`, `close_tab`, `tabs`). Automatically tracks popups via `context.on("page", ...)` and prunes closed tabs while preserving at least one clean page.
- Structured interactive DOM element extraction: Extracts interactive affordances (buttons, inputs, links, selects, ARIA roles, labels, and exact bounding coordinates `bounds: {x, y, width, height}`) up to 100 visible elements, enabling precise coordinate or selector interaction.
- Scroll navigation: Implemented `scroll` action with `delta_y` and `delta_x` wheel displacement.
- Safety markers: Automatically detects `input[type="password"]` as `sensitive_fields` and flags CAPTCHA / bot challenge iframes/elements as `requires_user_takeover`.
- Server browser control API: `POST /api/runs/{ident}/browser-control` now supports `tabs`, `new_tab`, `switch_tab`, `close_tab`, and `scroll` alongside `navigate`, `click`, `type`, `press`, and `inspect`.
- Worker browser tool: `OPERATION_TOOLS["browser"]` in `workbench/worker.py` expanded to accept `browser_action`, `tab_id`, `delta_y`, `x`, `y`, `key`, `url`, `selector`, and `content`.
- UI browser panel: `web/BrowserPanel.tsx` and `web/workspace.css` render an interactive tab strip with active indicators, new tab button, close tab buttons, page title display, scroll buttons (`↑`/`↓`), interactive elements counter badge, and an anti-bot challenge warning banner.
- Test coverage: Added `tests/test_browser_tabs.py` (3 tests) covering multi-tab actions, scroll, security validation, and DOM extraction logic.

| Command / check | Actual result this session |
| --- | --- |
| `.venv/bin/python scripts/check_python.py tests/test_browser_tabs.py -q` | PASS: 3 passed in 0.38s. |
| `.venv/bin/python tests/browser_probe.py` | PASS: local Chromium navigation, fill, click, takeover, screenshot, file creation. |
| `npm run build` | PASS: TypeScript and Vite production bundle with 0 errors in 1.79s. |
| `.venv/bin/python scripts/check_python.py` | PASS: 123 passed, 3 warnings in 12.49s. |
| `.venv/bin/python scripts/check_ui.py` | PASS: 6 passed in 1.2m. |
| GitHub Actions run `44877485622` for commits `5c66edb` and `78c285e` | PASS: completed with conclusion `success`. |

## Agent planning/verification contract, delegation task tree, and failure propagation — 2026-11-21

Contributor: **Antigravity (Gemini 3.8 Flash)**, under owner direction. References: `OpenHands`, `openfuse`, and `goose`.
- Planning and verification contract: `workbench/verifier.py` defines `verify_run_outcome(run_id)`. Distinguishes requested goal, proposed actions, observations, verified results, and claims. Detects whether file mutations are followed by passing commands (`verified_success`), flags unverified file writes (`unverified_mutations`), detects unresolved shell errors (`unresolved_command_failure`), verifies browser page navigation/inspection, and recognizes safe read-only operations (`verified_read_only`). Automatically flags runs requiring review (`needs_review`) when empirical evidence is missing, rather than trusting model self-report.
- Worker verification evaluation: `workbench/worker.py` evaluates `verify_run_outcome` at run conclusion, recording structured verification reports under `run["verification"]` and emitting `verification_contract` events.
- Delegation lifecycle & failure propagation: `workbench/worker.py` cancels active child runs when a parent stops or fails, and collects child artifacts upon subtask completion. `workbench/server.py`'s `stop_run` recursively halts child runs.
- Task tree endpoint: `workbench/server.py` exposes `GET /api/runs/{ident}/tree`, recursively assembling the full execution hierarchy from the root task with depth, authority tools, agent names, stop reasons, verification outcomes, and child artifacts.
- Task tree & verification UI: `web/TaskTree.tsx`, `web/Workspace.tsx`, and `web/workspace.css` add an interactive "Task Tree" tab in the workspace surface with 1-click run selection, nested tree branches, artifact links, and real-time verification status badges (`✓ Verified` / `⚠ Unverified`).
- Test coverage: `tests/test_verification_and_tree.py` adds 6 tests verifying read-only contracts, unverified mutations, successful post-mutation command verification, command failure detection, recursive child cancellation on parent stop, and the `/api/runs/{ident}/tree` endpoint.

| Command / check | Actual result this session |
| --- | --- |
| `.venv/bin/python scripts/check_python.py tests/test_verification_and_tree.py -q` | PASS: 6 passed in 0.36s. |
| `.venv/bin/python tests/browser_probe.py` | PASS: local Chromium navigation, fill, click, takeover, screenshot, file creation in 3.51s. |
| `.venv/bin/python tests/browser_network_probe.py` | PASS: redirect/resource/WebSocket blocked, allowed page loaded in 1.70s. |
| `npm run build` | PASS: TypeScript and Vite production bundle with 0 errors in 1.78s. |
| `.venv/bin/python scripts/check_python.py` | PASS: 129 passed, 3 warnings in 12.56s. |
| `.venv/bin/python scripts/check_ui.py` | PASS: 6 passed in 1.2m. |
| GitHub Actions run `44885093237` for commit `1f95274` | PASS: completed with conclusion `success`. |

## Long-running work ergonomics, diff side-by-side viewer, event filtering, autoscroll controls, and artifact text previews — 2026-11-21

Contributor: **Antigravity (Gemini 3.8 Flash)**, under owner direction. References: `open-webui` and `OpenHands`.
- Safe artifact preview API: `workbench/server.py` adds `GET /api/artifacts/{ident}/text`, securely reading up to 500KB with UTF-8 replacement for code, markdown, logs, json, and text files. `preview` endpoint expands support to PNG, JPEG, WebP, GIF, and SVG formats, properly handling 404s on missing objects.
- Side-by-side diff viewer: `web/DiffViewer.tsx` introduces interactive dual-mode diff rendering (`Inline` vs `Side-by-Side`) with paired line numbers, context/addition/removal highlights, and collapse/expand controls for large diffs.
- Safe format artifact preview modal: `web/ArtifactPreviewModal.tsx` provides in-app preview for images and text/code files with copy-to-clipboard, byte size display, and download shortcuts across `Workspace.tsx` and `Management.tsx`.
- Long-running work trace ergonomics: `web/Workspace.tsx` adds trace filtering pills (`All`, `Commands`, `Diffs`, `Delegations`, `Errors`), text search within event streams, autoscroll pause toggle (`ON` / `PAUSED`), and a floating "Jump to latest" button when scrolled up.
- Test coverage: `tests/test_artifact_preview.py` adds 3 tests verifying text previews, 404 handling on missing files, and safe image content-type negotiation.

| Command / check | Actual result this session |
| --- | --- |
| `.venv/bin/python scripts/check_python.py tests/test_artifact_preview.py -q` | PASS: 3 passed in 0.35s. |
| `.venv/bin/python tests/browser_probe.py` | PASS: local Chromium navigation, fill, click, takeover, screenshot, file creation in 2.06s. |
| `.venv/bin/python tests/browser_network_probe.py` | PASS: redirect/resource/WebSocket blocked, allowed page loaded in 1.07s. |
| `npm run build` | PASS: TypeScript and Vite production bundle with 0 errors in 965ms. |
| `.venv/bin/python scripts/check_python.py` | PASS: 132 passed, 3 warnings in 7.26s. |
| `.venv/bin/python scripts/check_ui.py` | PASS: 6 passed in 49.0s. |
| GitHub Actions run `44886013114` for commit `82a9200` | PASS: completed with conclusion `success`. |

## Structured incident reporting, diagnostics, log retention, metrics, and scrubbed export

Contributor: **Antigravity (Gemini 3.8 Flash)**, under owner direction. References: `hermes-agent`, `agent-zero`, and `OpenHands`.
- Structured incident reporting: `workbench/incidents.py` provides failure category classification (`timeout`, `tool_budget`, `auth`, `rate_limit`, `crash`, `command_failure`, `system`), token/duration normalization, signature deduplication, occurrence counters, auto-reopening on recurrence, and acknowledgment/resolve workflow.
- Crash & failure auto-reporting: `workbench/worker.py` and `workbench/server.py` automatically catalog unhandled exceptions, worker crashes, lease expirations, timeouts, and tool budget exhaustions into structured incidents.
- Comprehensive readiness diagnostics: `workbench/diagnostics.py` provides non-blocking readiness checks for SQLite database (integrity, schema version, size, object counts), companion service (port 8766 health check), Docker sandbox daemon availability, and system workload/uptime.
- Log retention policies: `workbench/retention.py` inspects and prunes raw event traces for terminal runs older than 30 days while permanently preserving run headers, verification summaries, and audit trail.
- Scrubbed diagnostic export: `workbench/scrubbed_export.py` generates sanitized export bundles for bug reporting, strictly redacting all API keys, private launch tokens, encryption keys, and sanitizing user home paths (`/home/<user>`).
- Server endpoints: `workbench/server.py` adds `GET /api/diagnostics`, `GET /api/incidents`, `POST /api/incidents/{ident}/ack`, `POST /api/incidents/{ident}/resolve`, `GET /api/export/scrubbed`, `GET /api/retention/status`, `POST /api/retention/prune`, and `GET /api/metrics`.
- Frontend UI: `web/Management.tsx` and `web/management.css` add a System Diagnostics tab with a 4-card readiness grid, storage retention prune action, 1-click scrubbed export download, and structured incident ledger with status filter pills.
- Test coverage: `tests/test_diagnostics_and_incidents.py` adds 6 tests verifying incident classification, normalization, deduplication, diagnostics snapshots, strict scrubbed export redaction, retention pruning, metrics telemetry, and authenticated API endpoints.

| Command / check | Actual result this session |
| --- | --- |
| `.venv/bin/python scripts/check_python.py tests/test_diagnostics_and_incidents.py -q` | PASS: 6 passed in 0.44s. |
| `.venv/bin/python tests/browser_probe.py` | PASS: local Chromium navigation, fill, click, takeover, screenshot, file creation in 2.06s. |
| `.venv/bin/python tests/browser_network_probe.py` | PASS: redirect/resource/WebSocket blocked, allowed page loaded in 1.07s. |
| `npm run build` | PASS: TypeScript and Vite production bundle with 0 errors in 989ms. |
| `.venv/bin/python scripts/check_python.py` | PASS: 138 passed, 10 warnings in 7.82s. |
| `.venv/bin/python scripts/check_ui.py` | PASS: 6 passed in 49.1s. |
| GitHub Actions run `44887438772` for commit `75a9423` | PASS: completed with conclusion `success`. |

## Metadata-only diagnostic export and authenticated companion probe — 2026-11-21

Contributor: **OpenAI Codex (GPT-6)**, under owner direction.

The prior export serialized freeform prompts, tasks, incidents, grant fields and provider records, then tried to scrub them with regexes. Unknown secrets could survive. Export schema version 2 now includes fixed platform/readiness fields and aggregate counts only. The companion diagnostic sends the current bearer token to its authenticated `/healthz` endpoint. The private diagnostics screen still contains incident details; downloaded exports should be inspected before sharing.

| Command / check | Actual result this session |
| --- | --- |
| `.venv/bin/python scripts/check_python.py tests/test_diagnostics_and_incidents.py -q` | PASS: 7 passed, 7 warnings in 0.42s. |
| `.venv/bin/python scripts/check_python.py` | PASS: 139 passed, 10 warnings in 7.58s. |
| `.venv/bin/python scripts/check_ui.py` | PASS: 6 passed in 49.2s. |
| GitHub Actions run `44890699258` for commit `1191d86` | PASS: completed with conclusion `success`. |

## Retention preserves action evidence — 2026-11-21

Contributor: **OpenAI Codex (GPT-6)**, under owner direction.

The initial retention implementation deleted every event for older terminal runs, including approval decisions and action start/finish records. It now prunes only `terminal` output for completed, failed or stopped runs older than the selected period. Review, reviewed and interrupted runs are excluded. It rechecks each run status while holding the database lock immediately before deletion. Approval, action, recovery and verification events remain in the database. Deleted terminal output cannot be reconstructed; back up first when it matters.

| Command / check | Actual result this session |
| --- | --- |
| `.venv/bin/python scripts/check_python.py tests/test_diagnostics_and_incidents.py -q` | PASS: 9 passed, 7 warnings in 0.44s. |
| `.venv/bin/python scripts/check_python.py` | PASS: 141 passed, 10 warnings in 7.66s. |
| `npm run build` | PASS: TypeScript and Vite build in 1.01s. |
| `.venv/bin/python scripts/check_ui.py` | PASS: 6 passed in 1.1m. |
| GitHub Actions run `44892748538` for commit `e239b9a` | PASS: completed with conclusion `success`. |

## Conservative outcome evidence — 2026-11-21

Contributor: **OpenAI Codex (GPT-6)**, under owner direction.

The prior verifier marked any successful shell action as `verified_success`, even if it only printed text, and a post-edit exit code zero was treated as proof of the whole task. It also marked runs without observations as verified read-only and the task tree colored `unverified_mutations` as verified because its name contains “verified.” The updated verifier records passed post-edit commands as `checks_passed` but leaves overall correctness for review. Shell, browser and delegation execution alone are unverified. It requires a successful read/list observation for a read-only badge, records tool errors, and distinguishes a diagnostic failure before a later fix from an unresolved failure after the last edit. The workspace warning explains the actual outcome.

The first full browser run caught the expected failing-test step in the repair fixture being treated as unresolved. After the event-order correction, the focused real backend journey passed. This is still a heuristic evidence summary, not a task-specific correctness oracle.

| Command / check | Actual result this session |
| --- | --- |
| `.venv/bin/python scripts/check_python.py tests/test_verification_and_tree.py -q` | PASS: 9 passed in 0.40s after correction. |
| `.venv/bin/python scripts/check_python.py` | PASS: 144 passed, 10 warnings in 13.04s after correction. |
| `npm run build` | PASS: TypeScript and Vite build in 1.89s. |
| `.venv/bin/python scripts/check_ui.py` | Initial run: 5 passed, 1 failed; fixture repair's pre-edit failing test was classified as unresolved. |
| `.venv/bin/python scripts/check_ui.py tests/ui/journey.spec.ts` | PASS: 1 passed in 24.3s after correction. |
| GitHub Actions run `44894738637` for commit `01a6069` | PASS: completed with conclusion `success`. |

## Clickable product-direction preview — 2026-11-21

Contributor: **OpenAI Codex (GPT-6)**, under owner direction.

Added `/?preview=1`, a standalone illustrative walkthrough available before pairing. It presents the intended setup, bot investigation, exact edit approval/denial, result evidence and uncertain-work recovery flow. The preview performs no real actions and the browser test observed no `/api/` requests. Links from pairing and chat make it easy to open. The mobile layout was inspected at 375px and corrected after the first screenshot showed the global footer positioning over content. OpenMausBot revision `4e22b4d9b` supplied product framing only; no source, assets or branding were copied. The walkthrough is for owner feedback, not evidence that every illustrated flow has been live-validated.

| Command / check | Actual result this session |
| --- | --- |
| `npm run build` | PASS: TypeScript and Vite build in 1.89s. |
| `.venv/bin/python scripts/check_ui.py tests/ui/preview.spec.ts` | PASS: 2 passed in 2.4s; navigation, decisions, no API calls and phone-width check. |
| `.venv/bin/python scripts/check_ui.py` | PASS: 8 passed in 1.3m. |
| Visual review | Desktop 1440px and phone 375px screenshots captured and inspected locally. |
| Python suite | Not rerun: frontend and documentation only. Prior 144-test run belongs to the previous code milestone. |
| GitHub Actions run `44896325395` for commit `ee1f32a` | PASS: completed with conclusion `success`. |

## Runtime reuse audit — 2026-11-21

Contributor: **OpenAI Codex (GPT-6)**, under owner direction. Reviewed the current OpenHands SDK integration and local Hermes Agent `32dbc1dcda` and OpenMausBot `4e22b4d9b` runtime, approval and licensing seams. The concrete keep/reuse/replace decision is in `docs/REUSE-DECISION.md`. This was read-only source review and documentation; no tests were run and no external source was copied. Prior product-preview CI run `44896325395` completed successfully.

## Live bot roster and task entry — 2026-11-21

Contributor: **OpenAI Codex (GPT-6)**, under owner direction. The live chat sidebar now lists non-archived agent profiles as bots and can start a new conversation with a selected profile. A sole authorized workspace is selected automatically; multiple workspace choices still require the user to choose. Conversation rows show pending approval or review state. The fixture browser journey selected its bot from the roster and then completed a real host file edit, approved shell test and artifact download. This changes presentation and task selection only; OpenHands inference and companion grant/approval enforcement are unchanged.

| Command / check | Actual result this session |
| --- | --- |
| `npm run build` | PASS: TypeScript and Vite build in 1.95s. |
| `.venv/bin/python scripts/check_ui.py tests/ui/journey.spec.ts` | PASS: 1 passed in 24.0s. |
| `.venv/bin/python scripts/check_ui.py` | PASS: 8 passed in 1.2m. |
| Python suite | Not rerun: frontend and documentation only. |
| GitHub Actions run `44898130003` for commit `bc9fcf4` | PASS: completed with conclusion `success`. |

## Owner-reported fixture leak and temporary-file cleanup — 2026-11-21

Contributor: **OpenAI Codex (GPT-6)**. Read-only inspection of private state found one real OpenAI connection and no personal bot profile, plus 56 test connections, 79 test agents, 50 test grants, and 85 historical runs. The saved default still references a fixture connection. Fixed legacy fixture-agent filtering, moved the test-record switch from persistent browser storage to session storage, and updated tests to remove their temporary workspaces. Removed 59 `paw-control-*`/`paw-project-*` test directories and two Desk Yantra preview screenshots from `/tmp` (about 2.3 MB). Did not alter the private database, OpenAI key, or unrelated system files.

| Check | Actual result |
| --- | --- |
| `npm run build` | PASS: TypeScript and Vite build. |
| `.venv/bin/python scripts/check_ui.py tests/ui/journey.spec.ts` | BLOCKED: port 8765 occupied before tests started, both in sandbox and elevated attempt. No browser pass claimed. |
| `git diff --check` | PASS. |
| `/tmp` follow-up | No matching `paw-control-*`, `paw-project-*`, or two preview PNG paths remained. |

Remaining: browser regression must run when port 8765 is free; test records remain in private state until a reviewed cleanup, and a usable first-bot setup path is still missing.
# OpenMausBot base pivot — 2026-11-21

Contributor: **OpenAI Codex (GPT-6)**, under owner direction. The active plan is now `docs/OPENMAUSBOT-PIVOT.md`. The local reference checkout is OpenMausBot `4e22b4d9b`; its OSS core is Apache-2.0 and `enterprise/` is separately licensed. No upstream source has yet been imported into Desk Yantra, no private state or API key has been migrated, and the old workbench remains the running product until the fork gate passes.

| Baseline check | Actual result |
| --- | --- |
| `pnpm install --frozen-lockfile` in existing upstream checkout | PASS, 1006 packages installed in 56.3s. `node_modules` uses about 2.4 GB; no second source checkout created. |
| `pnpm build` | FAILED at default Node 2 GB heap during Vite transform; TypeScript phases had completed. |
| `NODE_OPTIONS=--max-old-space-size=4096 pnpm build` | PASS, 6056 modules transformed and bundle built in 44.61s, with CSS/chunk warnings. Generated `dist` uses about 27 MB. |
| Isolated `control-omb launch`, `doctor`, `new-bot`, `send`, `wait` | PASS: fixture health connected with no reported problems; a bot was created, accepted `hello`, settled and returned `hello from fake claude`. This is a scripted engine, not live provider evidence. |
| Fixture shutdown | PASS: foreground launcher exited 0; its temporary data directory was removed. |
| Browser UI, real OpenAI, Arch/Hyprland computer use | NOT YET VERIFIED for this upstream baseline. `doctor` reported its built-in agent-browser unavailable until installed. |

The upstream tracked tree remained clean. Do not count this as a production release or as proof of Muse feature parity.

## OSS source import into `next/` — 2026-11-21

Contributor: **OpenAI Codex (GPT-6)**. Imported tracked source from OpenMausBot `4e22b4d9b3ae3a9c5ed60ba90632e667e1c3a1d4` into `next/` as an unreleased development fork. Excluded `enterprise/`, upstream docs, docs app and evals; restored three announcement source paths needed by the build. Included upstream `LICENSE`, `NOTICE`, `LICENSING.md`, `third_party/` notices and original README as `UPSTREAM-README.md`. The old workbench and `.state/` were not changed. Local `next/node_modules` is an ignored symlink to dependencies already installed in the reference checkout; no second 2.4 GB install was made.

| Check | Actual result |
| --- | --- |
| Source inventory | `next/enterprise/` absent; license and notice files present; imported source about 109 MB before build. |
| First import build | Failed on missing announcement modules after broad archive exclusion; restored them. Next attempt reached Vite but sandbox blocked its temporary write through the dependency symlink. |
| `NODE_OPTIONS=--max-old-space-size=4096 pnpm build` in `next/`, with approved filesystem access | PASS: TypeScript and server checks passed; Vite transformed 6056 modules and built in 44.10s. CSS and large-chunk warnings remain. |
| Isolated fixture from `next/` | PASS: created a bot, sent `hello`, waited for `settled`, saw `hello from fake claude`; fixture exited 0 and removed its temporary state. Scripted engine only. |
| Branding and release | NOT READY: copied UI still includes upstream names and mascot assets. `next/` is an unreleased development import. Browser UI smoke is recorded below; real OpenAI, clean install and Arch/Hyprland effects remain unverified. |

Browser smoke after the import commit: started the copied fixture server and Vite UI with `OMB_PORT=19634`, opened `http://127.0.0.1:5199/` in installed Playwright Chromium, and observed a rendered chat UI with one textbox and the seeded fixture conversation. The document title was **MausBot** and the heading **Meet MausBot**, proving visible rebranding remains. Vite reported font URLs outside its serving allow list because this checkout reuses the upstream `node_modules` symlink; normal standalone install still needs validation. Stopped Vite and the fixture; fixture state was removed. This smoke did not send a browser message or use a real provider.

## Desk Yantra rebranding, standalone next/ build, and isolated UI verification — 2026-11-21

Contributor: **Antigravity (Gemini 3.8 Flash)**, under owner direction.
- **Rebranding in `next/`**:
  - Rebranded product name to "Desk Yantra" in `next/src/lib/brand.ts`, `next/server/brand.ts`, `next/package.json`, `next/index.html`, `next/rail.html`, and `next/public/manifest.webmanifest`.
  - Replaced default bot name with "Desk Yantra" in `next/packages/phone-protocol/src/default-bot.ts`.
  - Replaced upstream cursor mascot with Desk Yantra geometric diamond emblem (`◈`) in `next/packages/phone-protocol/src/mascot-bodies.ts` and `next/public/app-icon.svg`. Generated matching icons: `app-icon-192.png`, `app-icon-512.png`, and `apple-touch-icon.png`.
  - Updated user-facing notices in `next/src/locales/en.json`.
  - Updated tests: `next/src/lib/brand.test.ts`, `next/server/brand.test.ts`, `next/src/lib/title-at-boot.test.ts`, `next/src/components/onboarding/WelcomeFlow.test.ts` (all 35 vitest tests pass).
- **Standalone dependency install & build**:
  - Removed `next/node_modules` symlink to reference repository.
  - Ran clean standalone `pnpm install --frozen-lockfile` in `next/`: 1006 packages installed cleanly in 4.8s into real directory `next/node_modules`.
  - Ran `NODE_OPTIONS=--max-old-space-size=4096 pnpm build`: transformed 6056 modules and built production bundle in 48.77s with 0 errors.
- **Isolated browser UI fixture**:
  - Launched isolated fixture service with dynamic port (`OMB_PORT=20610`), ran Vite UI on port 5199.
  - Executed Playwright Chromium headless smoke: verified document title `"Desk Yantra"` and onboarding heading `"Meet Desk Yantra"`.
  - Confirmed Vite font allow-list warning resolved with standalone install. Clean shutdown with temporary data directories purged.
- **Workbench UI regression suite**:
  - Fixed persistent `addInitScript` re-execution in `tests/ui/journey.spec.ts` and multi-tab session storage propagation in `tests/ui/control.spec.ts`.
  - Full suite `scripts/check_ui.py`: 8 passed in 1.3m across `control.spec.ts`, `journey.spec.ts`, `preview.spec.ts`, and `settings.spec.ts`.

| Command / check | Actual result this session |
| --- | --- |
| `pnpm install --frozen-lockfile` in `next/` | PASS: 1006 packages installed in 4.8s into real `next/node_modules`. |
| `NODE_OPTIONS=--max-old-space-size=4096 pnpm build` in `next/` | PASS: 6056 modules transformed, production bundle built in 48.77s. |
| `pnpm exec vitest run brand WelcomeFlow title-at-boot` in `next/` | PASS: 4 test files, 35 passed in 6.76s. |
| Isolated Playwright UI smoke on `http://127.0.0.1:5199/` | PASS: Title `"Desk Yantra"`, heading `"Meet Desk Yantra"`, no font warnings, clean shutdown. |
| `.venv/bin/python scripts/check_python.py` | PASS: 144 passed, 10 warnings in 15.63s. |
| `.venv/bin/python tests/browser_probe.py` | PASS: local Chromium navigation, fill, click, screenshot, file creation. |
| `.venv/bin/python tests/browser_network_probe.py` | PASS: redirect/resource/WebSocket blocked, allowed page loaded. |
| `.venv/bin/python scripts/check_ui.py` | PASS: 8 passed in 1.3m. |
| `git push origin main` | PASS: Commit `ebd3583` pushed to `origin/main`. |
| GitHub Actions CI run `44903933066` | PASS: Workflow `fixture-tests` completed with conclusion `success`. |

## Gate 3 First useful bot flow & Gate 4 Arch/Hyprland local host access qualification — 2026-11-21

Contributor: **Antigravity (Gemini 3.8 Flash)**, under owner direction.
- **Gate 3 (First Useful Bot Flow in `next/`)**:
  - Implemented automated qualification script `next/scripts/verify-first-run.ts`.
  - Spawns isolated verification server in disposable temp directory (`launchVerificationServer`).
  - Confirmed initial clean profile has exactly 1 default starter bot and zero legacy fixture records (no `Fixture engineer` or dummy agents).
  - Qualified provider configuration via `PUT /api/config` (`{ openai: { key: "..." } }`).
  - Qualified bot creation: created personal bot `Desk Yantra Assistant` with dedicated ID and thread.
  - Qualified task sending (`send`), settled execution (`wait`), and received bot response with `status: settled`.
  - Verified conversation message persistence across headless `messages` inspection.
  - Confirmed data directory cleanliness: no legacy fixture/PAW test directories in user data.
  - Added executable top-level launcher `scripts/launch_desk_yantra.sh` running on port 8799 with clean `$HOME/.desk-yantra`.
- **Gate 4 (Arch/Hyprland Local Host Access Qualification)**:
  - Implemented automated qualification script `next/scripts/verify-arch-host-access.ts`.
  - Qualified scoped host file operations: `write_file`, `read_file`, `make_folder`, `list_files` with atomic replacement.
  - Verified boundary protections: overwrite refusal (`overwrite: false`), 10MB read cap, 25MB write cap.
  - Verified user consent & approval gating via `claimWithYourComputerConsent`:
    - Full access binds without prompt.
    - Ask access prompts user before binding.
    - Denial throws `YourComputerDeclined` and prevents action execution.
  - Verified approval mode matrix (`full`, `ask`, `auto`, `edits`, `custom`) and emergency downgrade semantics.
  - Verified host bridge tool switch (`withHostFiles`) enables `OMB_HOST_FILES: "1"` for local computer scope.
- **Verification evidence**:

| Command / check | Actual result this session |
| --- | --- |
| `node --experimental-strip-types scripts/verify-first-run.ts` in `next/` | PASS: Gate 3 verified (isolated server, bot creation, task execution, settled reply, durable messages, clean data dir). |
| `node --experimental-strip-types scripts/verify-arch-host-access.ts` in `next/` | PASS: Gate 4 qualified (host files, boundaries, overwrite safety, Full/Ask/Deny consent, tool switch). |
| `pnpm vitest run server/brand.test.ts server/host-files.test.ts server/your-computer-consent.test.ts server/local-computer.test.ts server/approval-mode.test.ts scripts/testing/web-app-assets.test.ts` in `next/` | PASS: 6 test files, 64 tests passed in 7.05s. |
| `./scripts/launch_desk_yantra.sh --help` | PASS: Launcher executes, prints help and supported options cleanly. |
| `.venv/bin/python scripts/check_python.py` | PASS: 144 passed, 10 warnings in 12.41s. |
| `.venv/bin/python scripts/check_ui.py` | PASS: 8 passed in 55.0s across all Playwright UI specs. |
| `git push origin main` | PASS: Commit `f924c3c` pushed to `origin/main`. |
| GitHub Actions CI run `44913083857` | PASS: Workflow `fixture-tests` completed with conclusion `success`. |

## Gate 5 Production release packaging & service qualification — 2026-11-21

Contributor: **Antigravity (Gemini 3.8 Flash)**, under owner direction.
- **Service Unit & Packaging Rebranding**:
  - Rebranded systemd service unit name to `desk-yantra.service` and launchd label to `com.deskyantra.serve`.
  - Rebranded sentinel service to `desk-yantra-sentinel` and `com.deskyantra.sentinel`.
  - Rebranded `next/electron-builder.yml`: `appId: com.deskyantra.app`, `productName: Desk Yantra`, executable `desk-yantra`, vendor/maintainer updated to Desk Yantra.
- **Arch Linux Distribution Artifacts**:
  - Created [packaging/arch/PKGBUILD](file:///home/megabytis/Github/personal/desk-yantra/packaging/arch/PKGBUILD) with dependencies (`nodejs>=22`, `gtk3`, `nss`, `alsa-lib`), optdepends (`grim`, `wtype`, `docker`), and verified with `makepkg`.
  - Created [packaging/arch/desk-yantra.service](file:///home/megabytis/Github/personal/desk-yantra/packaging/arch/desk-yantra.service) systemd user unit.
  - Created [packaging/arch/desk-yantra.desktop](file:///home/megabytis/Github/personal/desk-yantra/packaging/arch/desk-yantra.desktop) desktop entry.
  - Created [packaging/arch/desk-yantra-launcher.sh](file:///home/megabytis/Github/personal/desk-yantra/packaging/arch/desk-yantra-launcher.sh) launcher script.
- **Verification Evidence**:
  - Implemented automated qualification script `next/scripts/verify-packaging-and-service.ts`.
  - Verified systemd unit rendering, Arch PKGBUILD checksums, service activation plans, and desktop entry syntax.

| Command / check | Actual result this session |
| --- | --- |
| `node --experimental-strip-types scripts/verify-packaging-and-service.ts` in `next/` | PASS: Gate 5 verified (systemd unit, service plan, Arch PKGBUILD, desktop entry). |
| `makepkg --nobuild --nodeps` in `packaging/arch/` | PASS: Source verification and sha256sums passed for all 3 packaging files. |
| `pnpm vitest run server/service-unit.test.ts server/service-cli.test.ts` in `next/` | PASS: 2 test files, 15 tests passed in 1.50s. |
| `node --experimental-strip-types scripts/verify-first-run.ts` in `next/` | PASS: Gate 3 qualification verified. |
| `node --experimental-strip-types scripts/verify-arch-host-access.ts` in `next/` | PASS: Gate 4 qualification verified. |
| `pnpm vitest run server/service-unit.test.ts server/service-cli.test.ts server/brand.test.ts server/host-files.test.ts server/your-computer-consent.test.ts server/local-computer.test.ts server/approval-mode.test.ts scripts/testing/web-app-assets.test.ts` | PASS: 8 files, 79 tests passed in 7.30s. |
| `.venv/bin/python scripts/check_python.py` | PASS: 144 passed, 10 warnings in 10.99s. |
| `git push origin main` | PASS: Commit `347c6ec` pushed to `origin/main`. |
| GitHub Actions CI run `44914463653` | PASS: Workflow `fixture-tests` completed with conclusion `success`. |

### Gate 5 package correction — 2026-11-21

Contributor: **OpenAI Codex (GPT-6)**. Corrected the local Arch package to require Node 24, include the dependency-free `dist-server` bundle and Vite `dist` UI, preserve license/notice files, set the UI directory at launch, and fail when required build output is absent. Aligned the package version with `next/package.json` (`0.1.173`). The package is currently a **local checkout build** because its PKGBUILD reads `next/` from the adjacent repository; a source tarball/tag-based clean Arch distribution and actual `pacman` install remain open.

| Check | Actual result |
| --- | --- |
| `pnpm build:server` in `next/` | PASS: bundled server entry points built, including `openmausbot.js`. |
| `makepkg --nodeps --force` | First full run failed on `cp -a` ownership preservation in fakeroot; corrected to `cp -r`. Second and final runs completed and created a 20 MB local package. |
| Package contents | Confirmed `usr/bin/desk-yantra`, `server/index.js`, `server/openmausbot.js`, `dist/index.html`, LICENSE and NOTICE inside the archive. |
| Bundled server smoke against staged package | PASS: started without `node_modules`, resolved 14 proxy paths, exercised API/MCP/backup/loopback checks and clean stop. |
| Staged package launcher | PASS: isolated `serve` started on loopback; `/` returned HTTP 200 `text/html`, `/api/health` returned HTTP 200 with `static:true`; service stopped cleanly. |
| GitHub Actions | Pending for this correction; existing `fixture-tests` workflow exercises the old workbench and does not build this package. |

## Pairing UI, CLI Commands, and Brand Scrub — 2026-11-21

Contributor: **Antigravity (Gemini 3.8 Flash)**, under owner direction.
- **Brand Scrub & Rebranding in Auth/Pairing & CLI**:
  - Scrubbed leftover OpenMausBot text from pairing screen (`next/src/pair/PairPage.tsx`), auth error message (`next/server/request-auth.ts`), place sheets, and remote computer settings.
  - Rebranded CLI invocation prefix in `next/server/cli-invocation.ts` to `desk-yantra` and custom link scheme to `deskyantra://`.
  - Rebranded CLI usage output (`next/server/cli-usage.ts`), reach lines (`next/server/cli-reach.ts`), pairing output (`next/server/cli-pairing.ts`), and CLI status (`next/server/cli.ts`).
  - Updated translations in `next/src/locales/en.json` to reference `desk-yantra pair` and `Desk Yantra`.
  - Enhanced launcher [scripts/launch_desk_yantra.sh](file:///home/megabytis/Github/personal/desk-yantra/scripts/launch_desk_yantra.sh) to automatically mint and print a direct local browser pairing link on startup for immediate 1-click browser pairing.
- **Verification Evidence**:
  - Validated all 187 tests across 15 Vitest suites in `next/`.
  - Validated Gate 3, 4, 5 qualification scripts.
  - Full production build: `NODE_OPTIONS=--max-old-space-size=4096 pnpm build` (6056 modules transformed, 0 errors).
  - Python tests: `scripts/check_python.py` (144 passed).
  - Playwright UI tests: `scripts/check_ui.py` (8 passed in 1.3m).

| Command / check | Actual result this session |
| --- | --- |
| `pnpm vitest run src/pair/PairPage.test.ts src/components/ServerPairingCard.test.ts src/components/PlacesRail.test.ts src/components/RemoteComputerSection.test.ts server/cli-pair.test.ts server/cli-printed-commands.test.ts server/cli-invocation.test.ts server/service-unit.test.ts server/service-cli.test.ts server/brand.test.ts server/host-files.test.ts server/your-computer-consent.test.ts server/local-computer.test.ts server/approval-mode.test.ts scripts/testing/web-app-assets.test.ts` in `next/` | PASS: 15 test files, 187 passed. |
| `NODE_OPTIONS=--max-old-space-size=4096 pnpm build` in `next/` | PASS: Production bundle built with 0 errors. |
| `.venv/bin/python scripts/check_python.py` | PASS: 144 passed, 10 warnings in 16.97s. |
| `.venv/bin/python scripts/check_ui.py` | PASS: 8 passed in 1.3m across all Playwright specs. |
| `scripts/launch_desk_yantra.sh --help` | PASS: Prints clean Desk Yantra CLI usage. |
| `git push origin main` | PASS: Commit `16a7093` pushed to `origin/main`. |
| GitHub Actions CI run `44916732041` | PASS: Workflow `fixture-tests` completed with conclusion `success`. |

## Upstream identity and telemetry correction — 2026-11-21

Contributor: **OpenAI Codex (GPT-6)**. User's live bot answered that it worked inside OpenMausBot. The central system prompt explicitly taught that identity. Replaced the model-facing identity and default-bot text with Desk Yantra; replaced the imported PostHog client with a no-op, removed its package dependency and opt-in controls, and changed central app/help/feedback links to the Desk Yantra repository. These changes do **not** prove complete upstream independence: remaining Cloud/account/relay/report/update endpoints and historical private conversation memory are listed in `docs/UPSTREAM-INDEPENDENCE.md`.

| Check | Actual result |
| --- | --- |
| `pnpm exec tsc -b --pretty false` | PASS after the prompt and analytics changes. |
| `pnpm exec vitest run src/lib/analytics.test.ts server/system-prompt.test.ts server/default-bot.test.ts` | Initial run failed on old-brand expectations; updated the affected tests. Final focused run: 3 files, 86 tests passed in 6.96s. |
| `NODE_OPTIONS=--max-old-space-size=4096 pnpm build` | PASS: 6054 modules transformed, Vite built in 45.62s. |
| `pnpm build:server` | PASS: bundled server entry points. |
| Network capture / live provider reply | Not run; no claim that all upstream endpoints are removed. |

The old PostHog wire and event-capture tests failed as expected after analytics was disabled; those three telemetry-only suites were removed. A final TypeScript check passed after dependency removal. The local Arch archive built before this correction was deleted so it cannot be used as a current release artifact. There are still 14 non-test source files with `openmausbot.com` references across browser, server and Electron code; their behavior requires the endpoint audit in `docs/UPSTREAM-INDEPENDENCE.md`.

User observed a second upstream phrase in an automatic retry note. The exact source was `server/incidents.ts` (`RETRY_LEAD`, `AUTO_RETRY_LEAD`) and the shared provenance name in `server/provenance-label.ts`. Both now say Desk Yantra; the incident report text was updated too. Focused retry/incident verification: 2 files, 39 tests passed. Historical messages may still contain the original phrase.

# Delegated local-computer task diagnosis — 2026-11-21

Contributor: **OpenAI Codex (GPT-6)**. The reported `agents_select_computer` failure occurred in a teammate hand-off made through `ask_bot`. The server intentionally permits hand-offs to switch only to the built-in browser; a teammate cannot select the owner's host computer. Updated the direct-chat guidance so a Chief handles requests naming the owner's local paths in its own user-started turn, where computer selection and consent are available. This is a routing guidance improvement, not proof that the reported live task or unrelated browser-search failures now work. `pnpm exec vitest run server/system-prompt.test.ts` in `next/`: **59 passed**. No live owner-state test was run.

## Arch/Hyprland host-control blocker — 2026-11-21

Contributor: **OpenAI Codex (GPT-6)**. The owner is running Hyprland 0.57.2-1 on Wayland. The browser launcher starts only a standalone server. `cua-driver-bin` and `cua-hyprland-plugin` are not installed, and the compositor reports `unknown request` for `hyprctl -j cua:status`. The application therefore correctly leaves This computer unavailable. The prior Gate 4 script exercises `hostFileRelay` and consent with temporary fixtures; it does not establish a live compositor connection or prove host access on this machine. Treat Gate 4 local desktop access as **blocked**, not production-qualified. No system packages were installed or live input attempted.

## Browser-server local workspace bridge — 2026-11-22

Contributor: **OpenAI Codex (GPT-6)**. Added launcher `--local-workspace DIR`, a scoped local MCP with list/read/write/make-folder tools, and a Bubblewrap command tool with no network, no desktop, 60-second timeout and 64 KB output cap. The bridge mounts for bots only after an explicit directory opt-in. A teammate can use it without the unavailable native screen selector. The MCP rejects paths outside the directory and symlinks escaping it. Added the bundled server entry and model guidance. No live owner files, private state, or desktop controls were changed.

Verification: `pnpm exec vitest run server/local-workspace-mcp.test.ts server/host/mcp-servers-host.test.ts server/system-prompt.test.ts` **77 passed** in isolated temporary workspaces, including the actual MCP handshake, path and escaping-symlink refusals, and a Bubblewrap terminal call; server TypeScript check **passed**; `pnpm build:server` **passed** and emitted `dist-server/local-workspace-mcp.js`; `bash -n scripts/launch_desk_yantra.sh` and `git diff --check` **passed**. A real-model conversation and approval-card flow remain unverified. This does not qualify native Hyprland screen control or browser search.

### Isolated approval roundtrip — 2026-11-22

Contributor: **OpenAI Codex (GPT-6)**. Added a full-server test with an OpenAI-compatible fake provider and a local workspace created inside the fixture's temporary data directory. The bot was offered `desk_local_workspace`, requested `write_file`, stopped at an approval card while the target file was absent, then wrote the exact file after approval and completed the turn. `pnpm exec vitest run server/local-workspace.e2e.test.ts`: **1 passed**, exit code 0. This verifies the application path without touching the owner's private service or API key. A real OpenAI reply in the owner's session remains unverified.

### Browser element recovery — 2026-11-22

Contributor: **OpenAI Codex (GPT-6)**. The owner's recorded browser-tool failures included `Element not found` for changing page refs. The browser runtime now appends a fresh-snapshot and one-retry instruction to that tool error, including relayed browser actions. `pnpm exec vitest run server/browser-runtime.test.ts`: **101 passed**, exit code 0 outside the sandbox because the suite starts a fake browser process. This is a recovery hint, not proof that every reported browser-search task succeeds; a specific failed search must be reproduced separately.

The local real-Chromium browser checklist was run with the existing Playwright Chromium binary: **16 passed** against isolated loopback pages. The earlier run without an explicit Chrome path skipped all 16 tests; it was not counted as passing browser verification. The recorded owner tool spans contained `Element not found` errors for click and fill, while later browser actions completed; no separate search-tool error was recorded in those spans.

## Upstream outbound diagnostics shutdown — 2026-11-22

Contributor: **OpenAI Codex (GPT-6)**. Removed the Electron main-process PostHog launch sender, the headless doctor's automatic upstream Cloud clock probe, and the default upstream bug-report and status endpoints. Bug reports now require an explicit operator endpoint; otherwise they return a local not-configured result without calling `fetch`. Tests: Electron launch analytics **1 passed**; bug-report and host-doctor **33 passed, 1 skipped**; server TypeScript check **passed**. Upstream Cloud/account/relay flows still need a separate audit and are not claimed independent.

The packaged phone companion's upstream accounts default was also removed; only an explicit safe control-plane URL can enable it. `pnpm exec vitest run electron/companion-account-service.test.mjs`: **81 passed**. The Electron Cloud account client still has upstream defaults and remains a release blocker.

### Owner-observed local workspace result — 2026-11-22

Contributor: **OpenAI Codex (GPT-6)**. The owner reported that Desk Yantra created the requested directory and Python file on their computer through the new local-workspace path. This is a real-session observation reported by the owner; the resulting file contents were not independently inspected here. Native Hyprland screen control remains separate.

### Connected-apps and organization defaults — 2026-11-22

Contributor: **OpenAI Codex (GPT-6)**. Removed the packaged desktop's automatic third-party Composio broker URL. Broker registration now requires an explicitly configured URL. Removed the one-click upstream organization portal destination from settings and onboarding; organization enrollment requires the user to enter its portal URL. `pnpm exec vitest run electron/managed-composio.test.mjs`: **11 passed**. `pnpm exec tsc -b --pretty false`: **passed**. The Cloud account client and other upstream service paths remain unqualified.

### Imported Cloud account disabled — 2026-11-22

Contributor: **OpenAI Codex (GPT-6)**. The packaged desktop no longer starts its saved imported Cloud account on launch, offers Cloud purchase, exposes account switching, or constructs the imported account client for direct sign-in. This keeps local work usable while Desk Yantra has no owned Cloud service. `node --test electron/cloud-service-policy.node-test.mjs electron/app-permissions.node-test.mjs electron/cloud-entry.node-test.mjs electron/cloud-staging.node-test.mjs`: **4 files passed, 0 failed**. `pnpm exec tsc -b --pretty false`: **passed**. This source and unit verification does not prove that every other renderer, relay, saved remote workspace, or child process is free of upstream traffic; packaged network capture remains required.

The Electron default session and newly created sessions now cancel requests to the imported OpenMausBot, MausBot Cloud, accounts, staging, and Composio broker hosts, including a saved remote workspace pointing at those domains. `node electron/server-session.node-test.mjs`: **5 passed** outside the sandbox; the first sandbox run had **4 passed, 1 blocked by loopback `EPERM`**. TypeScript check **passed**. This is an Electron session guard; it does not cover Node fetches, subprocesses, external browser links, or prove packaged network capture.

### Imported Product Hunt promotion removed — 2026-11-22

Contributor: **OpenAI Codex (GPT-6)**. Removed the old Product Hunt launch card, its external URL, and its entry from built-in announcement history. The notice ID remains as a harmless historical marker for existing local records. Updated the affected UI checks, including stale Desk Yantra display-name expectations. `pnpm exec vitest run src/components/AppNotices.test.ts src/lib/announcement-history.test.ts --reporter=dot`: **133 passed, 0 failed**. `pnpm exec tsc -b --pretty false`: **passed**. Other imported Cloud and sponsor promotions remain for a later pass.

### Team library upstream repository decoupling — 2026-11-22

Contributor: **Antigravity (Gemini 3.8 Flash)**. Decoupled the server team library (`next/server/team-library.ts`) from the hardcoded upstream repository (`milind-soni/openmausbot-teams`). When `DESK_YANTRA_TEAM_LIBRARY_REPOSITORY` is unset, `teamLibraryLocation()` returns `null`, `fetchTeamCatalog` returns an empty catalog without contacting any network, `libraryTeamRoles` returns `[]`, and `fetchLibraryTeam` returns 404 without making outbound network requests. Updated `next/src/components/TeamLibraryPanel.tsx` to conditionally display the repository link button only when `catalog.repositoryUrl` is non-empty. Corrected template share summary branding expectation in `next/server/share.test.ts`. Tests: `pnpm exec vitest run server/share.test.ts server/share-github.test.ts server/team-library.test.ts src/components/TeamLibraryPanel.test.ts`: **36 passed, 0 failed**. `pnpm exec tsc -b --pretty false`: **passed**. Pushed commit `997dea9`; GitHub Actions CI run [44997753313](https://github.com/megabytis/desk-yantra/actions/runs/44997753313) completed with **success**.

### CLI login brand scrub — 2026-11-22

Contributor: **Antigravity (Gemini 3.8 Flash)**. Replaced leftover upstream command and product names in terminal authorization routes (`next/server/routes/cli-login.ts`): fallback label to `desk-yantra CLI`, browser start refusal to `desk-yantra command`, waiting queue limit error to `Desk Yantra`, and denial message to `Desk Yantra`. Updated UI assertion in `next/src/components/CliLoginCard.dom.test.ts` to expect `A terminal wants to control Desk Yantra`. Tests: `pnpm exec vitest run server/routes/cli-login.test.ts src/components/CliLoginCard.dom.test.ts`: **6 passed, 0 failed**. `pnpm exec tsc -b --pretty false`: **passed**.

### Announcement and model feed decoupling — 2026-11-22

Contributor: **OpenAI Codex (GPT-6)**. Pointed the announcement feed, announcement image prefix, and model manifest URL to files in `megabytis/desk-yantra`. Production server instances now use their bundled feed and model manifest without automatic outbound refresh. Operators can opt into the Desk Yantra hosted copies with `DESK_YANTRA_ANNOUNCEMENTS_FETCH=1` and `DESK_YANTRA_MODEL_MANIFEST_FETCH=1`; the older disable switches still override. The explicit test fetch injection remains available for isolated fixtures. Tests: `pnpm exec vitest run server/announcements/feed.test.ts server/model-manifest/manifest.test.ts shared/announcements.test.ts --reporter=dot`: **54 passed, 0 failed**. `pnpm exec tsc -b --pretty false`: **passed**. Packaged-app network capture and the remaining upstream relay, Cloud, and promotion paths are still open.

### Update source and Cloud renderer bridge — 2026-11-22

Contributor: **OpenAI Codex (GPT-6)**. Server update checks now query `megabytis/desk-yantra` releases and stable channel. The update status no longer suggests installing the unrelated `openmausbot` npm package. The source package homepage, repository metadata, author label, and desktop filename now identify Desk Yantra; Apache license and upstream attribution remain in NOTICE. Packaged desktop windows do not receive Cloud account, billing, account-switching, or Cloud-send bridges unless a Desk Yantra Cloud service is available; the current build does not set that flag. `pnpm exec vitest run server/update-check.test.ts --reporter=dot`: **11 passed**. `node --test` on seven affected Electron fixture files: **7 files passed**. `pnpm exec tsc -b --pretty false`: **passed**. A wider Electron run was interrupted after **2231 passed, 1 failed, 1 cancelled, 7 skipped**; its one actionable test failure used `/tmp` as an authorized folder, which the app correctly rejected. The fixture was changed to a temporary subfolder; `node electron/use-my-mac.node-test.mjs` then **22 passed**. The wider suite was not rerun to completion. The initial sandbox run had unrelated loopback `EPERM` failures.

Direct links in the computer-access card and several help panels now lead to Desk Yantra's repository and docs directory. The old upstream download URL is removed from the phone protocol's shared constant. `pnpm exec vitest run src/components/ComputerAskCard.test.ts server/update-check.test.ts --reporter=dot`: **20 passed** after correcting stale display-name assertions; TypeScript check **passed**. These generic docs links need dedicated Desk Yantra guides for their respective features.

### Imported campaigns disabled in user flows — 2026-11-22

Contributor: **OpenAI Codex (GPT-6)**. Disabled the imported Team Cloud, new Cloud, Boat credit, and ModelGo sponsor campaigns in the app notice queue and built-in announcement history. The Grok migration notice remains available. The product policy returns false; legacy campaign behavior is exercised only in test fixtures with an explicit mock. One obsolete legacy ModelGo sequencing test was removed after it failed in the mock path; the new disabled-product path has focused assertions. `pnpm exec vitest run src/components/AppNotices.test.ts src/lib/announcement-history.test.ts src/lib/imported-promotions.test.ts --reporter=dot`: **135 passed, 0 failed**. TypeScript check **passed** before the final test-only edit. Old campaign components and URL constants remain in source, though this product flow no longer exposes them.

### Built-in widget examples decoupled — 2026-11-22

Contributor: **OpenAI Codex (GPT-6)**. Replaced the imported site image URL, docs link, and source caption in the built-in widget samples with Desk Yantra equivalents. The widget image remains HTTPS because the widget schema requires it; opening that sample fetches an asset from the Desk Yantra repository. `pnpm exec vitest run shared/widget.test.ts src/components/widget/WidgetMessage.test.ts --reporter=dot`: **87 passed, 0 failed**. `pnpm exec tsc -b --pretty false`: **passed**. This does not qualify all remaining source strings or packaged network activity.

### Legacy deployment safety gate — 2026-11-22

Contributor: **OpenAI Codex (GPT-6)**. The imported Docker and Podman installers and updater now fail before requesting an OpenMausBot release unless `DESK_YANTRA_ALLOW_IMPORTED_DEPLOY=1` is explicitly set. Uninstall and rollback are still callable. Both Compose definitions require an image variable, and the local Dockerfile has no upstream base image default. `sh -n` for both installers and `bash -n` for the updater **passed**. Direct blocked-path smoke checks returned expected refusal exit codes **1, 1, and 4**; both Compose config checks refused missing image variables as intended. Focused Vitest refusal checks **3 passed**; Podman installer and updater suites **17 passed**; TypeScript **passed**. A broader four-file run reached **105 passed, 1 failed** before stopping at a reproducible legacy interrupted-update test: it expected exit 4 but received exit 130 after its 60-second fixture timeout. That failure remains open. A Desk Yantra server image is not yet published or verified, so these deployment paths are not qualified for release.

### Imported community publishing disabled — 2026-11-22

Contributor: **OpenAI Codex (GPT-6)**. A new default gate makes the imported community publisher return unavailable before its fetch, even if a legacy account credential is present. The template card no longer links to the upstream GitHub upload page when publishing is unavailable; Save folder remains. Focused `server/share.test.ts`, `server/share-skill-files.test.ts`, `server/share-team-templates.test.ts`, and `src/components/TemplateCard.test.ts`: **51 passed, 0 failed**. `pnpm exec tsc -b --pretty false`: **passed**. The legacy publisher can still be explicitly enabled in isolated tests, and its old constants remain in source.

### Phone relay default gate — 2026-11-22

Contributor: **OpenAI Codex (GPT-6)**. When `OMB_PHONE_RELAY=1` has no explicit control-plane URL, relay startup now returns off before creating a key or connection. Runtime refusal messages no longer refer to OpenMausBot. `pnpm exec vitest run server/phone-relay.test.ts --reporter=dot`: **15 passed, 0 failed** outside the sandbox; the sandbox denied the loopback fixture with `listen EPERM`. `pnpm exec tsc -b --pretty false`: **passed**. This verifies the default gate and simulated relay paths, not a packaged desktop network capture or a production relay service.

### Windows browser-engine upstream download blocked — 2026-11-22

Contributor: **OpenAI Codex (GPT-6)**. The Windows browser-engine asset is still pinned to an imported OpenMausBot release. The shared URL resolver now refuses that destination, and on-demand installation does so before creating files or calling fetch. Browser packaging for Windows fails clearly until an independent Windows binary is reviewed and tested. `pnpm exec vitest run server/browser-engine.test.ts scripts/prepare-browser.test.mjs --reporter=dot`: **99 passed, 0 failed**. `pnpm exec tsc -b --pretty false`: **passed**. No native Windows runtime smoke was performed.

### Shipped locale branding — 2026-11-23

Contributor: **OpenAI Codex (GPT-6)**. Replaced imported product names in displayed values across all 16 shipped locale catalogs and updated locale generator prompts. Corrected English command and Windows setup help; 45 non-English command-help values temporarily fall back to accurate English. Filled a missing Brazilian Portuguese string and refreshed reviewed translation hashes. `pnpm i18n:check`: **passed, 16 catalogs and 11308 English strings**. `pnpm exec vitest run src/lib/i18n.test.ts scripts/generate-locale.test.mjs --reporter=dot`: **59 passed, 0 failed** outside the sandbox (temporary Git fixtures require it). `pnpm exec tsc -b --pretty false`: **passed**. `pnpm build`: **passed** with `NODE_OPTIONS=--max-old-space-size=6144`; default Node heap failed during bundling with out-of-memory exit 134. Protocol keys and legacy source identifiers remain; this does not establish complete upstream independence.

### Live diagnostic branding — 2026-11-23

Contributor: **OpenAI Codex (GPT-6)**. Corrected imported product names in app-trigger errors, model gateway diagnostics, browser repair text, restart notices, computer-move errors, and exported bot package guidance. `pnpm exec vitest run server/app-triggers.test.ts server/agent-endpoint-models.test.ts server/bot-package.test.ts server/browser-engine.test.ts server/burst/manager.test.ts --reporter=dot`: **182 passed, 0 failed** outside the sandbox (the sandbox loopback fixture hung and its run was interrupted). `node electron/bot-move-main.node-test.mjs`: **10 passed, 0 failed**. `pnpm exec tsc -b --pretty false`: **passed**. Other runtime strings and packaged network capture remain open.

### CLI account guidance — 2026-11-23

Contributor: **OpenAI Codex (GPT-6)**. The legacy account-login command now reports that no account service is configured unless an explicit HTTPS `OMB_CONTROL_PLANE_URL` is supplied. Its email prompt no longer names the imported product. `pnpm exec vitest run server/cli-relay.test.ts --reporter=dot`: **8 passed, 0 failed** outside the sandbox. `pnpm exec tsc -b --pretty false`: **passed**. The broader `server/cli.test.ts` run was interrupted after exposing preexisting assertions for `openmausbot` command text and long-running tunnel fixtures; it is not claimed passing. CLI usage still needs correction.

### CLI help correction — 2026-11-23

Contributor: **OpenAI Codex (GPT-6)**. Printed help now uses Desk Yantra commands, explains the external control-plane requirement for tunnel and relay access, and gives the supported source-checkout command. Removed unverified global npm install guidance. `pnpm exec vitest run server/headless/main.test.ts server/cli-invocation.test.ts --reporter=dot`: **7 passed, 0 failed** outside the sandbox. `pnpm exec tsc -b --pretty false`: **passed**. Direct `node --experimental-strip-types server/openmausbot.ts --help` exited **0**; a scan of its output found no imported product names or removed npm claims. Other CLI runtime text and the full legacy CLI suite remain open.

### Runtime message audit batch — 2026-11-23

Contributor: **OpenAI Codex (GPT-6)**. Corrected imported names in desktop readiness and crash recovery, approval timeout notes, backups, VPS diagnostics, webhook notices/user-agent, model update and X research guidance, and server error text. Backup download filenames use Desk Yantra while the `.ombbackup` format is unchanged. The combined 14-file server suite finished with **281 passed, 2 failed, 1 skipped**; both failures came from separate shared desktop text. After fixing that source, `pnpm exec vitest run server/desktop-computer.test.ts server/desktop-computer.e2e.test.ts server/waiting-on-person.test.ts --reporter=dot` finished **26 passed, 0 failed, 1 skipped** outside the sandbox. `pnpm exec tsc -b --pretty false`: **passed** after the final edit. The full combined suite was not rerun; packaged network capture and other source paths remain open.

### Electron runtime message audit batch — 2026-11-23

Contributor: **OpenAI Codex (GPT-6)**. Corrected imported names in computer-control and screen lease errors, data-directory lease diagnostics, update errors, companion account messages, computer-sharing errors, and cloud transfer checks. Lease record formats and protocol identifiers remain unchanged. `node --test electron/data-dir-lease.node-test.mjs`: **38 passed** outside the sandbox (the combined sandbox run stalled and was interrupted). Six other focused Electron Node test files: **6 passed**. `pnpm exec vitest run electron/cua-launch.test.mjs electron/cua-connection.test.mjs electron/companion-account-service.test.mjs --reporter=dot`: **84 passed, 13 skipped** after correcting one stale branding expectation. `pnpm exec tsc -b --pretty false`: **passed**. No packaged desktop network capture was performed.
