"""Render a systemd user service for this checkout without installing it."""
import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def render_service(state: Path, python: Path) -> str:
    state = state.expanduser().resolve()
    # Keep the virtualenv path: resolving its Python symlink would bypass the venv.
    python = python.expanduser().absolute()
    for path in (ROOT, state, python):
        if any(character.isspace() for character in str(path)) or "%" in str(path):
            raise ValueError("Service paths cannot contain whitespace or %")
    if not state.is_dir() or not (state / "token").is_file() or not (state / "encryption.key").is_file():
        raise ValueError(f"Existing Desk Yantra private state not found: {state}")
    if not python.is_file():
        raise ValueError(f"Python interpreter not found: {python}")
    return f"""[Unit]
Description=Desk Yantra personal agent
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory={ROOT}
Environment=PAW_STATE={state}
Environment=PAW_SERVICE_MODE=1
ExecStart={python} -m workbench
Restart=on-failure
RestartSec=3
TimeoutStopSec=120
KillMode=mixed
UMask=0077

[Install]
WantedBy=default.target
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state", type=Path, default=ROOT / ".state", help="Existing private state path; defaults to this checkout's .state")
    parser.add_argument("--python", type=Path, default=ROOT / ".venv" / "bin" / "python", help="Locked project Python interpreter")
    args = parser.parse_args()
    try:
        sys.stdout.write(render_service(args.state, args.python))
    except ValueError as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()
