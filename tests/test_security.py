import pytest
from fastapi.testclient import TestClient
from workbench import server, companion
from workbench import store


def test_oversized_payload_rejected():
    client = TestClient(server.app)
    # Send request with content-length exceeding 10MB
    headers = {"Host": "127.0.0.1:8765", "Content-Length": "15000000", "x-paw": "1", "Cookie": f"paw={store.TOKEN}"}
    response = client.post("/api/runs", headers=headers, json={"task": "oversized"})
    assert response.status_code == 413
    assert "exceeds size limit" in response.json()["detail"]


def test_logout_clears_cookie():
    client = TestClient(server.app)
    # Log in first
    login_res = client.post("/api/login", headers={"Host": "127.0.0.1:8765"}, json={"token": store.TOKEN})
    assert login_res.status_code == 200
    assert "paw" in login_res.cookies

    # Logout
    logout_res = client.post("/api/logout", headers={"Host": "127.0.0.1:8765", "x-paw": "1"}, cookies=login_res.cookies)
    assert logout_res.status_code == 200
    assert logout_res.json()["ok"] is True
    # Verify cookie was deleted / expired
    cookie_header = logout_res.headers.get("set-cookie", "")
    assert 'paw=""' in cookie_header or "Max-Age=0" in cookie_header


def test_rotate_token():
    client = TestClient(server.app)
    old_token = store.TOKEN
    client.cookies.set("paw", old_token)

    # Rotate token
    rotate_res = client.post("/api/rotate-token", headers={"Host": "127.0.0.1:8765", "x-paw": "1"})
    assert rotate_res.status_code == 200
    new_token = store.TOKEN
    assert new_token != old_token

    # Old token fails on a client holding the old token
    old_client = TestClient(server.app)
    old_client.cookies.set("paw", old_token)
    old_check = old_client.get("/api/state", headers={"Host": "127.0.0.1:8765"})
    assert old_check.status_code == 401

    # New token succeeds
    new_client = TestClient(server.app)
    new_client.cookies.set("paw", new_token)
    new_check = new_client.get("/api/state", headers={"Host": "127.0.0.1:8765"})
    assert new_check.status_code == 200

    # Companion accepts new token and rejects old token
    comp_client = TestClient(companion.app)
    assert comp_client.get("/capabilities", headers={"Authorization": f"Bearer {old_token}"}).status_code == 403
    assert comp_client.get("/capabilities", headers={"Authorization": f"Bearer {new_token}"}).status_code == 200


def test_origin_and_host_validation():
    client = TestClient(server.app)
    client.cookies.set("paw", store.TOKEN)

    # Malicious origin rejected
    bad_origin = client.get("/api/state", headers={"Host": "127.0.0.1:8765", "Origin": "https://malicious.site"})
    assert bad_origin.status_code == 403

    # Malicious host rejected
    bad_host = client.get("/api/state", headers={"Host": "malicious.site"})
    assert bad_host.status_code == 403

    # Missing x-paw CSRF header on POST rejected
    no_csrf = client.post("/api/runs", headers={"Host": "127.0.0.1:8765"}, json={})
    assert no_csrf.status_code == 403


def test_chunked_payload_limit_rejects_actual_bytes_without_length():
    client = TestClient(server.app)
    client.cookies.set("paw", store.TOKEN)
    chunks = iter((b"x" * (server.MAX_REQUEST_BODY // 2),) * 3)
    response = client.post("/api/runs", headers={"Host": "127.0.0.1:8765", "x-paw": "1", "Content-Type": "application/json"}, content=chunks)
    assert response.status_code == 413
    assert "exceeds size limit" in response.json()["detail"]


def test_token_rotation_reaches_separate_process():
    import os
    import subprocess
    import sys

    child = subprocess.Popen(
        [sys.executable, "-u", "-c", "from workbench import store; import sys; print(store.TOKEN, flush=True); sys.stdin.readline(); print(store.current_token(), flush=True); print(store.redact(store.current_token()), flush=True)"],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, env=os.environ.copy(),
    )
    old = child.stdout.readline().strip()
    try:
        new = store.rotate_token()
        assert new != old
        child.stdin.write("continue\n")
        child.stdin.flush()
        assert child.stdout.readline().strip() == new
        assert child.stdout.readline().strip() == "[REDACTED]"
        assert child.wait(timeout=5) == 0
    finally:
        if child.poll() is None:
            child.kill()
            child.wait()
        child.stdin.close()
        child.stdout.close()
