import json
import time
import uuid
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from workbench import diagnostics, incidents, metrics, retention, scrubbed_export, server, store


@pytest.fixture
def clean_state(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "STATE", tmp_path)
    # re-init database
    import sqlite3
    db = sqlite3.connect(tmp_path / "workbench.db", check_same_thread=False)
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA user_version = 1")
    db.execute("CREATE TABLE IF NOT EXISTS objects (kind TEXT, id TEXT, body TEXT, PRIMARY KEY(kind,id))")
    db.execute("CREATE TABLE IF NOT EXISTS events (seq INTEGER PRIMARY KEY AUTOINCREMENT, run TEXT, time REAL, kind TEXT, body TEXT)")
    db.execute("CREATE INDEX IF NOT EXISTS events_run_sequence ON events(run,seq)")
    monkeypatch.setattr(store, "DB", db)
    token_file = tmp_path / "token"
    token_file.write_text("test-secret-token")
    monkeypatch.setattr(store, "TOKEN", "test-secret-token")
    monkeypatch.setattr(store, "current_token", lambda: "test-secret-token")
    (tmp_path / "artifacts").mkdir(mode=0o700, exist_ok=True)
    return tmp_path


def test_incident_normalization_and_deduplication(clean_state):
    # Category classification
    assert incidents.classify_category("Operation timed out after 30s") == "timeout"
    assert incidents.classify_category("Tool budget exhausted (max 30 calls)") == "tool_budget"
    assert incidents.classify_category("HTTP 401 Unauthorized accessing model") == "auth"
    assert incidents.classify_category("429 Rate limit exceeded") == "rate_limit"
    assert incidents.classify_category("Worker terminated unexpectedly or crashed") == "crash"
    assert incidents.classify_category("Command failed with exit code 1") == "command_failure"

    # Normalization masks dynamic tokens
    msg1 = "Process timed out after 12.5s at address 0x7fffdeadbeef"
    msg2 = "Process timed out after 30.0s at address 0x7fff12345678"
    norm1 = incidents.normalize_for_signature(msg1)
    norm2 = incidents.normalize_for_signature(msg2)
    assert norm1 == norm2
    assert "<DURATION>" in norm1
    assert "<ADDR>" in norm1

    # Incident recording & deduplication
    inc1 = incidents.record_incident(msg1, run_id="run-1", agent_id="agent-a")
    assert inc1["count"] == 1
    assert inc1["status"] == "detected"
    assert inc1["run_ids"] == ["run-1"]

    # Same normalized error records to the same incident ID
    inc2 = incidents.record_incident(msg2, run_id="run-2", agent_id="agent-a")
    assert inc2["id"] == inc1["id"]
    assert inc2["count"] == 2
    assert inc2["run_ids"] == ["run-1", "run-2"]
    assert inc2["latest_run_id"] == "run-2"

    # Acknowledgment
    acked = incidents.ack_incident(inc1["id"])
    assert acked["status"] == "acknowledged"
    assert acked["acknowledged_at"] > 0

    # Resolving
    resolved = incidents.resolve_incident(inc1["id"])
    assert resolved["status"] == "resolved"
    assert resolved["resolved_at"] > 0

    # Repeat of resolved incident re-opens it to detected
    inc3 = incidents.record_incident(msg1, run_id="run-3")
    assert inc3["id"] == inc1["id"]
    assert inc3["count"] == 3
    assert inc3["status"] == "detected"
    assert inc3["resolved_at"] is None


def test_diagnostics_snapshot(clean_state):
    # Put sample objects
    store.put("agents", {"id": "ag1", "name": "Agent 1"})
    store.put("runs", {"id": "r1", "status": "running"})
    incidents.record_incident("Sample crash failure", category="crash", run_id="r1")

    snapshot = diagnostics.get_diagnostics_snapshot(clean_state)
    assert snapshot["system"]["platform"]
    assert snapshot["database"]["ready"] is True
    assert snapshot["database"]["schema_version"] == 1
    assert snapshot["database"]["integrity"] == "ok"
    assert snapshot["database"]["objects_count"] >= 2
    assert snapshot["workload"]["active_runs_count"] == 1
    assert snapshot["incidents"]["active_count"] == 1
    assert len(snapshot["incidents"]["recent"]) == 1


