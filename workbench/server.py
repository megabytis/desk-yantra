import asyncio
import json
import os
import secrets
import signal
import subprocess
import sys
import time
import threading
import uuid
from collections import deque
from contextlib import asynccontextmanager
from pathlib import Path

import httpx
from fastapi import FastAPI, HTTPException, Request, Response, Body
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from .providers import DEFAULTS, adapter, public, detect_local_engines
from .catalog import get_catalog, find_catalog_model
from .client import companion
from . import store
from .store import STATE, CIPHER, all_objects, event, events, get, put, redact, transition_run, rotate_token, artifact_path, touch_heartbeat, get_heartbeat, delete_heartbeat

WORKERS = {}
MAX_REQUEST_BODY = 10 * 1024 * 1024
LOGIN_FAILURE_LIMIT = 8
LOGIN_WINDOW_SECONDS = 60
_login_failures = {}
_login_lock = threading.Lock()


def login_attempt(client: str, valid: bool) -> int:
    """Return seconds until this client may retry; count only failed attempts."""
    now = time.monotonic()
    with _login_lock:
        for key, failures in list(_login_failures.items()):
            while failures and now - failures[0] >= LOGIN_WINDOW_SECONDS:
                failures.popleft()
            if not failures:
                _login_failures.pop(key, None)
        failures = _login_failures.get(client)
        if failures and len(failures) >= LOGIN_FAILURE_LIMIT:
            return max(1, int(LOGIN_WINDOW_SECONDS - (now - failures[0]) + 0.999))
        if valid:
            _login_failures.pop(client, None)
        else:
            _login_failures.setdefault(client, deque()).append(now)
    return 0


LEASE_TIMEOUT = 45.0


def reconcile_runs():
    """Periodic and on-demand reconciliation of active workers based on leases and heartbeats."""
    now = time.time()
    reconciled = []
    for run in all_objects("runs"):
        if run.get("status") in ("running", "approval"):
            ident = run["id"]
            hb = get_heartbeat(ident)
            is_dead = False
            if ident in WORKERS:
                if WORKERS[ident].poll() is not None:
                    is_dead = True
            elif hb:
                if (now - hb.get("time", 0)) >= LEASE_TIMEOUT:
                    is_dead = True
                elif hb.get("pid"):
                    try:
                        os.kill(hb["pid"], 0)
                    except (ProcessLookupError, PermissionError):
                        is_dead = True

            if is_dead:
                kill_worker(ident)
                delete_heartbeat(ident)
                cleanup_confirmed = False
                try:
                    cleanup_confirmed = companion("/stop/" + ident, {}, timeout=5).get("stopped") is True
                except Exception:
                    pass
                for approval in all_objects("approvals"):
                    if approval.get("run") == ident and approval.get("status") in ("pending", "approved"):
                        approval["status"] = "cancelled"
                        put("approvals", approval)
                history = events(ident)
                uncertain = any(item["kind"] in ("action_started", "tool_call") and item["data"].get("op") not in ("read", "list") for item in history)
                status = "review" if uncertain or not cleanup_confirmed else "failed"
                changed = transition_run(ident, ("running", "approval"), status, {"stop_reason": "lease_expired"})
                if changed:
                    reconciled.append(ident)
                    event(ident, "recovery", f"Worker lease expired (> {LEASE_TIMEOUT}s). Unresponsive worker stopped.")
                    try:
                        from .incidents import record_incident
                        record_incident(
                            f"Worker lease expired (> {LEASE_TIMEOUT}s) for run {ident}",
                            category="crash",
                            run_id=ident,
                            agent_id=run.get("agent"),
                        )
                    except Exception:
                        pass
    return reconciled


