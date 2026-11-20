# Desk Yantra

A self-hosted personal agent workspace with a React/TypeScript browser interface, Python OpenHands SDK workers, isolated Docker execution, and a separately authenticated Linux companion. See [acceptance status](docs/ACCEPTANCE.md) for actual live verification and remaining gaps. The deployment supports a single trusted local user.

## Arch Linux installation

Install Python tooling, Node and Docker using your normal system administration workflow:

```sh
sudo pacman -S --needed uv nodejs npm docker grim wtype
uv sync --locked --python 3.13
npm ci
npm run build
uv run python -m workbench
```

Open http://127.0.0.1:8765 and enter the launch token printed in your terminal. Both web service (8765) and companion (8766) bind only to loopback. Keep the launcher running. Closing a browser tab does not stop runs. To stop all active work locally:

```sh
uv run python -m workbench stop
```

1. **Settings & providers → Add connection**: name a connection, choose its type, enter its base URL/key, save, refresh models, select a model, test inference, and set the default.
2. **Computer access → Add workspace**: create a sandbox or host workspace grant. For host file work choose an existing folder. Shell permission grants account-wide execution; it is not confined by the folder.
3. **Agents**: create a profile with instructions, optional model override, tools and allowed workspace grants.
4. **Chat**: select the agent and workspace and submit a task. Approve or deny exact actions and proposed diffs. Inspect terminal output and SDK events.
5. **Runs / Artifacts**: reconnect to work and download actual output snapshots.

Archive unused agents or connections from their settings cards. This prevents new tasks while preserving running work, credentials, and history. Enable **Show archived** to restore them. An archived default connection must be restored or replaced before new tasks can use it.

After a completed task, send a follow-up in the conversation composer. Prior results remain attached to the conversation; the next task gets its own run history and fresh approvals. Interrupted tasks require review before starting replacement work. A run finishing does not establish task correctness: the interface flags an unresolved last-command failure, and final model messages are displayed alongside actual tool evidence. One bounded evidence review lets an agent correct a premature conclusion while preserving tool budgets and approvals.

OpenAI, Anthropic, Gemini, OpenRouter, xAI, Ollama, LM Studio and compatible APIs have discovery adapters. Unknown model capabilities are explicitly unknown. Keys are encrypted at rest with a local mode-0600 key. This protects accidental database disclosure, not compromise of the Linux account. Local models require no paid account. Ollama uses `/api/tags` for installed models and `/v1` for inference. The model must support tool calling for agent work.

## Sandbox

```sh
sudo systemctl start docker
docker build -t paw-sandbox:local sandbox
```

The launcher user needs Docker access. Docker membership effectively grants root-level host control; configure it deliberately. Containers get no host bind mounts unless you create an explicit shared sandbox grant in Computer access. Shared folders appear read-only at `/shared`; file tools can list and read them without shell permission. The image uses an unprivileged agent account with UID 1000 by default. If your UID differs, build with `docker build --build-arg AGENT_UID="$(id -u)" -t paw-sandbox:local sandbox` so explicitly shared private files remain readable without weakening their host permissions.

Containers use dropped capabilities, no-new-privileges, CPU/memory/process limits, and an unprivileged user. They retain network access. A sandbox conversation retains its container across follow-up tasks; delegated runs get independent containers. Browser tools use persistent Chromium and capture screenshots into Artifacts. Browser navigation and interaction require approval because they may affect external services. Stop removes the conversation container. Completed containers remain for inspection; remove selected `paw-<workspace-id>` containers when no longer needed.

After a sandbox run completes, open **Browser → Take browser control**. You can navigate, click the actual page capture, type into focused fields, and send supported keys. **Return control** enables follow-up tasks. Agent work and user takeover do not overlap. This controls sandbox Chromium only; it does not establish host desktop input support. The live Docker suite verifies navigation, file creation, screenshot display, user clicks and typing, returning control, container restrictions, and exact downloaded file contents.

## Desktop

The companion reports the actual Wayland session, advertised portal interfaces, `grim` capture availability and keyboard/pointer availability independently. Capture and input each require their own grant and exact-action approval. `grim` uses direct compositor access; the local approval is the consent mechanism. `wtype` typing depends on compositor virtual-keyboard protocol support and is live-verified on Hyprland with a disposable focus-checked window. The optional `ydotool` adapter supports typing, absolute pointer movement and button clicks when its daemon socket is accessible. Set `YDOTOOL_SOCKET` if needed. Configure the daemon deliberately; the app never elevates itself to start it. Host pointer input remains unverified. Portal consent-session integration remains unimplemented; this session advertises Screenshot/ScreenCast but not RemoteDesktop. Captures stay in ignored local state; never publish them.

