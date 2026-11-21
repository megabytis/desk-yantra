import uuid
import pytest
from workbench import server
from workbench.store import put, get, event, all_objects
from workbench.verifier import verify_run_outcome


def setup_test_runs():
    provider = put("providers", {
        "id": str(uuid.uuid4()), "name": "Test provider", "type": "compatible",
        "url": "http://test", "secret": "", "models": [{"id": "test-model", "source": "manual"}]
    })
    grant = put("grants", {
        "id": str(uuid.uuid4()), "mode": "host", "root": "/tmp", "capabilities": ["files", "shell", "browser"], "revoked": False
    })
    agent = put("agents", {
        "id": str(uuid.uuid4()), "name": "Lead Agent", "instructions": "Lead instructions",
        "connection": provider["id"], "model": "test-model",
        "tools": ["files", "shell", "delegate"], "grants": [grant["id"]], "archived": False
    })
    subagent = put("agents", {
        "id": str(uuid.uuid4()), "name": "Worker Subagent", "instructions": "Subagent instructions",
        "connection": provider["id"], "model": "test-model",
        "tools": ["files", "shell"], "grants": [grant["id"]], "archived": False
    })
    root_run = put("runs", {
        "id": str(uuid.uuid4()), "agent": agent["id"], "connection": provider["id"],
        "model": "test-model", "grant": grant["id"], "mode": "host", "machine": "local",
        "task": "Build feature and test", "status": "running", "tools": ["files", "shell", "delegate"],
        "depth": 0, "parent": None, "created": 1000.0
    })
    child_run = put("runs", {
        "id": str(uuid.uuid4()), "agent": subagent["id"], "connection": provider["id"],
        "model": "test-model", "grant": grant["id"], "mode": "host", "machine": "local",
        "task": "Subtask work", "status": "running", "tools": ["files", "shell"],
        "depth": 1, "parent": root_run["id"], "root_run": root_run["id"], "created": 1005.0
    })
    return root_run, child_run


def test_verification_read_only_contract():
    run_id = str(uuid.uuid4())
    put("runs", {"id": run_id, "task": "Inspect directory", "status": "completed", "tools": ["files"]})
    event(run_id, "tool_call", {"op": "list", "path": "."})
    event(run_id, "tool_result", {"path": ".", "entries": []})

    report = verify_run_outcome(run_id)
    assert report["outcome"] == "verified_read_only"
    assert report["verified"] is True
    assert get("runs", run_id)["outcome"] == "verified"


def test_verification_unverified_file_edits():
    run_id = str(uuid.uuid4())
    put("runs", {"id": run_id, "task": "Fix bug in code", "status": "completed", "tools": ["files", "shell"]})
    event(run_id, "tool_call", {"op": "write", "path": "fix.py", "content": "x = 1"})
    event(run_id, "tool_result", "File written")

    report = verify_run_outcome(run_id)
    assert report["outcome"] == "unverified_mutations"
    assert report["verified"] is False
    assert get("runs", run_id)["outcome"] == "needs_review"


def test_verification_successful_code_repair_with_passing_tests():
    run_id = str(uuid.uuid4())
    put("runs", {"id": run_id, "task": "Fix bug and run tests", "status": "completed", "tools": ["files", "shell"]})
    event(run_id, "tool_call", {"op": "write", "path": "fix.py", "content": "x = 1"})
    event(run_id, "tool_result", "File written")
    event(run_id, "tool_call", {"op": "shell", "command": "pytest tests/"})
    event(run_id, "command_result", {"command": "pytest tests/", "exit_status": 0, "cwd": "/tmp"})

    report = verify_run_outcome(run_id)
    assert report["outcome"] == "verified_success"
    assert report["verified"] is True
    assert any(v["kind"] == "post_mutation_test" and v["passed"] for v in report["verifications"])
    assert get("runs", run_id)["outcome"] == "verified"


def test_verification_unresolved_command_failure():
    run_id = str(uuid.uuid4())
    put("runs", {"id": run_id, "task": "Run build", "status": "completed", "tools": ["shell"]})
    event(run_id, "tool_call", {"op": "shell", "command": "make build"})
    event(run_id, "command_result", {"command": "make build", "exit_status": 2, "cwd": "/tmp"})

    report = verify_run_outcome(run_id)
    assert report["outcome"] == "unresolved_command_failure"
    assert report["verified"] is False
    assert get("runs", run_id)["outcome"] == "needs_review"


def test_delegation_tree_api_endpoint():
    root_run, child_run = setup_test_runs()
    put("artifacts", {"id": "art-1", "run": child_run["id"], "name": "child-output.txt", "path": "/tmp/1", "created": 1010.0})

    tree = server.run_tree(child_run["id"])
    assert tree is not None
    assert tree["id"] == root_run["id"]
    assert tree["agent"] == "Lead Agent"
    assert tree["depth"] == 0
    assert len(tree["children"]) == 1

    child_node = tree["children"][0]
    assert child_node["id"] == child_run["id"]
    assert child_node["agent"] == "Worker Subagent"
    assert child_node["depth"] == 1
    assert len(child_node["artifacts"]) == 1
    assert child_node["artifacts"][0]["name"] == "child-output.txt"


def test_stop_parent_cancels_active_child_runs(monkeypatch):
    root_run, child_run = setup_test_runs()
    monkeypatch.setattr(server, "companion", lambda *args, **kwargs: {"stopped": True})
    monkeypatch.setattr(server, "kill_worker", lambda ident: None)

    # Stop root run
    server.stop_run(root_run["id"])

    # Root run is stopped
    assert get("runs", root_run["id"])["status"] == "stopped"
    # Child run was cancelled recursively
    assert get("runs", child_run["id"])["status"] == "stopped"
    assert get("runs", child_run["id"])["stop_reason"] == "user_cancelled"

