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
