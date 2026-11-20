"""Offline private state backup and verified restore.

The archive deliberately includes the local encryption key and pairing token. Keep it
private; it is not a scrubbed export for sharing.
"""
import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import sqlite3
import stat
import tempfile

FORMAT = 1
MAX_SCHEMA_VERSION = 1
ACTIVE = {"queued", "running", "approval", "paused"}


def _private_file(path):
    try:
        info = path.lstat()
    except FileNotFoundError as error:
        raise ValueError(f"Backup file is missing: {path.name}") from error
    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
        raise ValueError(f"Expected a private regular file: {path.name}")
    return path


def _digest(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _offline():
    for port in (8765, 8766):
        with socket.socket() as probe:
            if probe.connect_ex(("127.0.0.1", port)) == 0:
                raise ValueError("Stop the Desk Yantra app and companion before backup or restore")


def _objects(db, kind):
    return [json.loads(row[0]) for row in db.execute("SELECT body FROM objects WHERE kind=?", (kind,))]


def _validate_db(db):
    if db.execute("PRAGMA user_version").fetchone()[0] > MAX_SCHEMA_VERSION:
        raise ValueError("Backup schema is newer than this Desk Yantra build")
    if db.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
        raise ValueError("SQLite integrity check failed")
    active = [item["id"] for item in _objects(db, "runs") if item.get("status") in ACTIVE]
    if active:
        raise ValueError("Active or review runs must be resolved before backup")


def _copy_private(source, destination):
    _private_file(source)
    shutil.copyfile(source, destination)
    destination.chmod(0o600)


def create_backup(source, destination):
    _offline()
    source, destination = Path(source).absolute(), Path(destination).absolute()
    if destination.exists() or destination.is_symlink():
        raise ValueError("Backup destination already exists")
    if destination.is_relative_to(source) or source.is_relative_to(destination):
        raise ValueError("Backup destination must be separate from state")
    if not source.is_dir() or source.is_symlink():
        raise ValueError("State directory is unavailable or linked")
    original = sqlite3.connect(f"file:{source / 'workbench.db'}?mode=ro", uri=True)
    _validate_db(original)
    with tempfile.TemporaryDirectory(prefix=".desk-yantra-backup-", dir=destination.parent) as temporary:
        stage = Path(temporary)
        stage.chmod(0o700)
        for name in ("token", "encryption.key"):
            _copy_private(source / name, stage / name)
        snapshot = sqlite3.connect(stage / "workbench.db")
        original.backup(snapshot)
        snapshot.close()
        (stage / "workbench.db").chmod(0o600)
        snapshot = sqlite3.connect(stage / "workbench.db")
        _validate_db(snapshot)
        artifacts = _objects(snapshot, "artifacts")
        (stage / "artifacts").mkdir(mode=0o700)
        copied = set()
        for item in artifacts:
            path = Path(item["path"])
            if path.parent != source / "artifacts" or path.name in copied or (source / "artifacts").is_symlink():
                raise ValueError("Artifact record has an unsafe or duplicate path")
            _copy_private(path, stage / "artifacts" / path.name)
            copied.add(path.name)
        snapshot.close()
        names = ["token", "encryption.key", "workbench.db"] + [f"artifacts/{name}" for name in sorted(copied)]
        manifest = {"format": FORMAT, "files": {name: _digest(stage / name) for name in names}, "artifact_count": len(artifacts)}
        (stage / "manifest.json").write_text(json.dumps(manifest, sort_keys=True, indent=2) + "\n")
        (stage / "manifest.json").chmod(0o600)
        verify_backup(stage)
        os.rename(stage, destination)
    original.close()
    return manifest


def verify_backup(source):
    """Check the complete private archive without writing or restoring it."""
    source = Path(source).absolute()
    if source.is_symlink() or not source.is_dir() or (source / "artifacts").is_symlink():
        raise ValueError("Invalid backup directory")
    manifest_path = _private_file(source / "manifest.json")
    manifest = json.loads(manifest_path.read_text())
    if manifest.get("format") != FORMAT or not isinstance(manifest.get("files"), dict):
        raise ValueError("Unsupported backup format")
    names = manifest["files"]
    if not {"token", "encryption.key", "workbench.db"}.issubset(names):
        raise ValueError("Backup is incomplete")
    present = {path.relative_to(source).as_posix() for path in source.rglob("*") if path.is_file() or path.is_symlink()}
    if present != set(names) | {"manifest.json"}:
        raise ValueError("Backup contains missing or unlisted files")
    for name, digest in names.items():
        path = source / name
        if name not in ("token", "encryption.key", "workbench.db") and (not name.startswith("artifacts/") or Path(name).parts != ("artifacts", Path(name).name)):
            raise ValueError("Unsafe backup path")
        if not isinstance(digest, str) or len(digest) != 64 or _digest(_private_file(path)) != digest:
            raise ValueError("Backup checksum mismatch")
    try:
        db = sqlite3.connect(f"file:{source / 'workbench.db'}?mode=ro&immutable=1", uri=True)
        try:
            _validate_db(db)
            artifacts = _objects(db, "artifacts")
        finally:
            db.close()
    except sqlite3.DatabaseError as error:
        raise ValueError("Backup SQLite database is invalid") from error
    if len(artifacts) != manifest.get("artifact_count"):
        raise ValueError("Artifact count mismatch")
    expected = [f"artifacts/{Path(item['path']).name}" for item in artifacts]
    if len(expected) != len(set(expected)) or set(expected) != set(names) - {"token", "encryption.key", "workbench.db"}:
        raise ValueError("Artifact records do not match backup files")
    return manifest


def restore_backup(source, destination):
    _offline()
    source, destination = Path(source).absolute(), Path(destination).absolute()
    if destination.exists() or destination.is_symlink():
        raise ValueError("Restore destination already exists")
    if destination.is_relative_to(source):
        raise ValueError("Restore destination must be outside the backup")
    manifest = verify_backup(source)
    names = manifest["files"]
    with tempfile.TemporaryDirectory(prefix=".desk-yantra-restore-", dir=destination.parent) as temporary:
        stage = Path(temporary)
        stage.chmod(0o700)
        (stage / "artifacts").mkdir(mode=0o700)
        for name in names:
            _copy_private(source / name, stage / name)
        db = sqlite3.connect(stage / "workbench.db")
        _validate_db(db)
        artifacts = _objects(db, "artifacts")
        if len(artifacts) != manifest.get("artifact_count"):
            raise ValueError("Artifact count mismatch")
        for item in artifacts:
            name = Path(item["path"]).name
            if f"artifacts/{name}" not in names:
                raise ValueError("Artifact is missing from backup")
            item["path"] = str(destination / "artifacts" / name)
            db.execute("UPDATE objects SET body=? WHERE kind='artifacts' AND id=?", (json.dumps(item), item["id"]))
        db.commit()
        db.close()
        os.rename(stage, destination)
    return {"artifact_count": len(artifacts)}