def test_companion_diagnostic_uses_current_bearer_token(clean_state, monkeypatch):
    class HealthyResponse:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, *_):
            return False

    def urlopen(request, timeout):
        assert request.get_header("Authorization") == "Bearer test-secret-token"
        assert timeout == 1.0
        return HealthyResponse()

    monkeypatch.setattr(diagnostics.urllib.request, "urlopen", urlopen)
    assert diagnostics.check_companion_health()["ready"] is True


def test_scrubbed_export_strict_redaction(clean_state):
    # Store provider with secret and key
    store.put("providers", {
        "id": "prov1",
        "name": "Secret Provider",
        "type": "openai",
        "url": "http://127.0.0.1:11434",
        "secret": store.CIPHER.encrypt(b"fernet-secret-payload").decode(),
        "api_key": "sk-1234567890abcdefghijklmnop",
        "has_key": True,
    })
    store.put("agents", {"id": "ag1", "name": "private-agent-name", "system_prompt": "Bearer test-token-secret-123456789"})
    store.put("grants", {"id": "g1", "mode": "folder", "root": "/home/alice/projects/test"})
    store.put("runs", {"id": "r1", "status": "completed", "task": "unstructured-private-task-string"})
    store.put("incidents", {"id": "i1", "category": "system", "message": "unstructured-private-error-string"})
    store.put("artifacts", {"id": "art1", "name": "output.txt", "path": str(clean_state / "artifacts" / "art1"), "size": 100})

    export_bundle = scrubbed_export.create_scrubbed_export(clean_state)
    json_text = json.dumps(export_bundle)

    # STRICT ASSERTIONS: Secrets and sensitive data must not exist in export
    assert "sk-1234567890abcdefghijklmnop" not in json_text
    assert "fernet-secret-payload" not in json_text
    assert "test-secret-token" not in json_text
    assert "test-token-secret-123456789" not in json_text
    assert "/home/alice" not in json_text
    for private in ("private-agent-name", "unstructured-private-task-string", "unstructured-private-error-string", "output.txt", "prov1", "ag1", "g1", "r1", "/home/<user>"):
        assert private not in json_text
    assert export_bundle["counts"]["providers"] == 1
    assert export_bundle["counts"]["runs_by_status"] == {"completed": 1}
    assert export_bundle["manifest"]["is_scrubbed"] is True
    assert export_bundle["manifest"]["format"] == "desk-yantra-scrubbed-export"
    assert export_bundle["manifest"]["version"] == 2


def test_retention_inspection_and_pruning(clean_state):
    now = 1000000.0
    # Run 1: Old completed run (40 days old)
    old_run = {"id": "old_run", "status": "completed", "created_at": now - (40 * 86400)}
    store.put("runs", old_run)
    store.event("old_run", "terminal", "old output 1")
    store.event("old_run", "terminal", "old output 2")
    store.event("old_run", "approval", {"status": "approved"})
    store.event("old_run", "action_started", {"op": "shell"})
    store.event("old_run", "action_finished", {"exit_status": 0})
    store.event("old_run", "verification_contract", {"status": "verified"})

    # Run 2: Recent completed run (5 days old)
    recent_run = {"id": "recent_run", "status": "completed", "created_at": now - (5 * 86400)}
    store.put("runs", recent_run)
    store.event("recent_run", "message", "recent event")

    # Run 3: Active run (40 days old, but running)
    active_run = {"id": "active_run", "status": "running", "created_at": now - (40 * 86400)}
    store.put("runs", active_run)
    store.event("active_run", "message", "active event")

    report = retention.inspect_retention(older_than_days=30, now=now)
    assert report["eligible_runs_count"] == 1
    assert report["eligible_run_ids"] == ["old_run"]
    assert report["pruneable_events_count"] == 2

    prune_res = retention.prune_retention(older_than_days=30, now=now)
    assert prune_res["pruned_events"] == 2
    assert prune_res["affected_runs"] == 1

    # Events for old run pruned
    assert [e["kind"] for e in store.events("old_run")] == ["approval", "action_started", "action_finished", "verification_contract"]
    # Events for recent run and active run preserved
    assert len(store.events("recent_run")) == 1
    assert len(store.events("active_run")) == 1
    # Run objects themselves preserved!
    assert store.get("runs", "old_run")["id"] == "old_run"