@asynccontextmanager
async def lifespan(app):
    recover = []
    for run in all_objects("runs"):
        if run["status"] in ("queued", "running", "approval", "paused"):
            cleanup_confirmed = False
            try:
                cleanup_confirmed = companion("/stop/" + run["id"], {}, timeout=20).get("stopped") is True
            except Exception:
                pass
            kill_worker(run["id"])
            # A recovered worker starts fresh; decisions from the interrupted
            # worker must never authorize a later action on the same run ID.
            for approval in all_objects("approvals"):
                if approval.get("run") == run["id"] and approval.get("status") in ("pending", "approved"):
                    approval["status"] = "cancelled"
                    put("approvals", approval)
            history = events(run["id"])
            uncertain = any(item["kind"] in ("action_started", "tool_call") and item["data"].get("op") not in ("read","list") for item in history)
            try:
                grant = get("grants", run["grant"])
                grant_valid = not grant.get("revoked", False)
            except KeyError:
                grant_valid = False
            run["status"] = "queued" if cleanup_confirmed and not uncertain and grant_valid and not run.get("parent") else "review"
            put("runs", run)
            if run["status"] == "queued":
                recover.append(run["id"])
                event(run["id"], "recovery", "Safe work recovered: no mutating tool calls were issued. Repeating inference/read operations only; future mutations still require new approval.")
            else:
                detail = "Companion did not confirm prior tool cleanup. " if not cleanup_confirmed else ""
                event(run["id"], "recovery", detail + "Worker interrupted. Outcome may be unknown. No actions replayed. Inspect files and external state before starting a new task.")
    for ident in recover:
        try:
            companion("/recover-safe/" + ident, {})
            start_worker(ident)
        except Exception:
            run = get("runs", ident)
            run["status"] = "review"
            put("runs", run)
            event(ident, "recovery", "Companion could not confirm safe recovery; manual review required")
    yield


app = FastAPI(lifespan=lifespan)


@app.get("/healthz")
def healthz():
    if not store.storage_ready():
        return JSONResponse({"status": "unavailable"}, status_code=503)
    return {"status": "ok"}


@app.middleware("http")
async def security(request: Request, call_next):
    origin = request.headers.get("origin")
    allowed = {"http://127.0.0.1:8765", "http://localhost:8765"}
    if request.headers.get("host") not in ("127.0.0.1:8765", "localhost:8765", "testserver") or (origin and origin not in allowed):
        return JSONResponse({"detail": "Origin or host rejected"}, status_code=403)
    content_length = request.headers.get("content-length")
    if content_length:
        try:
            size = int(content_length)
            if size < 0:
                return JSONResponse({"detail": "Invalid Content-Length header"}, status_code=400)
            if size > MAX_REQUEST_BODY:
                return JSONResponse({"detail": "Request payload exceeds size limit"}, status_code=413)
        except ValueError:
            return JSONResponse({"detail": "Invalid Content-Length header"}, status_code=400)
    if request.url.path.startswith("/api/") and request.url.path != "/api/login":
        token = request.cookies.get("paw", "")
        if not secrets.compare_digest(token, store.current_token()):
            return JSONResponse({"detail": "Pair this browser with the local launch token"}, status_code=401)
        if request.method != "GET" and request.headers.get("x-paw") != "1":
            return JSONResponse({"detail": "Missing request protection"}, status_code=403)
    if request.method in ("POST", "PUT", "PATCH"):
        chunks = []
        received = 0
        async for chunk in request.stream():
            received += len(chunk)
            if received > MAX_REQUEST_BODY:
                return JSONResponse({"detail": "Request payload exceeds size limit"}, status_code=413)
            chunks.append(chunk)
        request._body = b"".join(chunks)
    try:
        response = await call_next(request)
    except (ValueError, KeyError) as error:
        return JSONResponse({"detail": redact(str(error))}, status_code=400)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'"
    return response


@app.post("/api/login")
def login(body: dict, request: Request):
    valid = secrets.compare_digest(str(body.get("token", "")), store.current_token())
    retry_after = login_attempt(request.client.host if request.client else "unknown", valid)
    if retry_after:
        raise HTTPException(429, "Too many pairing attempts", headers={"Retry-After": str(retry_after)})
    if not valid:
        raise HTTPException(401, "Invalid launch token")
    response = JSONResponse({"ok": True})
    response.set_cookie("paw", store.current_token(), httponly=True, samesite="strict")
    return response


@app.post("/api/logout")
def logout():
    response = JSONResponse({"ok": True, "message": "Logged out"})
    response.delete_cookie("paw", httponly=True, samesite="strict")
    return response


@app.post("/api/rotate-token")
def rotate_session_token():
    new_token = rotate_token()
    response = JSONResponse({"ok": True, "message": "Token rotated successfully"})
    response.set_cookie("paw", new_token, httponly=True, samesite="strict")
    return response


@app.get("/api/state")
def state():
    try:
        capabilities = companion("/capabilities")
    except Exception:
        capabilities = {"error": "Companion unavailable; start both services"}
    return redact({"providers": [public(item) for item in all_objects("providers")], "agents": all_objects("agents"), "runs": all_objects("runs"), "grants": all_objects("grants"), "approvals": all_objects("approvals"), "artifacts": [{name: value for name, value in item.items() if name != "path"} for item in all_objects("artifacts")], "budgets": all_objects("budgets"), "defaults": all_objects("settings"), "provider_types": DEFAULTS, "capabilities": capabilities, "catalog": get_catalog()})


