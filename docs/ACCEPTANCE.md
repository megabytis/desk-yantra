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


