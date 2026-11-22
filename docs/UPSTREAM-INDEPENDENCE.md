# Upstream independence audit

2026-11-21 — OpenAI Codex (GPT-6), under owner direction.

The imported application still contains OpenMausBot names and service integrations. A source rename alone cannot establish independence. This document records the remaining work before claiming that Desk Yantra has no upstream branding or automatic upstream traffic.

## Fixed in this pass

- The model's central system prompt, default bot text, and volatile context notes now identify Desk Yantra. This addresses the user's observed reply about being inside OpenMausBot on new turns. Existing conversation history and personal memory are left intact and can still contain old wording.
- Automatic retry and incident notes now use Desk Yantra as their provenance label. The older text remains in existing chat history.
- The browser PostHog analytics implementation is replaced with a local no-op; the settings switch and bot-accessible setting are removed. `posthog-js` is removed from the package manifest and lockfile. Telemetry-only test suites were removed; the disabled policy has a focused regression.
- The Electron main-process launch analytics hooks are now inert and cannot send to PostHog, even if an old local preference says analytics is on. The headless doctor no longer contacts the upstream Cloud to check clock offset. Bug reports and their status checks send no network request unless the operator explicitly configures a report endpoint.
- The packaged desktop's phone companion no longer defaults to the upstream accounts control plane. A phone control-plane URL must be explicitly configured.
- The main app/help/feedback links now target the Desk Yantra repository rather than upstream promotion.

## Release blockers

1. Audit and remove or replace all remaining upstream service destinations, especially `cloud.openmausbot.com`, `accounts.openmausbot.com`, `admin.openmausbot.com`, `relay*.openmausbot.com`, upstream release/download links and the bug-report sender. Their current use differs: some are clicked links, some are optional cloud/account features, and some can be probed by diagnostics. Do not silently redirect these services to an unrelated Desk Yantra URL.
2. Remove or disable upstream Cloud, account, phone relay, checkout, and update flows until Desk Yantra owns and verifies replacements. Preserve only locally working features in the user experience.
3. Audit all user-visible locales, desktop resources, icon/mascot assets, and default bot templates for upstream names and promotional text. Keep Apache-2.0 attribution in license and notice files.
4. Verify an isolated browser session with network capture: no requests to OpenMausBot, PostHog, or upstream domains during launch, pairing, bot creation, task execution, settings and shutdown. Repeat for the packaged desktop app and any background service.
5. Review existing private conversations and memory with the owner before any cleanup. New prompts are corrected, but historical messages may still lead a model to repeat the old name.

Until those gates pass, describe the app as an in-progress fork and do not claim complete telemetry or branding independence.

The Arch archive made before this pass was removed. Rebuild a package only after the endpoint and network-capture gates pass.
