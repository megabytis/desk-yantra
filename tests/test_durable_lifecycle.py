import time
import uuid
import pytest
from workbench import server
from workbench.store import put, get, touch_heartbeat, get_heartbeat, delete_heartbeat, all_objects


def test_heartbeat_store_operations():
    run_id = str(uuid.uuid4())
    hb = touch_heartbeat(run_id, pid=12345)
    assert hb["id"] == run_id
    assert hb["pid"] == 12345
    assert hb["time"] > 0

    fetched = get_heartbeat(run_id)
    assert fetched is not None
    assert fetched["pid"] == 12345

    delete_heartbeat(run_id)
    assert get_heartbeat(run_id) is None


def test_idempotency_key_deduplication(monkeypatch):
    grant_id = str(uuid.uuid4())
    put("grants", {"id": grant_id, "mode": "host", "root": "/var/tmp", "capabilities": ["files"], "revoked": False})

    agent_id = str(uuid.uuid4())
    put("agents", {"id": agent_id, "name": "Idempotent Agent", "instructions": "", "tools": ["files"], "grants": [grant_id], "archived": False, "connection": "c1", "model": "m1"})

    put("providers", {"id": "c1", "name": "P1", "type": "openai", "url": "http://127.0.0.1:8000/v1", "models": [{"id": "m1"}], "archived": False})

    started_workers = []
    monkeypatch.setattr(server, "start_worker", lambda ident: started_workers.append(ident))

    idem_key = "key-" + str(uuid.uuid4())
    body = {
        "agent": agent_id,
        "grant": grant_id,
        "task": "Test task with idempotency",
        "connection": "c1",
        "model": "m1",
        "idempotency_key": idem_key,
    }

    # First launch creates run
    first_run = server.launch(body)
    assert first_run["idempotency_key"] == idem_key
    assert len(started_workers) == 1

    # Second launch with same idempotency_key returns identical run without starting another worker
    second_run = server.launch(body)
    assert second_run["id"] == first_run["id"]
    assert len(started_workers) == 1


def test_reconcile_runs_catches_expired_leases(monkeypatch):
    run_id = str(uuid.uuid4())
    put("runs", {
        "id": run_id,
        "status": "running",
        "created": time.time() - 100,
    })

    # Put a stale heartbeat (older than 45 seconds lease timeout)
    stale_time = time.time() - 60
    put("heartbeats", {"id": run_id, "time": stale_time, "pid": 999999})

    # Put a pending approval
    approval_id = str(uuid.uuid4())
    put("approvals", {"id": approval_id, "run": run_id, "status": "pending", "action": {"op": "write"}})

    monkeypatch.setattr(server, "companion", lambda path, body, **kwargs: {"stopped": True})
    monkeypatch.setattr(server, "kill_worker", lambda ident: None)

    reconciled = server.reconcile_runs()
    assert run_id in reconciled

    updated_run = get("runs", run_id)
    assert updated_run["status"] in ("review", "failed")
    assert updated_run.get("stop_reason") == "lease_expired"

    # Approval was cancelled
    updated_approval = get("approvals", approval_id)
    assert updated_approval["status"] == "cancelled"


def test_api_reconcile_endpoint(monkeypatch):
    monkeypatch.setattr(server, "reconcile_runs", lambda: ["run-1", "run-2"])
    res = server.api_reconcile()
    assert res["reconciled"] == 2
    assert res["runs"] == ["run-1", "run-2"]

