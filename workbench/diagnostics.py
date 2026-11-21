"""System readiness and diagnostic snapshot."""
from __future__ import annotations

import os
import platform
import shutil
import sqlite3
import subprocess
import sys
import time
import urllib.request
from pathlib import Path
from typing import Any, Dict

from .store import all_objects


SERVER_START_TIME = time.time()


def check_sqlite_health(db_path: Path) -> Dict[str, Any]:
    if not db_path.exists():
        return {"ready": False, "reason": "Database file missing"}
    try:
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        try:
            ver = conn.execute("PRAGMA user_version").fetchone()[0]
            integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
            objects_count = conn.execute("SELECT count(*) FROM objects").fetchone()[0]
            events_count = conn.execute("SELECT count(*) FROM events").fetchone()[0]
            kind_counts = dict(conn.execute("SELECT kind, count(*) FROM objects GROUP BY kind").fetchall())
        finally:
            conn.close()
        return {
            "ready": integrity == "ok",
            "schema_version": ver,
            "integrity": integrity,
            "size_bytes": os.path.getsize(db_path),
            "objects_count": objects_count,
            "events_count": events_count,
            "kind_counts": kind_counts,
        }
    except Exception as e:
        return {"ready": False, "error": str(e)}


def check_companion_health() -> Dict[str, Any]:
    try:
        req = urllib.request.Request("http://127.0.0.1:8766/healthz", headers={"X-PAW": "1"})
        with urllib.request.urlopen(req, timeout=1.0) as resp:
            if resp.status == 200:
                return {"ready": True, "status": "online"}
    except Exception:
        pass
    return {"ready": False, "status": "offline"}


def check_docker_health() -> Dict[str, Any]:
    docker_bin = shutil.which("docker")
    if not docker_bin:
        return {"available": False, "ready": False, "reason": "docker CLI not in PATH"}
    try:
        res = subprocess.run([docker_bin, "info", "--format", "{{.ServerVersion}}"], capture_output=True, text=True, timeout=2.0)
        if res.returncode == 0:
            version = res.stdout.strip()
            return {"available": True, "ready": True, "version": version, "status": f"Docker {version} running"}
        return {"available": True, "ready": False, "reason": res.stderr.strip() or "Docker daemon not responding"}
    except subprocess.TimeoutExpired:
        return {"available": True, "ready": False, "reason": "Docker daemon probe timed out"}
    except Exception as e:
        return {"available": False, "ready": False, "reason": str(e)}


def get_diagnostics_snapshot(state_path: Path) -> Dict[str, Any]:
    uptime = time.time() - SERVER_START_TIME
    db_path = state_path / "workbench.db"
    artifacts_dir = state_path / "artifacts"

    artifact_count = 0
    artifact_bytes = 0
    if artifacts_dir.is_dir() and not artifacts_dir.is_symlink():
        for item in artifacts_dir.iterdir():
            if item.is_file() and not item.is_symlink():
                artifact_count += 1
                artifact_bytes += item.stat().st_size

    incidents = all_objects("incidents")
    active_incidents = [i for i in incidents if i.get("status") in ("detected", "acknowledged")]

    runs = all_objects("runs")
    active_runs = [r for r in runs if r.get("status") in ("queued", "running", "approval", "review")]

    return {
        "system": {
            "platform": sys.platform,
            "architecture": platform.machine(),
            "os_release": platform.release(),
            "python_version": platform.python_version(),
            "uptime_seconds": round(uptime, 2),
            "pid": os.getpid(),
        },
        "database": check_sqlite_health(db_path),
        "companion": check_companion_health(),
        "docker": check_docker_health(),
        "storage": {
            "state_path": str(state_path),
            "artifacts_count": artifact_count,
            "artifacts_bytes": artifact_bytes,
        },
        "workload": {
            "active_runs_count": len(active_runs),
            "total_runs_count": len(runs),
        },
        "incidents": {
            "active_count": len(active_incidents),
            "total_count": len(incidents),
            "recent": incidents[:10],
        },
    }
