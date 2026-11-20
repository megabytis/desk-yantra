import json
import sqlite3
import uuid
from pathlib import Path
import pytest
from workbench.backup import create_backup, restore_backup


def state_fixture(root):
    root.mkdir(mode=0o700)
    (root / "artifacts").mkdir(mode=0o700)
    (root / "token").write_text("private-token")
    (root / "encryption.key").write_text("private-key")
    ident = str(uuid.uuid4())
    artifact = root / "artifacts" / ident
    artifact.write_bytes(b"actual artifact")
    db = sqlite3.connect(root / "workbench.db")
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("CREATE TABLE objects (kind TEXT, id TEXT, body TEXT, PRIMARY KEY(kind,id))")
    db.execute("CREATE TABLE events (seq INTEGER PRIMARY KEY AUTOINCREMENT, run TEXT, time REAL, kind TEXT, body TEXT)")
    db.execute("INSERT INTO objects VALUES (?,?,?)", ("artifacts", ident, json.dumps({"id": ident, "run": ident, "name": "result.txt", "path": str(artifact)})))
    db.execute("INSERT INTO objects VALUES (?,?,?)", ("runs", ident, json.dumps({"id": ident, "status": "completed"})))
    db.execute("INSERT INTO events (run,time,kind,body) VALUES (?,?,?,?)", (ident, 1, "result", json.dumps({"value": "preserved"})))
    db.commit()
    db.close()
    return ident


def test_private_backup_restores_database_and_artifact_paths(tmp_path):
    source, archive, restored = (tmp_path / name for name in ("source", "archive", "restored"))
    ident = state_fixture(source)
    manifest = create_backup(source, archive)
    assert manifest["artifact_count"] == 1
    assert (archive / "token").read_text() == "private-token"
    assert (archive / "workbench.db").stat().st_mode & 0o077 == 0
    assert restore_backup(archive, restored) == {"artifact_count": 1}
    db = sqlite3.connect(restored / "workbench.db")
    artifact = json.loads(db.execute("SELECT body FROM objects WHERE kind='artifacts'").fetchone()[0])
    assert artifact["path"] == str(restored / "artifacts" / ident)
    assert Path(artifact["path"]).read_bytes() == b"actual artifact"
    assert db.execute("SELECT kind FROM events").fetchone()[0] == "result"
    db.close()
    with pytest.raises(ValueError, match="already exists"):
        restore_backup(archive, restored)


def test_backup_detects_tampering_and_active_runs(tmp_path):
    source, archive = tmp_path / "source", tmp_path / "archive"
    ident = state_fixture(source)
    db = sqlite3.connect(source / "workbench.db")
    db.execute("UPDATE objects SET body=? WHERE kind='runs'", (json.dumps({"id": ident, "status": "running"}),))
    db.commit()
    db.close()
    with pytest.raises(ValueError, match="Active"):
        create_backup(source, archive)
    assert not archive.exists()
    db = sqlite3.connect(source / "workbench.db")
    db.execute("UPDATE objects SET body=? WHERE kind='runs'", (json.dumps({"id": ident, "status": "completed"}),))
    db.commit()
    db.close()
    create_backup(source, archive)
    (archive / "artifacts" / ident).write_bytes(b"tampered")
    with pytest.raises(ValueError, match="checksum"):
        restore_backup(archive, tmp_path / "restored")
    assert not (tmp_path / "restored").exists()


def test_backup_restore_cli_does_not_initialize_restore_target(tmp_path):
    import os
    import subprocess
    import sys

    source, archive, restored = (tmp_path / name for name in ("source", "archive", "restored"))
    state_fixture(source)
    env = os.environ | {"PAW_STATE": str(source)}
    made = subprocess.run([sys.executable, "-m", "workbench", "backup", str(archive)], env=env, capture_output=True, text=True)
    assert made.returncode == 0, made.stderr
    env["PAW_STATE"] = str(restored)
    loaded = subprocess.run([sys.executable, "-m", "workbench", "restore", str(archive)], env=env, capture_output=True, text=True)
    assert loaded.returncode == 0, loaded.stderr
    assert (restored / "token").read_text() == "private-token"


def test_backup_rejects_linked_source_and_artifact(tmp_path):
    source, archive = tmp_path / "source", tmp_path / "archive"
    ident = state_fixture(source)
    (source / "artifacts" / ident).unlink()
    (source / "artifacts" / ident).symlink_to(source / "token")
    with pytest.raises(ValueError, match="private regular file"):
        create_backup(source, archive)
    assert not archive.exists()
    linked = tmp_path / "linked"
    linked.symlink_to(source, target_is_directory=True)
    with pytest.raises(ValueError, match="linked"):
        create_backup(linked, archive)