def test_retention_keeps_review_and_interrupted_evidence(clean_state):
    now = 1000000.0
    for status in ("review", "interrupted", "reviewed", "running"):
        store.put("runs", {"id": status, "status": status, "created_at": now - 40 * 86400})
        store.event(status, "terminal", "potentially uncertain output")
    report = retention.inspect_retention(now=now)
    assert report["eligible_run_ids"] == []
    assert retention.prune_retention(now=now)["pruned_events"] == 0


def test_retention_rechecks_run_status_before_deletion(clean_state, monkeypatch):
    now = 1000000.0
    store.put("runs", {"id": "old", "status": "completed", "created_at": now - 40 * 86400})
    store.event("old", "terminal", "keep during review")
    original = retention.inspect_retention

    def changed_status(*args, **kwargs):
        preview = original(*args, **kwargs)
        store.put("runs", {"id": "old", "status": "review", "created_at": now - 40 * 86400})
        return preview

    monkeypatch.setattr(retention, "inspect_retention", changed_status)
    assert retention.prune_retention(now=now)["pruned_events"] == 0
    assert len(store.events("old")) == 1


def test_metrics_telemetry(clean_state):
    store.put("runs", {"id": "r1", "status": "completed", "stop_reason": "completed"})
    store.put("runs", {"id": "r2", "status": "failed", "stop_reason": "timeout"})
    store.event("r1", "tool", {"op": "read"})
    store.event("r2", "tool_error", "timeout")
    incidents.record_incident("timeout error", category="timeout", run_id="r2")

    m = metrics.get_metrics()
    assert m["runs"]["total"] == 2
    assert m["runs"]["by_status"]["completed"] == 1
    assert m["runs"]["by_status"]["failed"] == 1
    assert m["runs"]["by_stop_reason"]["timeout"] == 1
    assert m["events"]["tool_calls_total"] == 1
    assert m["events"]["tool_errors_total"] == 1
    assert m["incidents"]["total"] == 1
    assert m["incidents"]["by_category"]["timeout"] == 1


def test_server_diagnostic_endpoints(clean_state):
    client = TestClient(server.app)
    # Without cookie -> 401
    assert client.get("/api/diagnostics").status_code == 401

    cookies = {"paw": "test-secret-token"}
    headers = {"X-PAW": "1"}

    # Diagnostics endpoint
    resp = client.get("/api/diagnostics", cookies=cookies)
    assert resp.status_code == 200
    data = resp.json()
    assert data["database"]["ready"] is True

    # Incidents list & ack
    inc = incidents.record_incident("Critical crash in worker", category="crash")
    list_resp = client.get("/api/incidents", cookies=cookies)
    assert list_resp.status_code == 200
    assert any(item["id"] == inc["id"] for item in list_resp.json())

    ack_resp = client.post(f"/api/incidents/{inc['id']}/ack", cookies=cookies, headers=headers)
    assert ack_resp.status_code == 200
    assert ack_resp.json()["status"] == "acknowledged"

    # Scrubbed export endpoint
    export_resp = client.get("/api/export/scrubbed", cookies=cookies)
    assert export_resp.status_code == 200
    assert "attachment" in export_resp.headers.get("content-disposition", "")
    export_data = export_resp.json()
    assert export_data["manifest"]["is_scrubbed"] is True

    # Retention endpoints
    ret_resp = client.get("/api/retention/status", cookies=cookies)
    assert ret_resp.status_code == 200
    assert "pruneable_events_count" in ret_resp.json()

    prune_resp = client.post("/api/retention/prune", json={"older_than_days": 30}, cookies=cookies, headers=headers)
    assert prune_resp.status_code == 200
    assert "pruned_events" in prune_resp.json()

    # Metrics endpoint
    met_resp = client.get("/api/metrics", cookies=cookies)
    assert met_resp.status_code == 200
    assert "runs" in met_resp.json()
