import uuid
import pytest
from workbench import server
from workbench.store import put, get, all_objects, event, events
from workbench.worker import WorkExecutor, WorkAction


def setup_delegation_env():
    grant_id = str(uuid.uuid4())
    provider_id = str(uuid.uuid4())
    put("providers", {"id": provider_id, "name": "Test provider", "type": "compatible", "url": "http://test", "secret": "", "models": [{"id": "test-model", "source": "manual"}]})
    put("grants", {"id": grant_id, "mode": "host", "root": "/tmp", "capabilities": ["files", "shell"], "revoked": False})
    
    parent_agent = put("agents", {
        "id": str(uuid.uuid4()), "name": "Lead Agent", "instructions": "Lead work",
        "connection": provider_id, "model": "test-model",
        "tools": ["files", "delegate"], "grants": [grant_id], "archived": False
    })
    
    worker_agent = put("agents", {
        "id": str(uuid.uuid4()), "name": "Worker Agent", "instructions": "Worker work",
        "connection": provider_id, "model": "test-model",
        "tools": ["files", "shell"], "grants": [grant_id], "archived": False
    })

    return grant_id, provider_id, parent_agent, worker_agent


def test_delegated_tools_intersect_with_parent():
    grant_id, provider_id, parent_agent, worker_agent = setup_delegation_env()
    
    # Parent only has ['files', 'delegate'], worker has ['files', 'shell']
    parent_run = put("runs", {
        "id": str(uuid.uuid4()), "agent": parent_agent["id"], "connection": provider_id,
        "model": "test-model", "grant": grant_id, "mode": "host", "machine": "local",
        "task": "Lead task", "status": "running", "tools": ["files", "delegate"],
        "depth": 0, "parent": None, "created": 1000.0
    })

    # Spawn delegated run
    child_run = server.new_run({
        "agent": worker_agent["id"], "task": "Child task", "grant": grant_id
    }, parent=parent_run)

    # Worker requested ['files', 'shell'], but parent only has ['files', 'delegate']
    # Intersected tools must be ['files']
    assert child_run["tools"] == ["files"]
    assert "shell" not in child_run["tools"]
    assert child_run["depth"] == 1
    assert child_run["parent"] == parent_run["id"]
    assert child_run["root_run"] == parent_run["id"]


def test_parent_lacking_delegate_tool_rejected():
    grant_id, provider_id, parent_agent, worker_agent = setup_delegation_env()
    parent_run = put("runs", {
        "id": str(uuid.uuid4()), "agent": parent_agent["id"], "connection": provider_id,
        "model": "test-model", "grant": grant_id, "mode": "host", "machine": "local",
        "task": "Lead task", "status": "running", "tools": ["files"], # no delegate tool!
        "depth": 0, "parent": None, "created": 1000.0
    })

    with pytest.raises(ValueError, match="lacks delegation authority"):
        server.new_run({
            "agent": worker_agent["id"], "task": "Child task", "grant": grant_id
        }, parent=parent_run)


def test_delegation_cannot_escalate_grant_or_cross_workspaces():
    grant_id, provider_id, parent_agent, worker_agent = setup_delegation_env()
    other_grant = put("grants", {"id": str(uuid.uuid4()), "mode": "host", "root": "/var/tmp", "capabilities": ["files"], "revoked": False})
    
    # Worker agent has both grants, but parent only has grant_id
    worker_agent["grants"].append(other_grant["id"])
    put("agents", worker_agent)

    parent_run = put("runs", {
        "id": str(uuid.uuid4()), "agent": parent_agent["id"], "connection": provider_id,
        "model": "test-model", "grant": grant_id, "mode": "host", "machine": "local",
        "task": "Lead task", "status": "running", "tools": ["files", "delegate"],
        "depth": 0, "parent": None, "created": 1000.0
    })

    # Attempting to use a different grant than parent's grant is rejected
    with pytest.raises(ValueError, match="exceeds parent authority"):
        server.new_run({
            "agent": worker_agent["id"], "task": "Child task", "grant": other_grant["id"]
        }, parent=parent_run)


def test_delegation_depth_limit_enforced():
    grant_id, provider_id, parent_agent, worker_agent = setup_delegation_env()
    level2_run = put("runs", {
        "id": str(uuid.uuid4()), "agent": worker_agent["id"], "connection": provider_id,
        "model": "test-model", "grant": grant_id, "mode": "host", "machine": "local",
        "task": "Level 2 task", "status": "running", "tools": ["files", "delegate"],
        "depth": 2, "parent": "some-parent", "created": 1000.0
    })

    with pytest.raises(ValueError, match="exceeds parent authority"):
        server.new_run({
            "agent": worker_agent["id"], "task": "Level 3 task", "grant": grant_id
        }, parent=level2_run)


def test_delegation_to_archived_agent_rejected():
    grant_id, provider_id, parent_agent, worker_agent = setup_delegation_env()
    archived_worker = put("agents", {
        "id": str(uuid.uuid4()), "name": "Archived Agent", "instructions": "Archived",
        "connection": provider_id, "model": "test-model",
        "tools": ["files"], "grants": [grant_id], "archived": True
    })
    parent_run = put("runs", {
        "id": str(uuid.uuid4()), "agent": parent_agent["id"], "connection": provider_id,
        "model": "test-model", "grant": grant_id, "mode": "host", "machine": "local",
        "task": "Lead task", "status": "running", "tools": ["files", "delegate"],
        "depth": 0, "parent": None, "created": 1000.0
    })

    with pytest.raises(ValueError, match="archived"):
        server.new_run({
            "agent": archived_worker["id"], "task": "Child task", "grant": grant_id
        }, parent=parent_run)


def test_delegation_failure_propagates_to_parent(monkeypatch):
    grant_id, provider_id, parent_agent, worker_agent = setup_delegation_env()
    parent_run = put("runs", {
        "id": str(uuid.uuid4()), "agent": parent_agent["id"], "connection": provider_id,
        "model": "test-model", "grant": grant_id, "mode": "host", "machine": "local",
        "task": "Lead task", "status": "running", "tools": ["files", "delegate"],
        "depth": 0, "parent": None, "created": 1000.0
    })

    child_ident = str(uuid.uuid4())
    # Mock new_run to return a child that ends up failed
    monkeypatch.setattr(server, "new_run", lambda body, parent: put("runs", {
        "id": child_ident, "agent": body["agent"], "status": "failed", "depth": 1, "parent": parent["id"]
    }))

    executor = WorkExecutor(parent_run["id"])
    result = executor(WorkAction(op="delegate", agent=worker_agent["id"], content="Failing subtask"))
    
    # Must return an error observation
    assert result.is_error is True
    assert "status 'failed'" in result.content[0].text
    err_events = [item for item in events(parent_run["id"]) if item["kind"] == "tool_error"]
    assert len(err_events) > 0
    assert err_events[-1]["data"]["status"] == "failed"