@app.post("/api/providers")
def save_provider(body: dict):
    kind = body["type"]
    if kind not in DEFAULTS:
        raise ValueError("Unknown provider type")
    url = body.get("url") or DEFAULTS[kind]
    parsed = httpx.URL(url)
    if parsed.scheme not in ("http", "https") or parsed.username or parsed.password or parsed.query:
        raise ValueError("Use an HTTP endpoint without embedded credentials or query parameters")
    previous = get("providers", body["id"]) if body.get("id") else {}
    remove_key = body.get("remove_key", False)
    if not isinstance(remove_key, bool):
        raise ValueError("remove_key must be a boolean")
    key = body.get("key") or ""
    if remove_key and key:
        raise ValueError("Choose either a replacement key or remove the saved key")
    if remove_key and not previous:
        raise ValueError("Only an existing connection can have a saved key removed")
    secret = "" if remove_key else CIPHER.encrypt(key.encode()).decode() if key else previous.get("secret", "")
    same_endpoint = previous.get("type") == kind and previous.get("url") == url
    unchanged = same_endpoint and secret == previous.get("secret", "")
    models = previous.get("models", []) if unchanged else [item for item in previous.get("models", []) if item.get("source") in ("manual", "catalog")] if same_endpoint else []
    provider = {"id": previous.get("id", str(uuid.uuid4())), "name": body["name"], "type": kind, "url": url, "secret": secret, "models": models,"last_test":previous.get('last_test') if unchanged else None,"last_discovery":previous.get('last_discovery') if unchanged else None,"archived":previous.get('archived',False)}
    return public(put("providers", provider))


def record_provider_check(original, field, result, models=None):
    with store.LOCK:
        current = get("providers", original["id"])
        if any(current.get(key) != original.get(key) for key in ("type", "url", "secret")):
            raise ValueError("Connection changed during the check; run it again")
        current[field] = result
        if models is not None:
            current["models"] = models + [item for item in current["models"] if item.get("source") in ("manual", "catalog") and item["id"] not in {model["id"] for model in models}]
        put("providers", current)


@app.post("/api/providers/{ident}/discover")
def discover(ident: str):
    provider = get("providers", ident)
    started = time.perf_counter()
    try:
        models = adapter(provider).discover()
    except Exception as error:
        detail = "Server unreachable; check URL, listening address and network" if isinstance(error, httpx.RequestError) else str(redact(str(error)))[:500] if isinstance(error, ValueError) else "Server returned an invalid model list"
        record_provider_check(provider, "last_discovery", {"ok": False, "time": time.time(), "latency_ms": round((time.perf_counter() - started) * 1000), "message": detail})
        raise ValueError(detail) from error
    record_provider_check(provider, "last_discovery", {"ok": True, "time": time.time(), "latency_ms": round((time.perf_counter() - started) * 1000), "count": len(models)}, models)
    return {"models": models, "message": "Models refreshed" if models else "Server returned an empty model list; install a model or enter an ID manually"}


@app.get("/api/providers/detect-local")
def api_detect_local():
    return {"engines": detect_local_engines()}


@app.post("/api/providers/{ident}/manual")
def manual(ident: str, body: dict):
    provider = get("providers", ident)
    provider["models"].append({"id": body["model"], "source": "manual", "tools": None, "vision": None, "streaming": None})
    return public(put("providers", provider))


@app.post("/api/providers/{ident}/catalog-add")
def add_catalog_model(ident: str, body: dict):
    provider = get("providers", ident)
    model_id = str(body.get("model", "")).strip()
    if not model_id:
        raise ValueError("Model ID required")
    catalog_entry = find_catalog_model(provider["type"], model_id)
    entry = catalog_entry.copy() if catalog_entry else {
        "id": model_id,
        "source": "catalog",
        "tools": None,
        "vision": None,
        "streaming": None
    }
    existing_ids = {m["id"] for m in provider.get("models", [])}
    if model_id not in existing_ids:
        provider.setdefault("models", []).append(entry)
        put("providers", provider)
    return public(provider)


