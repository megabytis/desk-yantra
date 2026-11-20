import uuid
from workbench import server
from workbench.store import get, put


def test_stop_cancels_unused_approvals_and_descendants(monkeypatch):
    parent, child = str(uuid.uuid4()), str(uuid.uuid4())
    for ident, status, ancestor in ((parent, "approval", None), (child, "running", parent)):
        put("runs", {"id": ident, "status": status, "parent": ancestor})
        put("approvals", {"id": ident, "run": ident, "status": "approved", "action": {"op": "write"}})
    stopped = []
    monkeypatch.setattr(server, "companion", lambda path, body: stopped.append(path) or {"stopped": True})
    monkeypatch.setattr(server, "kill_worker", lambda ident: None)
    assert server.stop(parent)["status"] == "stopped"
    assert get("runs", child)["status"] == "stopped"
    assert all(get("approvals", ident)["status"] == "cancelled" for ident in (parent, child))
    assert set(stopped) == {"/stop/" + parent, "/stop/" + child}
    assert server.stop(parent)["status"] == "stopped"
    assert len(stopped) == 2


def test_stop_requires_confirmed_companion_cleanup(monkeypatch):
    ident = str(uuid.uuid4())
    put("runs", {"id": ident, "status": "running"})
    monkeypatch.setattr(server, "companion", lambda path, body: {"stopped": False})
    monkeypatch.setattr(server, "kill_worker", lambda run: None)
    assert server.stop(ident)["status"] == "review"


def test_revoke_stops_approval_wait_and_ignores_legacy_runs(monkeypatch):
    ident, legacy = str(uuid.uuid4()), str(uuid.uuid4())
    put("grants", {"id": ident, "revoked": False})
    put("runs", {"id": legacy, "status": "completed"})
    put("runs", {"id": ident, "grant": ident, "status": "approval"})
    put("approvals", {"id": ident, "run": ident, "status": "pending", "action": {"op": "shell"}})
    monkeypatch.setattr(server, "companion", lambda path, body: {"stopped": True})
    monkeypatch.setattr(server, "kill_worker", lambda run: None)
    assert server.revoke(ident)["revoked"] is True
    assert get("runs", ident)["status"] == "stopped"
    assert get("approvals", ident)["status"] == "cancelled"


def test_stop_deep_descendants_across_hierarchy(monkeypatch):
    root, child, grandchild = str(uuid.uuid4()), str(uuid.uuid4()), str(uuid.uuid4())
    put("runs", {"id": root, "status": "running", "parent": None})
    put("runs", {"id": child, "status": "approval", "parent": root})
    put("runs", {"id": grandchild, "status": "queued", "parent": child})
    for ident in (root, child, grandchild):
        put("approvals", {"id": ident, "run": ident, "status": "approved", "action": {"op": "write"}})
    stopped_calls = []
    killed = []
    monkeypatch.setattr(server, "companion", lambda path, body: stopped_calls.append(path) or {"stopped": True})
    monkeypatch.setattr(server, "kill_worker", lambda ident: killed.append(ident))

    result = server.stop(root)
    assert result["status"] == "stopped"
    assert get("runs", root)["status"] == "stopped"
    assert get("runs", child)["status"] == "stopped"
    assert get("runs", grandchild)["status"] == "stopped"
    for ident in (root, child, grandchild):
        assert get("approvals", ident)["status"] == "cancelled"
    assert set(stopped_calls) == {"/stop/" + root, "/stop/" + child, "/stop/" + grandchild}
    assert set(killed) == {root, child, grandchild}
