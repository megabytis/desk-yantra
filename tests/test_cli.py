import uuid
from workbench import __main__ as cli, server, companion
from workbench.store import get, put


def test_local_stop_cancels_waiting_approval(monkeypatch):
    ident = str(uuid.uuid4())
    put("runs", {"id": ident, "status": "approval"})
    put("approvals", {"id": ident, "run": ident, "status": "approved", "action": {"op": "write"}})
    calls = []
    monkeypatch.setattr(cli.sys, "argv", ["workbench", "stop"])
    monkeypatch.setattr(server, "companion", lambda path, body, timeout: calls.append(path) or {"stopped": True})
    monkeypatch.setattr(server, "kill_worker", lambda run_id: calls.append(("kill", run_id)))
    assert cli.main() == 0
    assert get("runs", ident)["status"] == "stopped"
    assert get("approvals", ident)["status"] == "cancelled"
    assert "/stop/" + ident in calls
    assert ("kill", ident) in calls


def test_local_stop_requires_cleanup_confirmation(monkeypatch):
    ident = str(uuid.uuid4())
    put("runs", {"id": ident, "status": "running"})
    monkeypatch.setattr(cli.sys, "argv", ["workbench", "stop"])
    monkeypatch.setattr(server, "companion", lambda path, body, timeout: {"stopped": False})
    monkeypatch.setattr(server, "kill_worker", lambda run_id: None)
    recovered = []
    monkeypatch.setattr(companion, "recover_commands", lambda: recovered.append(True))
    assert cli.main() == 1
    assert get("runs", ident)["status"] == "review"
    assert recovered == [True]