@app.post("/api/providers/{ident}/test")
def test_provider(ident: str, body: dict):
    from openhands.sdk import LLM
    from openhands.sdk.llm import Message, TextContent
    provider=get('providers',ident)
    started=time.perf_counter()
    try:
        llm = LLM(**adapter(provider).llm_config(body["model"]), usage_id="connection-test", timeout=30, num_retries=0)
        llm.completion(messages=[Message(role="user", content=[TextContent(text="Reply OK")])])
    except Exception as error:
        detail="Inference failed: " + str(redact(str(error)))[:500]
        record_provider_check(provider,'last_test',{'ok':False,'model':body['model'],'time':time.time(),'latency_ms':round((time.perf_counter()-started)*1000),'message':detail})
        raise ValueError(detail) from error
    record_provider_check(provider,'last_test',{'ok':True,'model':body['model'],'time':time.time(),'latency_ms':round((time.perf_counter()-started)*1000)})
    return {"message": "Inference succeeded with this connection and model"}


@app.post("/api/default")
def default(body: dict):
    if get('providers',body['connection']).get('archived'):
        raise ValueError('Restore this connection before using it as the default')
    return put("settings", {"id": "default", "connection": body["connection"], "model": body["model"]})


@app.post("/api/agents")
def agent(body: dict):
    previous=get('agents',body['id']) if body.get('id') else {}
    return put("agents", {"id": body.get("id") or str(uuid.uuid4()), "name": body["name"], "instructions": body["instructions"], "connection": body.get("connection", ""), "model": body.get("model", ""), "tools": body.get("tools", ["files"]), "grants": body.get("grants", []),"archived":previous.get('archived',False)})


@app.post('/api/{kind}/{ident}/archive')
def archive(kind:str,ident:str,body:dict):
    if kind not in ('providers','agents'):
        raise HTTPException(404,'Unknown archive collection')
    item=get(kind,ident)
    item['archived']=body.get('archived',True) is not False
    put(kind,item)
    return public(item) if kind=='providers' else item


@app.post("/api/grants")
def grant(body: dict):
    root = Path(body.get("root") or str(STATE)).resolve()
    if not root.is_dir():
        raise ValueError("Select an existing directory")
    if body["mode"] not in ("host", "sandbox"):
        raise ValueError("Unknown execution mode")
    shared = str(Path(body["shared"]).resolve()) if body.get("shared") else ""
    if shared and (not Path(shared).is_dir() or "," in shared):
        raise ValueError("Select an existing shared directory without commas in its path")
    domains = [item.strip().lower().rstrip(".") for item in (body.get("allowed_domains") or "").split(",") if item.strip()]
    if domains and body["mode"] != "sandbox":
        raise ValueError("Browser domain restrictions require a sandbox workspace")
    import re
    if any(not re.fullmatch(r"(?:\*\.)?[a-z0-9-]+(?:\.[a-z0-9-]+)*", item) for item in domains):
        raise ValueError("Enter comma-separated domain names, optionally starting with *.")
    return put("grants", {"id": str(uuid.uuid4()), "mode": body["mode"], "root": str(root), "shared": shared, "capabilities": body["capabilities"], "allowed_domains": domains, "revoked": False})


@app.post("/api/grants/{ident}/revoke")
def revoke(ident: str):
    grant = get("grants", ident)
    grant["revoked"] = True
    put("grants", grant)
    try:
        companion("/revoke/" + ident, {})
    except Exception:
        pass
    for run in all_objects("runs"):
        if run.get("grant") == ident and run.get("status") in ("running", "queued", "approval", "paused", "review"):
            stop(run["id"])
    return grant


