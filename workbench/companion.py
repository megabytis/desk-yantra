import difflib
import json
import os
import signal
import shutil
import subprocess
import threading
import time
import stat
import codecs
from contextlib import asynccontextmanager
from functools import lru_cache
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request

from . import store
from .store import STATE, event, events, get, put, claim_approval, redact, all_objects, safe_stream_prefix, get_budget, consume_output_quota

@asynccontextmanager
async def lifespan(app):
    recover_commands()
    yield


app = FastAPI(lifespan=lifespan)
PROCESSES = {}
STOPPED = set()
MUTEX = threading.RLock()


def process_identity(pid):
    return Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()[19]


def recover_commands():
    for item in all_objects("processes"):
        if not item.get("active"):
            continue
        try:
            if process_identity(item["pid"]) == item["started"]:
                os.killpg(item["pid"], signal.SIGKILL)
        except (FileNotFoundError, ProcessLookupError):
            pass
        item["active"] = False
        put("processes", item)
        run = get("runs", item["id"])
        if run["status"] in ("running", "queued", "paused"):
            run["status"] = "review"
            put("runs", run)
            event(run["id"], "recovery", "Companion restarted; prior command terminated. Its effects may be incomplete. Review required.")


@app.middleware("http")
async def authenticate(request: Request, call_next):
    from fastapi.responses import JSONResponse
    import secrets
    if request.headers.get("origin") or not secrets.compare_digest(request.headers.get("authorization", ""), "Bearer " + store.TOKEN):
        return JSONResponse({"detail": "Companion authentication required"}, status_code=403)
    return await call_next(request)


@lru_cache(maxsize=2)
def sandbox_status(bucket):
    if not shutil.which("docker"):
        return {"ready":False,"reason":"Docker is not installed. Install Docker, start its daemon and build the sandbox image."}
    try:
        daemon = subprocess.run(["docker","info","--format","{{.ServerVersion}}"],capture_output=True,text=True,timeout=3)
        if daemon.returncode:
            return {"ready":False,"reason":"Docker daemon is unavailable to this user. Start Docker and grant this user access to its socket."}
        image = subprocess.run(["docker","image","inspect","paw-sandbox:local"],capture_output=True,timeout=3)
        if image.returncode:
            return {"ready":False,"reason":"Sandbox image is missing. Run: docker build -t paw-sandbox:local sandbox"}
        return {"ready":True,"version":daemon.stdout.strip()}
    except subprocess.TimeoutExpired:
        return {"ready":False,"reason":"Docker did not respond within 3 seconds."}


@lru_cache(maxsize=2)
def portal_status(bucket):
    if not shutil.which('busctl'):
        return {'interfaces':[],'detail':'busctl is unavailable; desktop portal interfaces could not be detected.'}
    try:
        response=subprocess.run(['busctl','--user','--timeout=2','introspect','org.freedesktop.portal.Desktop','/org/freedesktop/portal/desktop','--no-pager'],capture_output=True,text=True,timeout=3)
        if response.returncode:
            return {'interfaces':[],'detail':'The desktop portal is unavailable on this user session bus.'}
        interfaces=[name for name in ('Screenshot','ScreenCast','RemoteDesktop') if 'org.freedesktop.portal.'+name in response.stdout]
        return {'interfaces':interfaces,'detail':'Advertised portal interfaces: '+(', '.join(interfaces) or 'none')+'. Portal consent sessions are not integrated in this app; direct capture/input still require independent grants and exact approvals.'}
    except subprocess.TimeoutExpired:
        return {'interfaces':[],'detail':'Desktop portal introspection timed out.'}


