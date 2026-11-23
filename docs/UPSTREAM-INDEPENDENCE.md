# Upstream independence audit

2026-11-21 — OpenAI Codex (GPT-6), under owner direction.

The imported application still contains OpenMausBot names and service integrations. A source rename alone cannot establish independence. This document records the remaining work before claiming that Desk Yantra has no upstream branding or automatic upstream traffic.

## Fixed in this pass

- The model's central system prompt, default bot text, and volatile context notes now identify Desk Yantra. This addresses the user's observed reply about being inside OpenMausBot on new turns. Existing conversation history and personal memory are left intact and can still contain old wording.
- Automatic retry and incident notes now use Desk Yantra as their provenance label. The older text remains in existing chat history.
- The browser PostHog analytics implementation is replaced with a local no-op; the settings switch and bot-accessible setting are removed. `posthog-js` is removed from the package manifest and lockfile. Telemetry-only test suites were removed; the disabled policy has a focused regression.
- The Electron main-process launch analytics hooks are now inert and cannot send to PostHog, even if an old local preference says analytics is on. The headless doctor no longer contacts the upstream Cloud to check clock offset. Bug reports and their status checks send no network request unless the operator explicitly configures a report endpoint.
- The packaged desktop's phone companion no longer defaults to the upstream accounts control plane. A phone control-plane URL must be explicitly configured.
- The packaged desktop no longer registers with the imported Composio broker by default. Organization onboarding and settings no longer offer an upstream admin portal button; the user must enter a portal URL.
- The packaged desktop no longer restores the imported Cloud account at startup or offers its purchase flow. Direct account-client creation is refused while no Desk Yantra Cloud service exists. Saved remote workspaces, renderer links, relay modules and packaged network capture still need audit.
- Electron sessions now cancel requests to known imported service domains, including saved workspace origins. Node fetches, subprocesses and links opened in the external browser need separate treatment and network capture.
- The old Product Hunt launch card and built-in announcement pointing at the imported product were removed. Other imported Cloud and sponsor promotions remain under audit.
- Announcement and model feeds now use bundled copies by default and point to Desk Yantra repository files when an operator explicitly enables remote refresh. Their request user-agent identifies Desk Yantra.
- Server update checks now target Desk Yantra releases, and update status no longer suggests the imported npm package. Packaged windows hide imported Cloud account and billing bridges while no Desk Yantra Cloud service is available. Package metadata identifies Desk Yantra.
- The computer-access download link and several help links no longer send users to the upstream product or documentation site. They currently use the Desk Yantra repository or docs index until feature-specific guides are written.
- Imported Team Cloud, new Cloud, Boat credit, and ModelGo campaigns are disabled in the app notice queue and built-in announcement history. Their dormant components and URL constants still need removal or replacement before the source branding audit is complete.
- Built-in widget examples now identify Desk Yantra and use its repository for the example image and documentation link, avoiding a request to the imported product site when the image is opened.
- Legacy Docker and Podman installers and the updater now refuse fresh installs or updates by default, because their published image and release feeds belong to OpenMausBot. Uninstall and rollback stay available. An operator can explicitly set `DESK_YANTRA_ALLOW_IMPORTED_DEPLOY=1` to run those legacy paths. Compose files and the local extension Dockerfile no longer select the upstream image implicitly; an operator must provide the image. This is a safety gate, not a Desk Yantra server release.
- Imported community template publishing is unavailable by default even if a legacy account token exists; it makes no request to the old Admin service. The fallback card offers Save folder without the imported community upload link. The old publisher and constants remain in source for audit.
- Phone relay now exits before creating a connection key when `OMB_PHONE_RELAY=1` but no explicit `OMB_CONTROL_PLANE_URL` is configured. Its runtime refusal text no longer names the imported product. An explicitly configured control plane remains an operator choice and requires separate qualification.
- The reviewed Windows browser-engine pin still identifies an OpenMausBot release, so Desk Yantra now refuses that URL before downloading or staging files. Windows browser packaging fails clearly until an independent Windows engine is verified; Linux and macOS pins are unaffected.
- The main app/help/feedback links now target the Desk Yantra repository rather than upstream promotion.
- The server team library catalog and fetch helpers no longer point by default to the upstream community team repository. When DESK_YANTRA_TEAM_LIBRARY_REPOSITORY is unset, the catalog returns empty and no outbound network request is made. The team library UI panel now renders the repository button only when an explicit repository URL is configured.
- Rebranded template share export summaries in the server to Desk Yantra and updated expectations in server tests.
- Rebranded CLI login route labels, browser refusal messages, and denial provenance to Desk Yantra (`next/server/routes/cli-login.ts`), and updated DOM card expectations (`next/src/components/CliLoginCard.dom.test.ts`).
- All 16 shipped locale catalogs now display Desk Yantra instead of imported product names in translated values. The locale generator prompts use Desk Yantra. Seven English help messages with obsolete CLI commands or unsupported Windows setup were corrected; 45 corresponding non-English command-help values temporarily use accurate English text. Existing localization keys and protocol identifiers remain for compatibility. The missing Brazilian Portuguese `chat.notice.computerNotReady` entry was added. Locale catalog check and 59 focused tests passed; TypeScript check passed.

## Release blockers

1. Audit and remove or replace all remaining upstream service destinations, especially `cloud.openmausbot.com`, `accounts.openmausbot.com`, `admin.openmausbot.com`, `relay*.openmausbot.com`, and the bug-report sender. The imported Windows browser-engine download is now blocked pending an independently verified replacement. Legacy installer and updater destinations are gated by explicit operator opt-in. Their current use differs: some are clicked links, some are optional cloud/account features, and some can be probed by diagnostics. Do not silently redirect these services to an unrelated Desk Yantra URL.
2. Remove or disable upstream Cloud, account, phone relay, checkout, and update flows until Desk Yantra owns and verifies replacements. Preserve only locally working features in the user experience.
3. Audit all user-visible locales, desktop resources, icon/mascot assets, and default bot templates for upstream names and promotional text. Keep Apache-2.0 attribution in license and notice files.
4. Verify an isolated browser session with network capture: no requests to OpenMausBot, PostHog, or upstream domains during launch, pairing, bot creation, task execution, settings and shutdown. Repeat for the packaged desktop app and any background service.
5. Review existing private conversations and memory with the owner before any cleanup. New prompts are corrected, but historical messages may still lead a model to repeat the old name.

Until those gates pass, describe the app as an in-progress fork and do not claim complete telemetry or branding independence.

The Arch archive made before this pass was removed. Rebuild a package only after the endpoint and network-capture gates pass.