def new_run(body, parent=None):
    idempotency_key = body.get("idempotency_key")
    if idempotency_key:
        existing = next((r for r in all_objects("runs") if r.get("idempotency_key") == idempotency_key), None)
        if existing:
            return existing
    profile = get("agents", body["agent"])
    if profile.get('archived'):
        raise ValueError('This agent is archived. Restore it before starting work.')
    grant = get("grants", body["grant"])
    if grant["revoked"] or grant["id"] not in profile["grants"]:
        raise ValueError("Agent lacks this workspace grant")
    if grant["mode"] == "host" and not Path(grant["root"]).is_dir():
        raise ValueError("The authorized project folder no longer exists. Create a new workspace grant for an existing folder.")
    if grant["mode"] == "sandbox":
        status = companion("/capabilities").get("sandbox",{})
        if not status.get("ready"):
            raise ValueError(status.get("reason","Companion could not confirm Docker sandbox readiness"))
    default = next((item for item in all_objects("settings") if item["id"] == "default"), {})
    connection = profile["connection"] or default.get("connection", "")
    model = profile["model"] or default.get("model", "")
    if not parent:
        connection = body.get("connection") or connection
        model = body.get("model") or model
    if not model.strip():
        raise ValueError("Choose a model for this task or configure a global default")
    if not connection:
        raise ValueError("Choose a provider connection for this task")
    if get("providers", connection).get('archived'):
        raise ValueError('This connection is archived. Choose an active connection or restore it.')
    tools = set(profile["tools"])
    if parent:
        parent = get("runs", parent["id"])
        if parent["status"] != "running":
            raise ValueError("Parent is no longer running")
        if "delegate" not in parent.get("tools", []):
            raise ValueError("Parent lacks delegation authority")
        tools &= set(parent["tools"])
        if body["grant"] != parent["grant"] or parent["depth"] >= 2:
            raise ValueError("Delegation exceeds parent authority")
    run = {"id": str(uuid.uuid4()), "agent": profile["id"], "connection": connection, "model": model, "grant": grant["id"], "mode": grant["mode"], "machine": os.uname().nodename, "task": body["task"], "status": "queued", "tools": sorted(tools), "depth": parent["depth"] + 1 if parent else 0, "parent": parent["id"] if parent else None, "created": time.time()}
    run["root_run"] = parent.get("root_run", parent["id"]) if parent else run["id"]
    run["conversation"] = body.get("conversation") or run["id"]
    run["workspace_id"] = run["conversation"] if run["mode"]=="sandbox" and not parent else run["id"]
    run["context"] = body.get("context", "")
    run["idempotency_key"] = idempotency_key
    put("runs", run)
    event(run["id"], "created", run)
    start_worker(run["id"])
    return run


