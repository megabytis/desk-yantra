from workbench import __main__ as cli, store


def test_stop_includes_waiting_approval(monkeypatch):
    from workbench import client, server

    run = {"id": "waiting", "status": "approval"}
    calls = []
    monkeypatch.setattr(cli.sys, "argv", ["workbench", "stop"])
    monkeypatch.setattr(store, "all_objects", lambda kind: [run])
    monkeypatch.setattr(store, "put", lambda kind, value: calls.append((kind, value.copy())))
    monkeypatch.setattr(client, "companion", lambda path, body, timeout: calls.append(path))
    monkeypatch.setattr(server, "kill_worker", lambda ident: calls.append(("kill", ident)))
    cli.main()
    assert run["status"] == "stopped"
    assert "/stop/waiting" in calls
    assert ("kill", "waiting") in calls
