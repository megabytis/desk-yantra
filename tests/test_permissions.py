import os
import time
import threading
import uuid

from fastapi.testclient import TestClient
from workbench import companion
from workbench.store import TOKEN, get, put, redact, CIPHER, events


def setup_run(tmp_path):
    ident = str(uuid.uuid4())
    grant = put("grants", {"id": ident, "root": str(tmp_path), "capabilities": ["files", "shell"], "revoked": False})
    run = put("runs", {"id": ident, "grant": ident, "mode": "host", "status": "running", "tools": ["files", "shell"]})
    return grant, run


def authorize(run, action, status="approved"):
    ident = str(uuid.uuid4())
    put("approvals", {"id": ident, "run": run["id"], "action": action, "status": status})
    return action | {"approval": ident}


def test_denial_revocation_and_replay(tmp_path):
    grant, run = setup_run(tmp_path)
    client = TestClient(companion.app, headers={"Authorization": "Bearer " + TOKEN})
    action = {"op": "shell", "command": "touch forbidden"}
    denied = client.post("/execute/" + run["id"], json=authorize(run, action, "denied"))
    assert denied.status_code == 403
    assert not (tmp_path / "forbidden").exists()
    approved = authorize(run, {"op": "write", "path": "actual.txt", "content": "actual"})
    assert client.post("/execute/" + run["id"], json=approved).status_code == 200
    assert (tmp_path / "actual.txt").read_text() == "actual"
    assert client.post("/execute/" + run["id"], json=approved).status_code == 403
    grant["revoked"] = True
    put("grants", grant)
    assert client.post("/execute/" + run["id"], json={"op": "read", "path": "actual.txt"}).status_code == 403


def test_file_only_profile_can_list_and_create_nested_files(tmp_path):
    grant,run=setup_run(tmp_path)
    run['tools']=['files']
    put('runs',run)
    client=TestClient(companion.app,headers={'Authorization':'Bearer '+TOKEN})
    action={'op':'write','path':'reports/nested/result.txt','content':'actual result'}
    assert client.post('/execute/'+run['id'],json=authorize(run,action)).status_code==200
    listing=client.post('/execute/'+run['id'],json={'op':'list','path':'reports/nested'})
    assert listing.status_code==200
    assert listing.json()['result']['entries'][0]['name']=='result.txt'
    assert client.post('/execute/'+run['id'],json={'op':'list','path':'../'}).status_code==403
    assert client.post('/execute/'+run['id'],json=authorize(run,{'op':'shell','command':'touch must-not-execute'})).status_code==403
    assert not (tmp_path/'must-not-execute').exists()


def test_scoped_file_rejects_escape_and_symlink(tmp_path):
    import pytest
    (tmp_path / "link").symlink_to("/etc/passwd")
    for name in ("../outside", "/etc/passwd", "link"):
        with pytest.raises((ValueError, OSError)):
            companion.scoped_file(tmp_path, name)
    (tmp_path / "original").write_text("preserved")
    os.link(tmp_path / "original", tmp_path / "hardlink")
    with pytest.raises(ValueError):
        companion.scoped_file(tmp_path,"hardlink",True,"must not overwrite")
    assert (tmp_path / "original").read_text() == "preserved"
    os.mkfifo(tmp_path / "fifo")
    with pytest.raises(ValueError):
        companion.scoped_file(tmp_path,"fifo")


def test_stop_terminates_process_group(tmp_path):
    grant, run = setup_run(tmp_path)
    result = []
    worker = threading.Thread(target=lambda: result.append(companion.command(run, ["bash", "-c", "sleep 100"], tmp_path)))
    worker.start()
    deadline = time.time() + 5
    while run["id"] not in companion.PROCESSES and time.time() < deadline:
        time.sleep(.01)
    process = companion.PROCESSES[run["id"]]
    companion.terminate(run["id"])
    worker.join(timeout=5)
    assert not worker.is_alive()
    assert process.poll() is not None
    assert result[0]["exit_status"] != 0


