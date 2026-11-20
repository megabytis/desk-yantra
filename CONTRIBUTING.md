# Contributing

Read PLANNING.md, docs/ARCHITECTURE.md and docs/ACCEPTANCE.md before changing execution boundaries. Use a branch and a focused pull request. Describe the concrete behavior change, verification and remaining limits. Never commit runtime state, credentials, captures or model weights.

Install from uv.lock and package-lock.json with Python 3.13 and Node 24:

```sh
uv sync --locked --python 3.13
npm ci
npm run build
uv run python scripts/check_python.py
npx playwright install --with-deps chromium
uv run python tests/browser_probe.py
uv run python scripts/check_ui.py
```

The Python and UI runners create private temporary state and remove it after each run. The UI runner starts the application and scripted model fixture, checks readiness, runs Playwright and terminates its process groups. Ports 8765, 8766 and 18767 must be free. It refuses occupied ports rather than testing a personal service. Service logs and pairing tokens are deleted with temporary state. Playwright failure output remains in ignored test-results; inspect it for sensitive content before sharing. The tests create disposable projects in /tmp. They exercise actual local shell/file effects, with scripted model responses.

Record your name, changes, exact commands and observed results in PLANNING.md and docs/ACCEPTANCE.md. Distinguish fixtures from real model, Docker and desktop evidence. Live probes require deliberate grants and the documented services; they are not part of fixture CI.

All model tools must route through the companion. Preserve execution-time grant checks, one-use exact approvals and conservative recovery of uncertain effects. Report suspected vulnerabilities privately using SECURITY.md.
