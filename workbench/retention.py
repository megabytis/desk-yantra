"""Log and run event retention policies."""
from __future__ import annotations

import time
import json
from typing import Any, Dict

from . import store

TERMINAL_STATUSES = {"completed", "failed", "stopped"}
PRUNEABLE_KINDS = ("terminal",)


def inspect_retention(older_than_days: int = 30, now: float | None = None) -> Dict[str, Any]:
    if older_than_days < 1:
        raise ValueError("Retention period must be at least 1 day")
    cutoff = (time.time() if now is None else now) - (older_than_days * 86400)

    runs = store.all_objects("runs")
    eligible_run_ids = []
    for run in runs:
        if run.get("status") in TERMINAL_STATUSES:
            t = run.get("finished_at") or run.get("created_at") or 0
            if t <= cutoff:
                eligible_run_ids.append(run["id"])

    with store.LOCK:
        if not eligible_run_ids:
            return {
                "cutoff_days": older_than_days,
                "eligible_runs_count": 0,
                "pruneable_events_count": 0,
                "eligible_run_ids": [],
            }
        placeholders = ",".join("?" for _ in eligible_run_ids)
        row = store.DB.execute(
            f"SELECT count(*) FROM events WHERE run IN ({placeholders}) AND kind IN (?)", [*eligible_run_ids, *PRUNEABLE_KINDS]
        ).fetchone()
        pruneable = row[0] if row else 0

    return {
        "cutoff_days": older_than_days,
        "eligible_runs_count": len(eligible_run_ids),
        "pruneable_events_count": pruneable,
        "eligible_run_ids": eligible_run_ids,
    }


def prune_retention(older_than_days: int = 30, now: float | None = None) -> Dict[str, Any]:
    report = inspect_retention(older_than_days, now=now)
    run_ids = report["eligible_run_ids"]
    if not run_ids:
        return {"pruned_events": 0, "affected_runs": 0}

    with store.LOCK:
        # Recheck under the same database lock as deletion; a run may have
        # entered review since the preview was built.
        current_ids = []
        for run_id in run_ids:
            row = store.DB.execute("SELECT body FROM objects WHERE kind='runs' AND id=?", (run_id,)).fetchone()
            if row and json.loads(row[0]).get("status") in TERMINAL_STATUSES:
                current_ids.append(run_id)
        if not current_ids:
            return {"pruned_events": 0, "affected_runs": 0}
        placeholders = ",".join("?" for _ in current_ids)
        cursor = store.DB.execute(f"DELETE FROM events WHERE run IN ({placeholders}) AND kind IN (?)", [*current_ids, *PRUNEABLE_KINDS])
        pruned = cursor.rowcount
        store.DB.commit()

    return {"pruned_events": pruned, "affected_runs": len(current_ids)}
