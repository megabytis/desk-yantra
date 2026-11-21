"""Telemetry metrics aggregation for Desk Yantra."""
from __future__ import annotations

import time
from typing import Any, Dict
from . import store


def get_metrics() -> Dict[str, Any]:
    runs = store.all_objects("runs")
    incidents = store.all_objects("incidents")
    artifacts = store.all_objects("artifacts")

    status_counts: Dict[str, int] = {}
    stop_reasons: Dict[str, int] = {}
    for r in runs:
        s = r.get("status", "unknown")
        status_counts[s] = status_counts.get(s, 0) + 1
        sr = r.get("stop_reason")
        if sr:
            stop_reasons[sr] = stop_reasons.get(sr, 0) + 1

    incident_categories: Dict[str, int] = {}
    for inc in incidents:
        c = inc.get("category", "system")
        incident_categories[c] = incident_categories.get(c, 0) + inc.get("count", 1)

    with store.LOCK:
        total_events = store.DB.execute("SELECT count(*) FROM events").fetchone()[0]
        tool_events = store.DB.execute("SELECT count(*) FROM events WHERE kind='tool'").fetchone()[0]
        tool_errors = store.DB.execute("SELECT count(*) FROM events WHERE kind='tool_error'").fetchone()[0]

    total_artifact_bytes = sum(a.get("size", 0) for a in artifacts)

    return {
        "runs": {
            "total": len(runs),
            "by_status": status_counts,
            "by_stop_reason": stop_reasons,
        },
        "events": {
            "total": total_events,
            "tool_calls_total": tool_events,
            "tool_errors_total": tool_errors,
        },
        "artifacts": {
            "count": len(artifacts),
            "bytes_total": total_artifact_bytes,
        },
        "incidents": {
            "total": len(incidents),
            "by_category": incident_categories,
        },
    }