def start_worker(ident):
    process = subprocess.Popen([sys.executable, "-m", "workbench.worker", ident], start_new_session=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    WORKERS[ident] = process
    put("workers", {"id": ident, "pid": process.pid})
    threading.Thread(target=watch_worker,args=(ident,process),daemon=True).start()


def watch_worker(ident, process):
    returncode = process.wait()
    if get("runs", ident).get("status") not in ("queued", "running", "approval"):
        if WORKERS.get(ident) is process:
            WORKERS.pop(ident, None)
        return
    history = events(ident)
    uncertain = any(item["kind"] in ("action_started", "tool_call") and item["data"].get("op") not in ("read", "list") for item in history)
    cleanup_confirmed = False
    try:
        cleanup_confirmed = companion("/stop/" + ident, {}, timeout=5).get("stopped") is True
    except Exception:
        pass
    status = "review" if uncertain or not cleanup_confirmed else "failed"
    stop_reason = "interrupted" if status == "review" else "worker_crash"
    changed = transition_run(ident, ("queued", "running", "approval"), status, {"stop_reason": stop_reason})
    if changed:
        for approval in all_objects("approvals"):
            if approval.get("run") == ident and approval.get("status") in ("pending", "approved"):
                approval["status"] = "cancelled"
                put("approvals", approval)
        if not cleanup_confirmed:
            event(ident, "stop_incomplete", "The companion could not confirm tool cleanup; review required.")
        event(ident, "error", {"message": "Worker exited unexpectedly. No actions were replayed. Inspect actual results before starting replacement work.", "exit_status": returncode, "review_required": status == "review"})
    if WORKERS.get(ident) is process:
        WORKERS.pop(ident, None)


@app.post("/api/runs")
def launch(body: dict):
    return new_run({name:body[name] for name in ("agent","grant","task","connection","model","idempotency_key") if name in body})


@app.post("/api/runs/reconcile")
def api_reconcile():
    reconciled = reconcile_runs()
    return {"reconciled": len(reconciled), "runs": reconciled}


@app.get("/api/conversations/{ident}")
def conversation_history(ident: str):
    messages = []
    runs = sorted((run for run in all_objects("runs") if run.get("conversation",run["id"]) == ident), key=lambda run:run["created"])
    for run in runs:
        messages.append({"id":run["id"],"run":run["id"],"role":"user","text":run["task"]})
        for item in events(run["id"]):
            data = item["data"]
            if item["kind"] == "sdk" and data.get("kind") == "MessageEvent" and data.get("source") == "agent":
                text = "\n".join(part["text"] for part in data.get("llm_message",{}).get("content",[]) if part.get("type") == "text")
                if text:
                    messages.append({"id":str(item["seq"]),"run":run["id"],"role":"assistant","text":text})
            elif item['kind']=='sdk' and data.get('kind')=='ActionEvent' and data.get('action',{}).get('kind')=='FinishAction':
                text=data['action'].get('message','')
                if text:
                    messages.append({'id':str(item['seq']),'run':run['id'],'role':'assistant','text':text})
    return {"messages":messages,"runs":[run["id"] for run in runs]}


@app.post("/api/runs/{ident}/followup")
def followup(ident: str, body: dict):
    previous = get("runs", ident)
    if previous["status"] not in ('completed','reviewed'):
        raise ValueError("Review interrupted work before creating a new task; follow-up is available after completion")
    transcript = [{"kind":item["kind"],"data":item["data"]} for item in events(ident) if item["kind"] in ("tool_result","tool_error","review_resolution") or (item["kind"] == "sdk" and item["data"].get("kind") in ('MessageEvent','ActionEvent'))]
    context = previous.get("context", "")[-16000:] + "\nPrevious task: " + previous["task"] + "\nObserved history: " + json.dumps(transcript)[-24000:]
    return new_run({"agent":previous["agent"],"grant":previous["grant"],"connection":previous["connection"],"model":previous["model"],"task":body["task"],"conversation":previous.get("conversation",ident),"context":context})


@app.post('/api/runs/{ident}/resolve-review')
def resolve_review(ident:str,body:dict):
    run=get('runs',ident)
    if run['status'] not in ('review','failed','stopped'):
        raise ValueError('Only interrupted, failed, or stopped runs can be reviewed')
    note=str(body.get('note','')).strip()
    if not note or len(note)>8000:
        raise ValueError('Record what you inspected and the observed outcome (up to 8000 characters)')
    if any(child.get('parent')==ident and child['status'] in ('queued','running','approval','paused') for child in all_objects('runs')):
        raise ValueError('Stop delegated work before closing this review')
    kill_worker(ident)
    # Do not enable replacement work while an earlier command may still be running.
    try:
        result=companion('/stop/'+ident,{},timeout=20)
    except Exception as error:
        raise ValueError('Companion could not confirm cleanup. Restore it and use Stop before resolving this review.') from error
    if not result.get('stopped'):
        raise ValueError('Companion did not confirm cleanup; review remains open')
    resolution={'note':redact(note),'time':time.time(),'previous_status':run['status'],'actions_replayed':False}
    changed=transition_run(ident,('review','failed','stopped'),'reviewed',{'review_resolution':resolution})
    if changed is None:
        raise ValueError('Run state changed; reload before resolving the review')
    for approval in all_objects('approvals'):
        if approval['run']==ident and approval['status'] in ('pending','approved'):
            approval['status']='cancelled'
            put('approvals',approval)
    event(ident,'review_resolution',resolution)
    return changed


@app.post("/api/runs/{ident}/stop")
def stop(ident: str):
    return stop_run(ident)


def stop_run(ident: str, cleanup_timeout: float | None = None):
    run = transition_run(ident, ("queued", "running", "approval", "paused", "review"), "stopped", {"stop_reason": "user_cancelled"})
    if run is None:
        return get("runs", ident)
    for approval in all_objects("approvals"):
        if approval.get("run") == ident and approval.get("status") in ("pending", "approved"):
            approval["status"] = "cancelled"
            put("approvals", approval)
    for child in all_objects("runs"):
        if child.get("parent") == ident and child.get("status") in ("queued", "running", "approval", "paused", "review"):
            stop_run(child["id"], cleanup_timeout)
    try:
        result = companion("/stop/" + ident, {}) if cleanup_timeout is None else companion("/stop/" + ident, {}, timeout=cleanup_timeout)
        confirmed = result.get("stopped") is True
        if not confirmed:
            raise ValueError("Companion did not confirm cleanup")
    except Exception:
        transition_run(ident, ("stopped",), "review")
        event(ident, "stop_incomplete", "Worker stop requested; companion could not confirm tool cleanup. Review interrupted effects and restore the companion.")
    finally:
        kill_worker(ident)
    current = get("runs", ident)
    event(ident, "stopped", {"status": current["status"], "worker": "cancellation requested"})
    return current


@app.post("/api/runs/{ident}/browser-control")
def browser_control(ident:str,body:dict):
    run=get("runs",ident)
    grant=get("grants",run["grant"])
    if run["mode"]!="sandbox" or "browser" not in run["tools"] or "browser" not in grant["capabilities"] or grant["revoked"]:
        raise ValueError("This run does not have sandbox browser authority")
    operation=body.get("operation")
    if operation=="begin":
        updated = transition_run(ident, ("completed",), "paused")
        if updated is None:
            raise ValueError("Browser control is available after the agent finishes, so user and agent actions cannot overlap")
        event(ident,"browser_control","User took control of the sandbox browser")
        return {"status": "paused"}
    elif operation=="end":
        updated = transition_run(ident, ("paused",), "completed")
        if updated is None:
            raise ValueError("Browser control is not active")
        event(ident,"browser_control","User returned browser control; inspect the current page before new work")
        return {"status":"completed"}
    if get("runs",ident)["status"]!="paused":
        raise ValueError("Take browser control before sending actions")
    if operation not in ("begin", "inspect", "navigate", "click", "type", "press", "scroll", "new_tab", "switch_tab", "close_tab", "tabs"):
        raise ValueError("Unsupported browser control action")
    action = {"op": "browser", "manual": True, "browser_action": operation if operation in ("click", "type", "press", "scroll", "new_tab", "switch_tab", "close_tab", "tabs") else "inspect"}
    if operation in ("navigate", "new_tab") and body.get("url"):
        url = str(body.get("url", ""))
        if httpx.URL(url).scheme not in ("http", "https"):
            raise ValueError("Browser control accepts HTTP and HTTPS navigation URLs")
        action["url"] = url
    if operation == "click":
        action["x"] = max(0, min(10000, int(body["x"])))
        action["y"] = max(0, min(10000, int(body["y"])))
    if operation == "type":
        action["content"] = str(body.get("text", ""))[:10000]
    if operation == "press":
        key = str(body.get("key", ""))
        if key not in ("Enter", "Tab", "Backspace", "Escape", "ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight"):
            raise ValueError("Unsupported browser key")
        action["key"] = key
    if operation == "scroll":
        action["delta_y"] = float(body.get("delta_y", 300))
        action["delta_x"] = float(body.get("delta_x", 0))
    if operation in ("switch_tab", "close_tab"):
        action["tab_id"] = int(body.get("tab_id", 0))
    approval={"id":str(uuid.uuid4()),"run":ident,"action":action,"status":"approved","source":"explicit-user-browser-control"}
    put("approvals",approval)
    event(ident,"browser_control_action",action)
    result=companion("/execute/"+ident,action|{"approval":approval["id"]})
    event(ident,"tool_result",result["result"])
    return {"status":"paused","result":result["result"]}


def kill_worker(ident):
    try:
        process_id = get("workers", ident)["pid"]
        command = Path(f"/proc/{process_id}/cmdline").read_bytes().split(b"\0")
        if b"workbench.worker" in command and ident.encode() in command:
            os.killpg(process_id, signal.SIGTERM)
    except (KeyError, FileNotFoundError, ProcessLookupError):
        pass


@app.get("/api/runs/{ident}/events")
async def stream(ident: str, request: Request, after: int = 0):
    get("runs",ident)
    cursor_start=max(after,int(request.headers.get("last-event-id","0")))
    async def generate():
        cursor = cursor_start
        while True:
            for item in events(ident, cursor):
                cursor = item["seq"]
                yield f"id: {cursor}\ndata: {json.dumps(item)}\n\n"
            yield ": keepalive\n\n"
            await asyncio.sleep(0.5)
    return StreamingResponse(generate(), media_type="text/event-stream")


@app.get("/api/runs/{ident}/tree")
def run_tree(ident: str):
    run = get("runs", ident)
    root_id = run.get("root_run", ident)
    all_runs = all_objects("runs")
    all_agents = {a["id"]: a for a in all_objects("agents")}
    all_artifacts = all_objects("artifacts")

    def build_node(r_id):
        r = next((item for item in all_runs if item["id"] == r_id), None)
        if not r:
            return None
        agent_obj = all_agents.get(r.get("agent"), {})
        node_artifacts = [
            {"id": a["id"], "name": a.get("name", ""), "created": a.get("created", 0)}
            for a in all_artifacts if a.get("run") == r_id
        ]
        children = [build_node(child["id"]) for child in all_runs if child.get("parent") == r_id]
        children = [c for c in children if c is not None]
        return {
            "id": r["id"],
            "task": r.get("task", ""),
            "agent": agent_obj.get("name", "Unknown agent"),
            "agent_id": r.get("agent"),
            "status": r.get("status"),
            "tools": r.get("tools", []),
            "depth": r.get("depth", 0),
            "created": r.get("created", 0),
            "stop_reason": r.get("stop_reason"),
            "outcome": r.get("outcome"),
            "verification": r.get("verification"),
            "artifacts": node_artifacts,
            "children": children,
        }

    return build_node(root_id)


@app.post("/api/approvals/{ident}")
def approve(ident: str, body: dict):
    approval = get("approvals", ident)
    if approval["status"] != "pending":
        raise ValueError("Approval already resolved")
    if get("runs", approval["run"])["status"] != "running":
        raise ValueError("This run is no longer running")
    approval["status"] = "approved" if body.get("approved") else "denied"
    put("approvals", approval)
    event(approval["run"], "decision", {"id": ident, "status": approval["status"]})
    return approval


@app.get("/api/artifacts/{ident}")
def artifact(ident: str):
    try:
        item = get("artifacts", ident)
        path = artifact_path(item)
    except (KeyError, ValueError) as error:
        raise HTTPException(404, str(error)) from error
    return FileResponse(path, filename=item["name"], media_type="application/octet-stream")


@app.get("/api/artifacts/{ident}/preview")
def preview(ident: str):
    try:
        item = get("artifacts", ident)
        path = artifact_path(item)
    except (KeyError, ValueError) as error:
        raise HTTPException(404, str(error)) from error
    name = (item.get("name") or "").lower()
    with open(path, "rb") as stream:
        header = stream.read(16)
    if header.startswith(b"\x89PNG\r\n\x1a\n"):
        media_type = "image/png"
    elif header.startswith(b"\xff\xd8\xff"):
        media_type = "image/jpeg"
    elif header.startswith(b"RIFF") and header[8:12] == b"WEBP":
        media_type = "image/webp"
    elif header.startswith((b"GIF87a", b"GIF89a")):
        media_type = "image/gif"
    elif name.endswith(".svg") and b"<svg" in header.lower():
        media_type = "image/svg+xml"
    else:
        raise HTTPException(415, "Only safe image previews (PNG, JPEG, WebP, GIF, SVG) are supported")
    return FileResponse(path, media_type=media_type)


@app.get("/api/artifacts/{ident}/text")
def artifact_text(ident: str):
    try:
        item = get("artifacts", ident)
        path = artifact_path(item)
    except (KeyError, ValueError) as error:
        raise HTTPException(404, str(error)) from error
    size = path.stat().st_size
    MAX_TEXT_PREVIEW = 500_000
    with open(path, "rb") as stream:
        raw = stream.read(MAX_TEXT_PREVIEW + 1)
    truncated = len(raw) > MAX_TEXT_PREVIEW
    text = raw[:MAX_TEXT_PREVIEW].decode("utf-8", errors="replace")
    return {
        "id": ident,
        "name": item.get("name", "artifact"),
        "content": text,
        "size": size,
        "truncated": truncated,
    }




@app.get("/api/diagnostics")
def api_diagnostics():
    from .diagnostics import get_diagnostics_snapshot
    return get_diagnostics_snapshot(store.STATE)


@app.get("/api/incidents")
def api_incidents(status: str | None = None):
    from .incidents import list_incidents
    return list_incidents(status=status)


@app.post("/api/incidents/{ident}/ack")
def api_ack_incident(ident: str):
    from .incidents import ack_incident
    try:
        return ack_incident(ident)
    except (KeyError, ValueError):
        raise HTTPException(status_code=404, detail="Incident not found")


@app.post("/api/incidents/{ident}/resolve")
def api_resolve_incident(ident: str):
    from .incidents import resolve_incident
    try:
        return resolve_incident(ident)
    except (KeyError, ValueError):
        raise HTTPException(status_code=404, detail="Incident not found")


@app.get("/api/export/scrubbed")
def api_export_scrubbed():
    from .scrubbed_export import create_scrubbed_export
    data = create_scrubbed_export(store.STATE)
    json_bytes = json.dumps(data, indent=2).encode("utf-8")
    return Response(
        content=json_bytes,
        media_type="application/json",
        headers={"Content-Disposition": 'attachment; filename="desk-yantra-diagnostics-export.json"'},
    )


@app.get("/api/retention/status")
def api_retention_status(older_than_days: int = 30):
    from .retention import inspect_retention
    try:
        return inspect_retention(older_than_days=older_than_days)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/retention/prune")
def api_retention_prune(payload: dict = Body(default={})):
    from .retention import prune_retention
    days = payload.get("older_than_days", 30)
    try:
        return prune_retention(older_than_days=days)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/metrics")
def api_metrics():
    from .metrics import get_metrics
    return get_metrics()


if Path("dist").exists():
    app.mount("/", StaticFiles(directory="dist", html=True), name="web")
