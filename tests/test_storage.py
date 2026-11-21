import os
import subprocess
import sys
import time

import pytest

from workbench import storage


def test_prune_only_old_unreferenced_private_files(tmp_path, monkeypatch):
    root = tmp_path / "artifacts"
    root.mkdir()
    kept = root / "kept"
    kept.write_bytes(b"saved")
    old = root / "orphan-old"
    old.write_bytes(b"unused")
    fresh = root / "orphan-fresh"
    fresh.write_bytes(b"new")
    link = root / "link"
    link.symlink_to(old)
    os.utime(old, (time.time() - 40 * 86400,) * 2)
    records = [{"id": "kept", "path": str(kept)}]
    report = storage.inspect_artifacts(tmp_path, records, older_than_days=30)
    assert report["referenced_count"] == 1
    assert report["orphan_count"] == 1
    assert report["orphan_bytes"] == len(b"unused")
    assert report["skipped_entries"] == 1
    monkeypatch.setattr("workbench.backup._offline", lambda: None)
    with pytest.raises(ValueError, match="Stop active"):
        storage.prune_artifacts(tmp_path, records, [{"status": "review"}], 30)
    result = storage.prune_artifacts(tmp_path, records, [{"status": "completed"}], 30)
    assert result == {"removed_count": 1, "removed_bytes": len(b"unused")}
    assert kept.read_bytes() == b"saved"
    assert fresh.read_bytes() == b"new"
    assert link.is_symlink()
    assert not old.exists()


def test_storage_cli_previews_before_applying(tmp_path):
    state = tmp_path / "private-state"
    environment = os.environ | {"PAW_STATE": str(state)}
    initial = subprocess.run([sys.executable, "-m", "workbench", "storage"], env=environment,
                             capture_output=True, text=True, timeout=10)
    assert initial.returncode == 0
    root = state / "artifacts"
    root.mkdir()
    orphan = root / "old-orphan"
    orphan.write_bytes(b"unused")
    os.utime(orphan, (time.time() - 40 * 86400,) * 2)
    preview = subprocess.run([sys.executable, "-m", "workbench", "prune-artifacts"], env=environment,
                             capture_output=True, text=True, timeout=10)
    assert preview.returncode == 0 and "Preview only" in preview.stdout
    assert orphan.exists()
    applied = subprocess.run([sys.executable, "-m", "workbench", "prune-artifacts", "--apply"], env=environment,
                             capture_output=True, text=True, timeout=10)
    assert applied.returncode == 0 and "Removed 1 files" in applied.stdout
    assert not orphan.exists()