def capabilities():
    wayland = bool(os.environ.get("WAYLAND_DISPLAY"))
    socket_path = Path(os.environ.get("YDOTOOL_SOCKET", "/tmp/.ydotool_socket"))
    pointer = bool(shutil.which("ydotool")) and socket_path.is_socket() and os.access(socket_path, os.W_OK)
    portal=portal_status(int(time.monotonic()//30))
    return {"portal_interfaces":portal['interfaces'],"sandbox":sandbox_status(int(time.monotonic()//10)),"machine": os.uname().nodename, "session": os.environ.get("XDG_SESSION_TYPE", "unknown"), "hyprland": bool(os.environ.get("HYPRLAND_INSTANCE_SIGNATURE")), "screen": wayland and bool(shutil.which("grim")), "input": (wayland and bool(shutil.which("wtype"))) or pointer, "screen_detail": "Direct compositor capture via grim; requires explicit per-action approval" if wayland and shutil.which("grim") else "Missing Wayland session or grim", "input_detail": "wtype typing; virtual-keyboard protocol required" if wayland and shutil.which("wtype") else "ydotool typing available; daemon socket accessible" if pointer else "Missing wtype and/or ydotool with accessible daemon socket; desktop input unavailable", "mouse": pointer, "mouse_detail": "ydotool daemon socket accessible; movement/click requires approval; physical accuracy needs live validation" if pointer else "Missing ydotool or accessible ydotoold socket; pointer input unavailable", "portal_consent": portal['detail']}


def input_command(action):
    kind = action.get("input_kind", "text")
    if kind == "text":
        if capabilities()["session"] == "wayland" and shutil.which("wtype"):
            return ["wtype", "--", action["content"]]
        if capabilities()["mouse"]:
            return ["ydotool", "type", "--", action["content"]]
        raise ValueError(capabilities()["input_detail"])
    if not capabilities()["mouse"]:
        raise ValueError(capabilities()["mouse_detail"])
    if kind == "move":
        coordinates = [int(action["x"]), int(action["y"])]
        if any(value < 0 or value > 100000 for value in coordinates):
            raise ValueError("Pointer coordinates out of range")
        return ["ydotool", "mousemove", "--absolute", "-x", str(coordinates[0]), "-y", str(coordinates[1])]
    if kind == "click" and action.get("button") in ("left", "right", "middle"):
        return ["ydotool", "click", {"left":"0xC0", "right":"0xC1", "middle":"0xC2"}[action["button"]]]
    raise ValueError("Unsupported desktop input action")


def scoped_file(root, name, write=False, content=None):
    relative = Path(name)
    if relative.is_absolute() or not relative.parts or any(part in ("..", ".") for part in relative.parts):
        raise ValueError("Use a relative file path without traversal")
    if (Path(root) / relative).is_relative_to(STATE):
        raise ValueError("Private workbench state is not available to file tools")
    descriptor = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for part in relative.parts[:-1]:
            try:
                child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=descriptor)
            except FileNotFoundError:
                if not write:
                    raise
                os.mkdir(part,0o700,dir_fd=descriptor)
                child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=descriptor)
            os.close(descriptor)
            descriptor = child
        flags = os.O_NOFOLLOW | os.O_NONBLOCK | (os.O_WRONLY | os.O_CREAT if write else os.O_RDONLY)
        file_descriptor = os.open(relative.parts[-1], flags, 0o600, dir_fd=descriptor)
        with os.fdopen(file_descriptor, "w" if write else "r") as stream:
            info = os.fstat(stream.fileno())
            if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
                raise ValueError("Only regular, unlinked files are supported")
            if write:
                stream.truncate(0)
                stream.write(content)
                return "File written"
            return stream.read(1_000_000)
    finally:
        os.close(descriptor)


def scoped_listing(root,name='.'):
    relative=Path(name)
    if relative.is_absolute() or '..' in relative.parts or (Path(root)/relative).is_relative_to(STATE):
        raise ValueError('Directory is outside authorized file access')
    descriptor=os.open(root,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
    try:
        for part in relative.parts:
            child=os.open(part,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=descriptor)
            os.close(descriptor)
            descriptor=child
        names=sorted(os.listdir(descriptor))
        entries=[]
        for filename in names[:200]:
            if (Path(root)/relative/filename).is_relative_to(STATE):
                continue
            info=os.stat(filename,dir_fd=descriptor,follow_symlinks=False)
            entries.append({'name':filename,'kind':'directory' if stat.S_ISDIR(info.st_mode) else 'symlink' if stat.S_ISLNK(info.st_mode) else 'file','size':info.st_size})
        return {'path':name,'entries':entries,'truncated':len(names)>200}
    finally:
        os.close(descriptor)


MAX_ARTIFACTS_PER_RUN = 20
MAX_ARTIFACT_SIZE = 5_000_000
MAX_RUN_ARTIFACT_STORAGE = 20_000_000


def check_artifact_quota(run_id, new_size):
    existing = [item for item in all_objects("artifacts") if item.get("run") == run_id]
    if len(existing) >= MAX_ARTIFACTS_PER_RUN:
        raise ValueError(f"Run artifact count quota exceeded (maximum {MAX_ARTIFACTS_PER_RUN} artifacts per run)")
    if new_size > MAX_ARTIFACT_SIZE:
        raise ValueError(f"Artifact size exceeds limit ({MAX_ARTIFACT_SIZE} bytes)")
    total_size = sum(Path(item["path"]).stat().st_size for item in existing if Path(item.get("path", "")).exists())
    if total_size + new_size > MAX_RUN_ARTIFACT_STORAGE:
        raise ValueError(f"Run artifact storage quota exceeded (maximum {MAX_RUN_ARTIFACT_STORAGE} bytes per run)")


def check(run, action):
    current = get("runs", run["id"])
    manual_browser=current["status"]=="paused" and action.get("manual") is True and action["op"]=="browser"
    if (current["status"] != "running" and not manual_browser) or run["id"] in STOPPED:
        raise ValueError("Run stopped or requires recovery review")
    grant = get("grants", run["grant"])
    capability = {"list":"files","read": "files", "write": "files", "shell": "shell", "screen": "screen", "input": "input", "browser": "browser"}[action["op"]]
    if grant.get("revoked") or capability not in grant["capabilities"] or capability not in run["tools"]:
        raise ValueError("Permission revoked or capability not granted")
    root_run = run.get("root_run", run["id"])
    budget = get_budget(root_run)
    if budget.get("used", 0) >= 90:
        raise ValueError("Task-wide tool budget exhausted")
    if action["op"] == "write":
        check_artifact_quota(run["id"], len(action.get("content", "")))
    return grant


def terminate(run_id):
    with MUTEX:
        STOPPED.add(run_id)
        process = PROCESSES.get(run_id)
        if process:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass


def command(run, argv, cwd, action=None):
    with MUTEX:
        if run["id"] in STOPPED:
            raise ValueError("Run stopped")
        if action:
            check(run, action)
        process = subprocess.Popen(argv, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, start_new_session=True, env={name: value for name, value in os.environ.items() if name in ("PATH", "HOME", "LANG", "WAYLAND_DISPLAY", "XDG_RUNTIME_DIR", "XDG_SESSION_TYPE", "HYPRLAND_INSTANCE_SIGNATURE", "DBUS_SESSION_BUS_ADDRESS", "YDOTOOL_SOCKET")})
        PROCESSES[run["id"]] = process
        try:
            put("processes", {"id": run["id"], "pid": process.pid, "started": process_identity(process.pid), "active": True})
        except FileNotFoundError:
            pass
    timer = threading.Timer(120, lambda: terminate(run["id"]))
    timer.start()
    output_limit = 200_000
    chunks = []
    captured = 0
    truncated = False
    run_quota_hit = False
    output_buffer = ""
    decoder = codecs.getincrementaldecoder("utf-8")(errors="replace")
    try:
        while chunk := process.stdout.read1(4096):
            output = decoder.decode(chunk)
            if captured < output_limit and not run_quota_hit:
                kept = output[:output_limit - captured]
                allowed_len, run_quota_hit = consume_output_quota(run["id"], len(kept))
                actual_kept = kept[:allowed_len]
                captured += len(actual_kept)
                if actual_kept:
                    chunks.append(actual_kept)
                    output_buffer += actual_kept
                    prefix, output_buffer = safe_stream_prefix(output_buffer)
                    if prefix:
                        event(run["id"], "terminal", {"output": prefix})
                if len(actual_kept) < len(output):
                    truncated = True
                if run_quota_hit:
                    truncated = True
                    break
            elif output:
                truncated = True
        final_text = decoder.decode(b"", final=True)
        if final_text and captured < output_limit and not run_quota_hit:
            kept = final_text[:output_limit - captured]
            allowed_len, run_quota_hit = consume_output_quota(run["id"], len(kept))
            actual_kept = kept[:allowed_len]
            captured += len(actual_kept)
            if actual_kept:
                chunks.append(actual_kept)
                output_buffer += actual_kept
            if len(actual_kept) < len(final_text):
                truncated = True
        elif final_text:
            truncated = True
        if output_buffer:
            event(run["id"], "terminal", {"output": output_buffer})
        if run_quota_hit:
            event(run["id"], "terminal", {"output": "\n[Aggregate run output quota (500000 characters) reached; further output suppressed.]\n"})
        elif truncated:
            event(run["id"], "terminal", {"output": "\n[Output truncated after 200000 characters; command continued to completion.]\n"})
        return {"output": "".join(chunks), "output_truncated": truncated, "exit_status": process.wait(), "cwd": str(cwd), "command": argv}
    finally:
        timer.cancel()
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        with MUTEX:
            PROCESSES.pop(run["id"], None)
            put("processes", {"id": run["id"], "active": False})


@app.get("/capabilities")
def get_capabilities():
    return capabilities()


@app.post("/stop/{run_id}")
def stop(run_id: str):
    terminate(run_id)
    run = get("runs", run_id)
    if run["mode"] == "sandbox":
        container='paw-'+run.get('workspace_id',run_id)
        removed=subprocess.run(['docker','rm','-f',container],capture_output=True,timeout=15)
        if removed.returncode:
            # A stopped/missing container is safe; an unreachable daemon is not proof
            # that an in-container process has terminated.
            remaining=subprocess.run(['docker','container','ls','-aq','--filter','name=^/'+container+'$'],capture_output=True,timeout=15)
            if remaining.returncode or remaining.stdout.strip():
                raise HTTPException(503,'Docker could not confirm sandbox removal. Restore Docker and retry Stop; in-container actions may still be running.')
    return {"stopped": True}


@app.post("/recover-safe/{run_id}")
def recover_safe(run_id: str):
    run = get("runs", run_id)
    unsafe = any(item["kind"] in ("action_started", "tool_call") and item["data"].get("op") not in ("read","list") for item in events(run_id))
    if run["status"] != "queued" or unsafe or get("grants", run["grant"])["revoked"]:
        raise HTTPException(403, "Unsafe recovery rejected")
    with MUTEX:
        process = PROCESSES.get(run_id)
        if process and process.poll() is None:
            raise HTTPException(409, "Prior process still running")
        STOPPED.discard(run_id)
    return {"safe": True}


@app.post("/revoke/{grant_id}")
def revoke(grant_id: str):
    with MUTEX:
        grant = get("grants", grant_id)
        grant["revoked"] = True
        put("grants", grant)
        for run in all_objects("runs"):
            if run["grant"] == grant_id:
                terminate(run["id"])
    return {"revoked": True}


@app.post("/execute/{run_id}")
def execute(run_id: str, action: dict):
    try:
        run = get("runs", run_id)
        grant = check(run, action)
        approval_id = action.pop("approval", "")
        if action["op"] not in ("read","list"):
            claim_approval(approval_id, run_id, action)
        check(run, action)
        event(run_id, "action_started", action)
        if run["mode"] == "sandbox":
            result = sandbox(run, action)
        elif action["op"] == "list":
            with MUTEX:
                check(run,action)
                result=scoped_listing(grant['root'],action.get('path','.'))
        elif action["op"] in ("read", "write"):
            with MUTEX:
                check(run, action)
                result = scoped_file(grant["root"], action["path"], action["op"] == "write", action.get("content"))
        elif action["op"] == "shell":
            result = command(run, ["bash", "-lc", action["command"]], grant["root"], action)
        elif action["op"] == "screen":
            if not capabilities()["screen"]:
                raise ValueError(capabilities()["screen_detail"])
            check_artifact_quota(run_id, 1_000_000)
            target = STATE / "artifacts" / (run_id + ".png")
            target.parent.mkdir(exist_ok=True)
            result = command(run, ["grim", str(target)], grant["root"], action)
            if result["exit_status"] == 0:
                put("artifacts", {"id": run_id + "-screen", "run": run_id, "name": "desktop.png", "path": str(target)})
                result['artifact_id']=run_id+'-screen'
        elif action["op"] == "input":
            if not capabilities()["input"]:
                raise ValueError(capabilities()["input_detail"])
            result = command(run, input_command(action), grant["root"], action)
        else:
            raise ValueError("Browser is only available in sandbox mode")
        if action["op"] == "write":
            artifact_id = str(__import__("uuid").uuid4())
            target = STATE / "artifacts" / artifact_id
            target.parent.mkdir(exist_ok=True)
            if run["mode"] == "host":
                target.write_text(redact(scoped_file(grant["root"], action["path"])))
            else:
                if result["exit_status"] != 0:
                    raise ValueError("Sandbox file write failed")
                target.write_text(redact(sandbox(run, {"op": "read", "path": action["path"]})["output"]))
            put("artifacts", {"id": artifact_id, "run": run_id, "name": Path(action["path"]).name, "path": str(target)})
        if action["op"] == "browser" and result["exit_status"] == 0:
            check_artifact_quota(run_id, 2_000_000)
            artifact_id = str(__import__("uuid").uuid4())
            target = STATE / "artifacts" / artifact_id
            target.parent.mkdir(exist_ok=True)
            subprocess.run(["docker", "cp", "paw-" + run.get("workspace_id",run_id) + ":/workspace/browser.png", str(target)], check=True, capture_output=True, timeout=15)
            put("artifacts", {"id": artifact_id, "run": run_id, "name": "browser.png", "path": str(target), "created": time.time()})
            result['artifact_id']=artifact_id
        event(run_id, "action_finished", result)
        return {"result": result}
    except (ValueError, KeyError, OSError) as error:
        raise HTTPException(403, str(error)) from error


def sandbox(run, action):
    container = "paw-" + run.get("workspace_id",run["id"])
    inspected = subprocess.run(["docker", "inspect", container], capture_output=True)
    if inspected.returncode:
        grant = get("grants", run["grant"])
        mounts = ["--mount", "type=bind,source=" + grant["shared"] + ",target=/shared,readonly"] if grant.get("shared") else []
        subprocess.run(["docker", "run", "-d", "--name", container, "--init", "--cap-drop=ALL", "--security-opt=no-new-privileges", "--memory=2g", "--cpus=2", "--pids-limit=256", "--network=bridge", *mounts, "paw-sandbox:local"], check=True, capture_output=True, timeout=60)
        for attempt in range(30):
            ready = subprocess.run(["docker", "exec", container, "python", "-c", "import socket; socket.create_connection(('127.0.0.1',9111),1).close()"], capture_output=True)
            if ready.returncode == 0:
                break
            time.sleep(.5)
    if action["op"] == "shell":
        return command(run, ["docker", "exec", "-w", "/workspace", container, "bash", "-lc", action["command"]], STATE, action)
    encoded = json.dumps(action)
    return command(run, ["docker", "exec", container, "python", "/opt/action.py", encoded], STATE, action)
