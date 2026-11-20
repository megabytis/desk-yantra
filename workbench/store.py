import json
import os
import secrets
import sqlite3
import threading
import time
from pathlib import Path

from cryptography.fernet import Fernet

STATE = Path(os.environ.get("PAW_STATE", ".state")).resolve()
STATE.mkdir(mode=0o700, parents=True, exist_ok=True)
os.chmod(STATE, 0o700)


def private_file(name, create):
    path = STATE / name
    if not path.exists():
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, "w") as stream:
            stream.write(create())
    return path.read_text().strip()


TOKEN = private_file("token", lambda: secrets.token_urlsafe(32))


def rotate_token():
    global TOKEN
    new_token = secrets.token_urlsafe(32)
    path = STATE / "token"
    descriptor = os.open(path, os.O_WRONLY | os.O_TRUNC | os.O_CREAT, 0o600)
    with os.fdopen(descriptor, "w") as stream:
        stream.write(new_token)
    TOKEN = new_token
    return new_token
ENCRYPTION_KEY = private_file("encryption.key", lambda: Fernet.generate_key().decode())
CIPHER = Fernet(ENCRYPTION_KEY)
LOCK = threading.RLock()
DB = sqlite3.connect(STATE / "workbench.db", check_same_thread=False)
DB.execute("PRAGMA journal_mode=WAL")
DB.executescript("""
CREATE TABLE IF NOT EXISTS objects (kind TEXT, id TEXT, body TEXT, PRIMARY KEY(kind,id));
CREATE TABLE IF NOT EXISTS events (seq INTEGER PRIMARY KEY AUTOINCREMENT, run TEXT, time REAL, kind TEXT, body TEXT);
CREATE INDEX IF NOT EXISTS events_run_sequence ON events(run,seq);
""")


def put(kind, value):
    with LOCK:
        DB.execute("INSERT OR REPLACE INTO objects VALUES (?,?,?)", (kind, value["id"], json.dumps(value)))
        DB.commit()
    return value


def get(kind, ident):
    with LOCK:
        row = DB.execute("SELECT body FROM objects WHERE kind=? AND id=?", (kind, ident)).fetchone()
    if not row:
        raise KeyError(f"Unknown {kind}")
    return json.loads(row[0])


def all_objects(kind):
    with LOCK:
        return [json.loads(row[0]) for row in DB.execute("SELECT body FROM objects WHERE kind=?", (kind,))]


def transition_run(ident,expected,status,extra=None):
    with LOCK:
        DB.execute('BEGIN IMMEDIATE')
        try:
            row=DB.execute("SELECT body FROM objects WHERE kind='runs' AND id=?",(ident,)).fetchone()
            run=json.loads(row[0]) if row else None
            if run is None or run.get('status') not in expected:
                DB.rollback()
                return None
            run.update(extra or {})
            run['status']=status
            DB.execute("UPDATE objects SET body=? WHERE kind='runs' AND id=?",(json.dumps(run),ident))
            DB.commit()
            return run
        except Exception:
            DB.rollback()
            raise


def sensitive_values():
    values = [TOKEN, ENCRYPTION_KEY]
    for provider in all_objects("providers"):
        if provider.get("secret"):
            secret = CIPHER.decrypt(provider["secret"].encode()).decode()
            if secret:
                values.append(secret)
    return values


def redact(value):
    secrets = sensitive_values()
    def clean(item):
        if isinstance(item, str):
            for secret in secrets:
                item = item.replace(secret, "[REDACTED]")
            return item
        if isinstance(item, list):
            return [clean(child) for child in item]
        if isinstance(item, dict):
            return {clean(name):clean(child) for name,child in item.items()}
        return item
    return clean(json.loads(json.dumps(value, default=str)))


def safe_stream_prefix(buffer):
    secrets = sensitive_values()
    cutoff = max(0, len(buffer) - max(map(len, secrets)))
    for secret in secrets:
        start = buffer.find(secret)
        while start >= 0:
            if start < cutoff < start + len(secret):
                cutoff = start
            start = buffer.find(secret, start+1)
    return buffer[:cutoff], buffer[cutoff:]


def event(run, kind, value):
    with LOCK:
        DB.execute("INSERT INTO events(run,time,kind,body) VALUES (?,?,?,?)", (run, time.time(), kind, json.dumps(redact(value))))
        DB.commit()


def events(run, after=0):
    with LOCK:
        rows = DB.execute("SELECT seq,time,kind,body FROM events WHERE run=? AND seq>? ORDER BY seq", (run, after)).fetchall()
    return [dict(seq=row[0], time=row[1], kind=row[2], data=json.loads(row[3])) for row in rows]


def claim_approval(ident, run, action):
    with LOCK:
        DB.execute("BEGIN IMMEDIATE")
        try:
            row = DB.execute("SELECT body FROM objects WHERE kind='approvals' AND id=?", (ident,)).fetchone()
            approval = json.loads(row[0]) if row else {}
            if approval.get("status") != "approved" or approval.get("run") != run or approval.get("action") != action:
                raise ValueError("Exact unconsumed approval required")
            approval["status"] = "consumed"
            DB.execute("UPDATE objects SET body=? WHERE kind='approvals' AND id=?", (json.dumps(approval), ident))
            DB.commit()
        except Exception:
            DB.rollback()
            raise


def consume_budget(root, limit=90):
    with LOCK:
        DB.execute("BEGIN IMMEDIATE")
        try:
            row = DB.execute("SELECT body FROM objects WHERE kind='budgets' AND id=?", (root,)).fetchone()
            budget = json.loads(row[0]) if row else {"id": root, "used": 0}
            if budget["used"] >= limit:
                raise ValueError("Task-wide tool budget exhausted")
            budget["used"] += 1
            DB.execute("INSERT OR REPLACE INTO objects VALUES ('budgets',?,?)", (root, json.dumps(budget)))
            DB.commit()
        except Exception:
            DB.rollback()
            raise


def get_budget(root):
    with LOCK:
        row = DB.execute("SELECT body FROM objects WHERE kind='budgets' AND id=?", (root,)).fetchone()
        return json.loads(row[0]) if row else {"id": root, "used": 0}


def consume_output_quota(run_id, count, limit=500_000):
    with LOCK:
        DB.execute("BEGIN IMMEDIATE")
        try:
            row = DB.execute("SELECT body FROM objects WHERE kind='output_quotas' AND id=?", (run_id,)).fetchone()
            quota = json.loads(row[0]) if row else {"id": run_id, "used": 0}
            remaining = max(0, limit - quota["used"])
            to_consume = min(count, remaining)
            quota["used"] += to_consume
            DB.execute("INSERT OR REPLACE INTO objects VALUES ('output_quotas',?,?)", (run_id, json.dumps(quota)))
            DB.commit()
            return to_consume, quota["used"] >= limit
        except Exception:
            DB.rollback()
            raise


def get_output_quota(run_id):
    with LOCK:
        row = DB.execute("SELECT body FROM objects WHERE kind='output_quotas' AND id=?", (run_id,)).fetchone()
        return json.loads(row[0]) if row else {"id": run_id, "used": 0}