def test_companion_rejects_browser_origins_and_missing_auth():
    client = TestClient(companion.app)
    assert client.get("/capabilities").status_code == 403
    assert client.get("/capabilities", headers={"Authorization": "Bearer " + TOKEN, "Origin": "https://evil.example"}).status_code == 403


def test_stop_kills_group_after_parent_shell_exits(tmp_path):
    grant, run = setup_run(tmp_path)
    result = []
    worker = threading.Thread(target=lambda: result.append(companion.command(run,["bash","-c","sleep 100 &"],tmp_path)))
    worker.start()
    deadline = time.time()+5
    while run["id"] not in companion.PROCESSES and time.time() < deadline:
        time.sleep(.01)
    time.sleep(.1)
    companion.terminate(run["id"])
    worker.join(timeout=5)
    assert not worker.is_alive()


def test_secret_redaction():
    put("providers", {"id": "redaction-test", "secret": CIPHER.encrypt(b"secret-test-value").decode()})
    assert redact({"output": "secret-test-value"}) == {"output": "[REDACTED]"}
    from workbench.store import safe_stream_prefix
    buffer, emitted = "", []
    for chunk in ("prefix "*100+"secret-test-", "value", " suffix"*100):
        buffer += chunk
        prefix, buffer = safe_stream_prefix(buffer)
        emitted.append(redact(prefix))
    emitted.append(redact(buffer))
    assert "secret-test-value" not in "".join(emitted)
    assert "[REDACTED]" in "".join(emitted)


def test_pointer_arguments_are_exact_and_validated(monkeypatch):
    import pytest
    monkeypatch.setattr(companion, "capabilities", lambda: {"mouse":True,"session":"unknown"})
    assert companion.input_command({"input_kind":"move","x":100,"y":200}) == ["ydotool","mousemove","--absolute","-x","100","-y","200"]
    assert companion.input_command({"input_kind":"click","button":"right"}) == ["ydotool","click","0xC1"]
    with pytest.raises(ValueError):
        companion.input_command({"input_kind":"move","x":-1,"y":200})


def test_noisy_command_has_bounded_observation_and_event_history(tmp_path):
    _,run=setup_run(tmp_path)
    result=companion.command(run,['python','-c','import sys;sys.stdout.write("x"*250000);sys.exit(7)'],tmp_path)
    terminal=''.join(item['data']['output'] for item in events(run['id']) if item['kind']=='terminal')
    assert result['exit_status']==7
    assert result['output_truncated'] is True
    assert len(result['output'])==200_000
    assert len(terminal)<201_000
    assert terminal.endswith('[Output truncated after 200000 characters; command continued to completion.]\n')


def test_revoke_waiting_on_file_admission_blocks_write(tmp_path, monkeypatch):
    """Revocation wins while a write waits for the companion admission lock."""
    grant, run = setup_run(tmp_path)
    client = TestClient(companion.app, headers={"Authorization": "Bearer " + TOKEN})
    action = authorize(run, {"op": "write", "path": "race.txt", "content": "forbidden"})
    entered = threading.Event()
    release = threading.Event()
    original = companion.claim_approval

    def wait_after_claim(*args):
        result = original(*args)
        entered.set()
        assert release.wait(5)
        return result

    monkeypatch.setattr(companion, "claim_approval", wait_after_claim)
    result = []
    worker = threading.Thread(target=lambda: result.append(client.post("/execute/" + run["id"], json=action)))
    worker.start()
    assert entered.wait(5)
    try:
        assert client.post("/revoke/" + grant["id"]).status_code == 200
    finally:
        release.set()
        worker.join(5)
    assert not worker.is_alive()
    assert result[0].status_code == 403
    assert not (tmp_path / "race.txt").exists()


