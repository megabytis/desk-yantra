# Support and release policy

The package version 0.1.0 identifies development source, not a production release. There are no published supported release artifacts or automatic upgrades.

| Environment | Evidence and support boundary |
| --- | --- |
| Arch Linux x86_64 / Hyprland | Owner's development target; local-model, Docker and selected desktop evidence in ACCEPTANCE.md. Fresh-machine installation remains unverified. |
| Ubuntu GitHub Actions / x86_64 | Fixture build, Python, Chromium and UI checks. No desktop, Docker isolation or live model claim. |
| Python 3.13 / Node 24 | Verification baseline. Node builds assets only. Other Python versions allowed by dependency metadata have not been separately validated. |
| ARM, macOS, Windows, multi-user hosting | Unverified and unsupported deployment targets. |

Use committed lockfiles. Rebuild the frontend when upgrading source. Sandbox images are currently manually built as paw-sandbox:local; immutable image digests, SBOM, provenance, signing and automated dependency audits remain release blockers.

Before a first release, satisfy PLANNING.md's applicable gates, choose and record the project license, review dependency notices, validate a clean installation, and test state migration plus backup/restore. No license grant is introduced by this policy. Production version tags and releases require owner authorization. Pre-1.0 releases must explain incompatible API/state changes; future stable versions should distinguish breaking, additive and corrective changes.

A private offline `backup` / `restore` command now snapshots SQLite and referenced artifacts with checksums. It includes the encryption key and token. It restores only to a fresh state directory and rewrites artifact paths; fixture data was tested. For upgrades, keep the old source revision and a separate backup, and stop work and both services first. Restore over existing state and automatic replay of interrupted actions are rejected. Unversioned state upgrades to schema version 1 on startup, tested on a temporary copy of real data. Upgrade migration and rollback across released versions remain unvalidated.
