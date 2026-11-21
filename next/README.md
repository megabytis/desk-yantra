# Desk Yantra next: upstream OSS import

This directory is an **unreleased development import** of OpenMausBot revision `4e22b4d9b3ae3a9c5ed60ba90632e667e1c3a1d4`. It is the base for the next Desk Yantra product. It still shows upstream names and mascot assets; it must be rebranded and reviewed before distribution. The current workbench at the repository root remains separate.

The import excludes `enterprise/`, the upstream docs archive, docs app and evals. It includes the Apache-2.0 `LICENSE`, `NOTICE`, `LICENSING.md`, and bundled `third_party/` notices. The original upstream README is kept as `UPSTREAM-README.md` for attribution and developer context. Upstream source: `https://github.com/milind-soni/OpenMausBot`.

## Local development

Use Node 24 and pnpm 10.33.0. Install with `pnpm install --frozen-lockfile`. The current machine reuses the existing upstream checkout's `node_modules` through an ignored local symlink; a clean checkout must run its own install. Build with `NODE_OPTIONS=--max-old-space-size=4096 pnpm build` on this 8 GB machine.

For isolated fake-engine verification, follow `AGENTS.md` and the upstream `docs/verification/README.md` in the reference checkout. Launch `node --experimental-strip-types scripts/control-omb.ts launch` from this directory, use the printed explicit URL with `pnpm control:omb`, and stop the launcher to remove its fixture state. Never point verification at the owner's live service or import their key into a test.

Current evidence and remaining gates: `../docs/ACCEPTANCE.md` and `../docs/OPENMAUSBOT-PIVOT.md`.
