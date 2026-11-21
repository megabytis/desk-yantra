from fastapi.testclient import TestClient

from workbench import companion, server, store


def test_app_and_companion_health_are_minimal_and_authenticated(monkeypatch):
    app = TestClient(server.app)
    tool = TestClient(companion.app)
    assert app.get("/healthz").json() == {"status": "ok"}
    assert tool.get("/healthz").status_code == 403
    headers = {"Authorization": "Bearer " + store.current_token()}
    assert tool.get("/healthz", headers=headers).json() == {"status": "ok"}

    monkeypatch.setattr(store, "storage_ready", lambda: False)
    assert app.get("/healthz").status_code == 503
    assert app.get("/healthz").json() == {"status": "unavailable"}
    assert tool.get("/healthz", headers=headers).status_code == 503
