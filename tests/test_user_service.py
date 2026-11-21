import os
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.render_user_service import ROOT, render_service


def test_user_service_renders_existing_checkout_and_private_state(tmp_path):
    state = tmp_path / "private-state"
    state.mkdir()
    (state / "token").write_text("fixture-token")
    (state / "encryption.key").write_text("fixture-key")
    unit = render_service(state, Path(sys.executable))
    assert f"WorkingDirectory={ROOT}" in unit
    assert f"Environment=PAW_STATE={tmp_path / 'private-state'}" in unit
    assert "Environment=PAW_SERVICE_MODE=1" in unit
    assert f"ExecStart={Path(sys.executable).absolute()} -m workbench" in unit
    assert "KillMode=mixed" in unit
    assert "token" not in unit.lower()


def test_user_service_rejects_ambiguous_paths(tmp_path):
    with pytest.raises(ValueError, match="whitespace"):
        render_service(tmp_path / "state with spaces", Path(sys.executable))
    with pytest.raises(ValueError, match="Existing Desk Yantra private state"):
        render_service(tmp_path / "missing", Path(sys.executable))


def test_token_command_reads_the_selected_private_state(tmp_path):
    state = tmp_path / "state"
    result = subprocess.run([sys.executable, "-m", "workbench", "token"],
                            env=os.environ | {"PAW_STATE": str(state)}, capture_output=True,
                            text=True, timeout=10)
    assert result.returncode == 0
    assert result.stdout.strip() == (state / "token").read_text().strip()
    assert result.stderr == ""
