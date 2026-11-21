"""Inspect private artifact usage and optionally remove old unreferenced files."""
import os
import stat
import time
from pathlib import Path


ACTIVE = {"queued", "running", "approval", "paused", "review"}


def inspect_artifacts(state: Path, records: list[dict], older_than_days: int = 30, now: float | None = None) -> dict:
    if older_than_days < 1:
        raise ValueError("Retention period must be at least one day")
    root = state / "artifacts"
    if root.is_symlink():
        raise ValueError("Artifact directory must not be a symlink")
    references = {Path(item["path"]).name for item in records if Path(item["path"]).parent == root}
    cutoff = (time.time() if now is None else now) - older_than_days * 86400
    candidates = []
    referenced_bytes = 0
    skipped = 0
    for path in root.iterdir() if root.is_dir() else ():
        info = path.lstat()
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            skipped += 1
            continue
        if path.name in references:
            referenced_bytes += info.st_size
        elif info.st_mtime <= cutoff:
            candidates.append({"name": path.name, "size": info.st_size, "inode": info.st_ino, "mtime_ns": info.st_mtime_ns})
    return {"referenced_count": len(references), "referenced_bytes": referenced_bytes,
            "orphan_count": len(candidates), "orphan_bytes": sum(item["size"] for item in candidates),
            "skipped_entries": skipped, "candidates": candidates}


def prune_artifacts(state: Path, records: list[dict], runs: list[dict], older_than_days: int = 30) -> dict:
    from .backup import _offline
    _offline()
    if any(run.get("status") in ACTIVE for run in runs):
        raise ValueError("Stop active and review runs before pruning artifacts")
    report = inspect_artifacts(state, records, older_than_days)
    root = state / "artifacts"
    removed = 0
    bytes_removed = 0
    for item in report["candidates"]:
        path = root / item["name"]
        info = path.lstat()
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or (info.st_ino, info.st_size, info.st_mtime_ns) != (item["inode"], item["size"], item["mtime_ns"]):
            continue
        os.unlink(path)
        removed += 1
        bytes_removed += info.st_size
    return {"removed_count": removed, "removed_bytes": bytes_removed}
