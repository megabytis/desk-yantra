import time
import uuid
import pytest
from workbench.store import put, get, transition_run
from workbench.worker import WorkExecutor, WorkAction
from workbench import server


def test_work_executor_wall_time_budget_exhaustion():
    grant_id = str(uuid.uuid4())
    put("grants", {"id": grant_id, "mode": "host", "root": "/var/tmp", "capabilities": ["files"], "revoked": False})
    
    agent_id = str(uuid.uuid4())
    put("agents", {"id": agent_id, "name": "Budget Agent", "instructions": "", "tools": ["files"], "grants": [grant_id], "archived": False})

    run_id = str(uuid.uuid4())
    run = {
        "id": run_id,
        "agent": agent_id,
        "grant": grant_id,
        "status": "running",
        "tools": ["read"],
        "wall_time_limit": 0.05,
        "created": time.time(),
        "root_run": run_id,
    }
    put("runs", run)

    executor = WorkExecutor(run_id)
    # Simulate time passing beyond wall_time_limit
    time.sleep(0.08)

    action = WorkAction(op="read", path="somefile.txt")
    with pytest.raises(TimeoutError, match="Run wall-time budget of 0.05s exhausted"):
        executor(action)

    updated_run = get("runs", run_id)
    assert updated_run["status"] == "failed"
    assert updated_run.get("stop_reason") == "timeout"


def test_work_executor_tool_budget_exhaustion():
    grant_id = str(uuid.uuid4())
    put("grants", {"id": grant_id, "mode": "host", "root": "/var/tmp", "capabilities": ["files"], "revoked": False})
    
    agent_id = str(uuid.uuid4())
    put("agents", {"id": agent_id, "name": "Budget Agent 2", "instructions": "", "tools": ["files"], "grants": [grant_id], "archived": False})

    run_id = str(uuid.uuid4())
    run = {
        "id": run_id,
        "agent": agent_id,
        "grant": grant_id,
        "status": "running",
        "tools": ["read"],
        "wall_time_limit": 1800,
        "created": time.time(),
        "root_run": run_id,
    }
    put("runs", run)

    executor = WorkExecutor(run_id)
    executor.calls = 30  # next call will be 31 (> 30)

    action = WorkAction(op="read", path="somefile.txt")
    with pytest.raises(ValueError, match="Tool budget exhausted"):
        executor(action)

    updated_run = get("runs", run_id)
    assert updated_run["status"] == "failed"
    assert updated_run.get("stop_reason") == "tool_budget_exhausted"


def test_server_stop_sets_user_cancelled_stop_reason(monkeypatch):
    run_id = str(uuid.uuid4())
    run = {
        "id": run_id,
        "status": "running",
        "created": time.time(),
    }
    put("runs", run)

    monkeypatch.setattr(server, "companion", lambda path, body: {"stopped": True})
    monkeypatch.setattr(server, "kill_worker", lambda ident: None)

    stopped_run = server.stop(run_id)
    assert stopped_run["status"] == "stopped"
    assert stopped_run.get("stop_reason") == "user_cancelled"
