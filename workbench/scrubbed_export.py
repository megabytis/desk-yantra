"""Metadata-only diagnostic export.

Freeform user and model text cannot be reliably scrubbed with regular expressions.
Only fixed fields and aggregate counts are exported; raw objects stay in state.
"""
from __future__ import annotations

import time
from collections import Counter
from pathlib import Path
from typing import Any

from . import store

EXPORT_SCHEMA_VERSION = 2


def _counts(kind: str, field: str, allowed: frozenset[str]) -> dict[str, int]:
    values = Counter()
    for item in store.all_objects(kind):
        value = item.get(field)
        if isinstance(value, str) and value in allowed:
            values[value] += 1
        else:
            values["unknown"] += 1
    return dict(values)


def create_scrubbed_export(state_path: Path) -> dict[str, Any]:
    from .diagnostics import get_diagnostics_snapshot

    snapshot = get_diagnostics_snapshot(state_path)
    database = snapshot["database"]
    docker = snapshot["docker"]
    return {
        "manifest": {
            "format": "desk-yantra-scrubbed-export",
            "version": EXPORT_SCHEMA_VERSION,
            "exported_at": time.time(),
            "is_scrubbed": True,
            "contents": "aggregate diagnostic metadata only; no names, paths, prompts, URLs, event bodies or artifact metadata",
        },
        "system": {
            "platform": snapshot["system"]["platform"],
            "architecture": snapshot["system"]["architecture"],
            "python_version": snapshot["system"]["python_version"],
        },
        "database": {
            "ready": database.get("ready", False),
            "schema_version": database.get("schema_version"),
            "integrity_ok": database.get("integrity") == "ok",
            "size_bytes": database.get("size_bytes"),
            "objects_count": database.get("objects_count"),
            "events_count": database.get("events_count"),
        },
        "companion_ready": snapshot["companion"]["ready"],
        "docker": {"available": docker.get("available", False), "ready": docker.get("ready", False)},
        "storage": {
            "artifacts_count": snapshot["storage"]["artifacts_count"],
            "artifacts_bytes": snapshot["storage"]["artifacts_bytes"],
        },
        "counts": {
            "providers": len(store.all_objects("providers")),
            "agents": len(store.all_objects("agents")),
            "grants": len(store.all_objects("grants")),
            "artifacts": len(store.all_objects("artifacts")),
            "runs_by_status": _counts("runs", "status", frozenset({"queued", "running", "approval", "paused", "review", "reviewed", "completed", "failed", "stopped", "cancelled", "interrupted"})),
            "incidents_by_category": _counts("incidents", "category", frozenset({"timeout", "tool_budget", "auth", "rate_limit", "crash", "command_failure", "inference_error", "system"})),
        },
    }
