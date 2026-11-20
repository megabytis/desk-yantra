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