def test_revoke_before_shell_launch_blocks_process(tmp_path, monkeypatch):
    """A consumed approval cannot launch a shell after the grant is revoked."""
    grant, run = setup_run(tmp_path)
    action = authorize(run, {"op": "shell", "command": "touch race-shell.txt"})
    entered = threading.Event()
    release = threading.Event()
    original = companion.claim_approval

    def wait_after_claim(*args):
        result = original(*args)
        entered.set()
        assert release.wait(10)
        return result

    monkeypatch.setattr(companion, "claim_approval", wait_after_claim)
    result = []
    def attempt():
        try:
            companion.execute(run["id"], action.copy())
            result.append("executed")
        except Exception as error:
            result.append(error)

    worker = threading.Thread(target=attempt)
    worker.start()
    assert entered.wait(10)
    try:
        assert companion.revoke(grant["id"]) == {"revoked": True}
    finally:
        release.set()
        worker.join(10)
    assert not worker.is_alive()
    assert getattr(result[0], "status_code", None) == 403
    assert not (tmp_path / "race-shell.txt").exists()


def test_revoke_kills_running_shell_before_late_effect(tmp_path):
    grant, run = setup_run(tmp_path)
    client = TestClient(companion.app, headers={"Authorization": "Bearer " + TOKEN})
    action = authorize(run, {"op": "shell", "command": "sleep 3; touch late-effect.txt"})
    result = []
    worker = threading.Thread(target=lambda: result.append(client.post("/execute/" + run["id"], json=action)))
    worker.start()
    deadline = time.monotonic() + 5
    while run["id"] not in companion.PROCESSES and time.monotonic() < deadline:
        time.sleep(.01)
    assert run["id"] in companion.PROCESSES
    process = companion.PROCESSES[run["id"]]
    assert process.poll() is None
    assert client.post("/revoke/" + grant["id"]).status_code == 200
    worker.join(5)
    assert not worker.is_alive()
    assert process.poll() is not None
    assert not (tmp_path / "late-effect.txt").exists()


def test_concurrent_duplicate_approval_executes_once(tmp_path, monkeypatch):
    """Two requests racing on one approval cannot both perform the action."""
    grant, run = setup_run(tmp_path)
    action = authorize(run, {"op": "write", "path": "once.txt", "content": "one execution"})
    barrier = threading.Barrier(2)
    original = companion.claim_approval

    def simultaneous_claim(*args):
        barrier.wait(timeout=10)
        return original(*args)

    monkeypatch.setattr(companion, "claim_approval", simultaneous_claim)
    responses = []

    def attempt():
        client = TestClient(companion.app, headers={"Authorization": "Bearer " + TOKEN})
        responses.append(client.post("/execute/" + run["id"], json=action.copy()).status_code)

    workers = [threading.Thread(target=attempt) for _ in range(2)]
    for worker in workers:
        worker.start()
    for worker in workers:
        worker.join(10)
    assert all(not worker.is_alive() for worker in workers)
    assert sorted(responses) == [200, 403]
    assert (tmp_path / "once.txt").read_text() == "one execution"
    assert len([item for item in events(run["id"]) if item["kind"] == "action_started"]) == 1


def test_revoke_waiting_on_read_admission_blocks_read(tmp_path, monkeypatch):
    """A read operation paused before admission is blocked if the grant is revoked, leaking no data."""
    secret_file = tmp_path / "secret.txt"
    secret_file.write_text("classified data")
    grant, run = setup_run(tmp_path)
    entered = threading.Event()
    release = threading.Event()
    original_event = companion.event

    def wait_on_start(run_id, kind, value):
        result = original_event(run_id, kind, value)
        if kind == "action_started" and value.get("op") == "read":
            entered.set()
            assert release.wait(10)
        return result

    monkeypatch.setattr(companion, "event", wait_on_start)
    client = TestClient(companion.app, headers={"Authorization": "Bearer " + TOKEN})
    response_holder = []

    def attempt():
        res = client.post("/execute/" + run["id"], json={"op": "read", "path": "secret.txt"})
        response_holder.append(res)

    worker = threading.Thread(target=attempt)
    worker.start()
    assert entered.wait(10)
    try:
        assert client.post("/revoke/" + grant["id"]).status_code == 200
    finally:
        release.set()
        worker.join(10)
    assert not worker.is_alive()
    assert response_holder[0].status_code == 403
    assert "classified data" not in response_holder[0].text
