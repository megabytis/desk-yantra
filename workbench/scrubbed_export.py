"""Scrubbed diagnostic and configuration export/import.

Completely sanitizes secrets, tokens, private keys, passwords, and user paths
for secure diagnostic sharing or template migration without compromising host security.
"""
from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any, Dict, List

from .store import all_objects, sensitive_values, redact

EXPORT_SCHEMA_VERSION = 1


def scrub_value(val: Any) -> Any:
    if isinstance(val, str):
        val = redact(val)
        val = re.sub(r"(Bearer\s+)[a-zA-Z0-9_\-\./]{15,}", r"\1[SCRUBBED_TOKEN]", val)
        val = re.sub(r"(sk-[a-zA-Z0-9]{15,})", "[SCRUBBED_API_KEY]", val)
        val = re.sub(r"/home/[a-zA-Z0-9_\-\.]+", "/home/<user>", val)
        return val
    elif isinstance(val, dict):
        scrubbed = {}
        for k, v in val.items():
            if k in ("secret", "api_key", "password", "token", "encryption_key", "key"):
                scrubbed[k] = "[SCRUBBED]"
            else:
                scrubbed[k] = scrub_value(v)
        return scrubbed
    elif isinstance(val, list):
        return [scrub_value(item) for item in val]
    return val


def create_scrubbed_export(state_path: Path) -> Dict[str, Any]:
    from .diagnostics import get_diagnostics_snapshot

    providers = []
    for p in all_objects("providers"):
        sanitized = dict(p)
        sanitized.pop("secret", None)
        sanitized.pop("api_key", None)
        sanitized["has_key"] = bool(p.get("has_key") or p.get("secret"))
        providers.append(scrub_value(sanitized))

    agents = [scrub_value(a) for a in all_objects("agents")]
    grants = [scrub_value(g) for g in all_objects("grants")]
    runs = [scrub_value(r) for r in all_objects("runs")]
    incidents = [scrub_value(i) for i in all_objects("incidents")]

    artifacts = []
    for a in all_objects("artifacts"):
        artifacts.append({
            "id": a.get("id"),
            "name": a.get("name"),
            "mime": a.get("mime"),
            "size": a.get("size"),
            "run": a.get("run"),
            "created_at": a.get("created_at"),
        })

    snapshot = get_diagnostics_snapshot(state_path)

    return {
        "manifest": {
            "format": "desk-yantra-scrubbed-export",
            "version": EXPORT_SCHEMA_VERSION,
            "exported_at": time.time(),
            "is_scrubbed": True,
        },
        "diagnostics": scrub_value(snapshot),
        "providers": providers,
        "agents": agents,
        "grants": grants,
        "runs": runs,
        "incidents": incidents,
        "artifacts_metadata": artifacts,
    }
