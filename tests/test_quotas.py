import uuid
import pytest
from fastapi.testclient import TestClient
from workbench import companion
from workbench.store import get, put, events, consume_budget


def setup_run(tmp_path):
    ident = str(uuid.uuid4())
    grant = put("grants", {"id": ident, "root": str(tmp_path), "capabilities": ["files", "shell"], "revoked": False})
    run = put("runs", {"id": ident, "grant": ident, "mode": "host", "status": "running", "tools": ["files", "shell"]})
    return grant, run


def authorize(run, action, status="approved"):
    ident = str(uuid.uuid4())
    put("approvals", {"id": ident, "run": run["id"], "action": action, "status": status})
    return action | {"approval": ident}


def test_companion_enforces_task_budget(tmp_path):
    from workbench.store import TOKEN
    grant, run = setup_run(tmp_path)
    put("budgets", {"id": run["id"], "used": 90})
    client = TestClient(companion.app, headers={"Authorization": "Bearer " + TOKEN})
    action = {"op": "write", "path": "file.txt", "content": "content"}
    response = client.post("/execute/" + run["id"], json=authorize(run, action))
    assert response.status_code == 403
    assert "budget exhausted" in response.json()["detail"].lower()
    assert not (tmp_path / "file.txt").exists()


def test_aggregate_output_quota_across_commands(tmp_path):
    grant, run = setup_run(tmp_path)
    res1 = companion.command(run, ["python", "-c", "import sys; sys.stdout.write('a' * 180000)"], tmp_path)
    assert len(res1["output"]) == 180000
    assert not res1["output_truncated"]

    res2 = companion.command(run, ["python", "-c", "import sys; sys.stdout.write('b' * 180000)"], tmp_path)
    assert len(res2["output"]) == 180000
    assert not res2["output_truncated"]

    res3 = companion.command(run, ["python", "-c", "import sys; sys.stdout.write('c' * 180000)"], tmp_path)
    assert res3["output_truncated"] is True
    assert len(res3["output"]) == 140000  # 500000 - 360000 = 140000

    terminal = "".join(item["data"]["output"] for item in events(run["id"]) if item["kind"] == "terminal")
    assert "Aggregate run output quota" in terminal


def test_artifact_count_quota(tmp_path):
    from workbench.store import TOKEN
    grant, run = setup_run(tmp_path)
    client = TestClient(companion.app, headers={"Authorization": "Bearer " + TOKEN})

    for i in range(20):
        put("artifacts", {"id": f"{run['id']}-art-{i}", "run": run["id"], "name": f"art{i}.txt", "path": str(tmp_path / f"art{i}.txt")})

    action = {"op": "write", "path": "art21.txt", "content": "test"}
    response = client.post("/execute/" + run["id"], json=authorize(run, action))
    assert response.status_code == 403
    assert "Run artifact count quota exceeded" in response.json()["detail"]


def test_artifact_size_quota(tmp_path):
    from workbench.store import TOKEN
    grant, run = setup_run(tmp_path)
    client = TestClient(companion.app, headers={"Authorization": "Bearer " + TOKEN})

    oversized = "x" * 5_000_001
    action = {"op": "write", "path": "large.txt", "content": oversized}
    response = client.post("/execute/" + run["id"], json=authorize(run, action))
    assert response.status_code == 403
    assert "Artifact size exceeds limit" in response.json()["detail"]