Approved captures are attached as SDK image observations only when vision support is reported by the connection's model metadata or known SDK catalog. Text-only or unknown models receive the artifact reference and an explicit instruction that they have not seen the image. Actual image-based inference still requires live validation with a vision model. Captures may contain sensitive pixels; the host screen approval states that a compatible selected model receives the image.

## Persistence and recovery

SQLite WAL stores settings, profiles, run records, approvals, event history and artifact metadata. Workers are independent processes. Every tool action has started/finished journal entries. Server restart kills old workers. It redoes safe inference/read-only work when no mutating call was issued, and marks other interrupted runs `review`. It never automatically replays commands or submissions with an uncertain outcome. Review the existing event history and real world outcome before creating a replacement task. Full SDK checkpoint continuation is not yet implemented. Companion restart checks recorded Linux process start times before terminating prior command groups and marking affected work for review.

Interrupted, stopped, and failed runs show a review form. Record the observed outcome, then choose **Close review without replaying actions**. The companion must confirm tool cleanup; otherwise the review stays open. Closing cancels unused approvals, removes the conversation's sandbox container, and retains saved artifacts. The run becomes `reviewed`, preserving its previous status and your notes rather than claiming success. You may then send a follow-up as a new run with fresh approvals. Inspect any external account effects yourself before doing so.

The companion checks the current grant at execution time. All operations except scoped reads need an atomically consumed one-use approval. File tools reject traversal, symlinks, hard links, special files and private app state. Revocation stops matching active runs. Tools are limited to 30 calls per worker, 90 across the task tree, and delegation to two levels; children inherit the intersection of parent and profile tools and must have the same workspace grant. Up to 30 iterations are allowed per SDK run.

## Development and tests

```sh
PAW_STATE=/tmp/paw-tests LITELLM_LOCAL_MODEL_COST_MAP=True uv run pytest -q
npm run build
npx playwright install chromium
uv run python tests/browser_probe.py
uv run python tests/fixture_server.py
# In a second terminal, start the application, then:
npx playwright test
```

The fixture server on 18767 is scripted, not an actual model. Browser tests create disposable Git repositories under `/tmp` and exercise the real SDK/companion execution path. Unit tests must use a separate `PAW_STATE`. UI tests currently expect the running app's `.state/token` and create clearly named fixture profiles. Do not point CI at a personal state directory.

The build's known scripted fixtures and live verification connections and their agents/runs are hidden from normal UI views. Use **Show test data** to inspect them. This changes visibility only and does not delete history. Personal connections you create remain visible. Connection and agent profiles can be edited from their management cards. The guided setup links model connection, workspace authorization and agent setup. Responses render Markdown, tables and code; approvals show the actual file diff or command and working directory.

An additional live suite uses an actual local llama.cpp server and is excluded from fixture CI:

```sh
llama-server -m /path/to/Qwen3-1.7B-Q8_0.gguf --host 127.0.0.1 --port 18768 --alias qwen3-local -c 8192 -np 1 -t 2 -ngl 0 -n 768 --jinja --chat-template-kwargs '{"enable_thinking":false}' --temp 0
npx playwright test --config playwright.live.config.ts
```

The live suites passed on 2026-11-20 with official Qwen models (SHA-256 values recorded in the acceptance ledger). The 0.6B model passed simple file writing and the Docker browser/takeover path, but failed the real repair scenario. The 1.7B model passed the failing-test repair journey, including diagnosis, approved edit and a passing retest verified on disk. Use a sufficiently capable tool-calling model for the full suite. Model weights are not included. Files under `/tmp`, including a test model, do not survive a reboot.

Additional explicitly invoked live probes, with actual system effects restricted to disposable test targets:

```sh
PYTHONPATH=. PAW_STATE=/tmp/paw-readonly-check uv run python tests/docker_sharing_probe.py
PYTHONPATH=. PAW_STATE=/tmp/paw-live-input uv run python tests/live_host_input.py
```

The input probe opens a native Wayland window, verifies its compositor focus, types a harmless marker through the companion, and checks revocation. It requires Hyprland and wtype. It is not run by CI and saves no recording.

Set `PAW_STATE` to a private persistent directory to relocate state. Keep it outside any public repo. The application does not load `.env` automatically. No provider credentials are required to launch. Python and npm dependency lockfiles are included. Node only builds the web assets; there is no production Node service.

## Publishing

The official source repository is `git@github.com:megabytis/desk-yantra.git`. The project remains under active development and has not passed the production release gates in `PLANNING.md`. Keep `.state`, `.env`, recordings, model weights, and logs out of commits. A GitHub Actions fixture workflow is included.
