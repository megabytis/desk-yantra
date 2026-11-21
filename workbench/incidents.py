"""Structured incident reporting with signature deduplication, redaction, and acknowledgment."""
from __future__ import annotations

import hashlib
import re
import time
from typing import Any, Dict, List, Optional
from .store import all_objects, get, put, redact

INCIDENT_CATEGORIES = (
    "timeout",
    "tool_budget",
    "auth",
    "rate_limit",
    "crash",
    "command_failure",
    "inference_error",
    "system",
)

_CATEGORY_PATTERNS = (
    ("timeout", (r"timeout", r"timed out", r"deadline exceeded")),
    ("tool_budget", (r"tool budget", r"budget exhausted", r"call limit")),
    ("auth", (r"\b401\b", r"unauthorized", r"authentication", r"forbidden", r"\b403\b")),
    ("rate_limit", (r"\b429\b", r"rate limit", r"quota exceeded", r"too many requests")),
    ("crash", (r"worker crash", r"segmentation fault", r"killed", r"sigterm", r"sigkill", r"terminated unexpectedly")),
    ("command_failure", (r"exit code", r"command failed", r"process returned non-zero", r"unresolved command")),
    ("inference_error", (r"model error", r"inference failed", r"provider error", r"connection error")),
)


def classify_category(message: str) -> str:
    lower = message.lower()
    for cat, patterns in _CATEGORY_PATTERNS:
        for pat in patterns:
            if re.search(pat, lower):
                return cat
    return "system"


def normalize_for_signature(message: str) -> str:
    cleaned = redact(message)
    cleaned = re.sub(r"\b\d+(\.\d+)?\s*(s|sec|seconds?|ms|millis?|minutes?)\b", "<DURATION>", cleaned)
    cleaned = re.sub(r"0x[0-9a-fA-F]+", "<ADDR>", cleaned)
    cleaned = re.sub(r"\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}(\.\d+)?", "<TIMESTAMP>", cleaned)
    cleaned = re.sub(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", "<UUID>", cleaned)
    return " ".join(cleaned.split()[:50])


def compute_signature(category: str, normalized_message: str) -> str:
    raw = f"{category}:{normalized_message}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def record_incident(
    message: str,
    category: Optional[str] = None,
    run_id: Optional[str] = None,
    agent_id: Optional[str] = None,
    traceback_text: Optional[str] = None,
) -> Dict[str, Any]:
    redacted_msg = redact(str(message))
    if not category:
        category = classify_category(redacted_msg)

    norm = normalize_for_signature(redacted_msg)
    sig = compute_signature(category, norm)
    incident_id = f"inc_{sig}"

    existing = None
    try:
        existing = get("incidents", incident_id)
    except (KeyError, ValueError):
        pass

    now = time.time()
    if existing:
        existing["count"] = existing.get("count", 1) + 1
        existing["last_seen_at"] = now
        existing["latest_run_id"] = run_id
        if run_id:
            run_ids = existing.setdefault("run_ids", [])
            if run_id not in run_ids:
                run_ids.append(run_id)
        if traceback_text:
            existing["traceback"] = redact(traceback_text[-2000:])
        if existing.get("status") == "resolved":
            existing["status"] = "detected"
            existing["resolved_at"] = None
        put("incidents", existing)
        return existing

    incident = {
        "id": incident_id,
        "signature": sig,
        "category": category,
        "status": "detected",
        "message": redacted_msg[:1000],
        "normalized": norm,
        "run_id": run_id,
        "run_ids": [run_id] if run_id else [],
        "latest_run_id": run_id,
        "agent_id": agent_id,
        "traceback": redact(traceback_text[-2000:]) if traceback_text else None,
        "count": 1,
        "first_seen_at": now,
        "last_seen_at": now,
        "resolved_at": None,
    }
    put("incidents", incident)
    return incident


def list_incidents(status: Optional[str] = None) -> List[Dict[str, Any]]:
    items = all_objects("incidents")
    if status:
        items = [i for i in items if i.get("status") == status]
    return sorted(items, key=lambda x: x.get("last_seen_at", 0), reverse=True)


def ack_incident(incident_id: str) -> Dict[str, Any]:
    incident = get("incidents", incident_id)
    incident["status"] = "acknowledged"
    incident["acknowledged_at"] = time.time()
    put("incidents", incident)
    return incident


def resolve_incident(incident_id: str) -> Dict[str, Any]:
    incident = get("incidents", incident_id)
    incident["status"] = "resolved"
    incident["resolved_at"] = time.time()
    put("incidents", incident)
    return incident
