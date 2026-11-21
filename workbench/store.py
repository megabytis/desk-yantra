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


def current_token():
    """Read the shared token so separately running services see rotations."""
    return (STATE / "token").read_text().strip()


def rotate_token():
    global TOKEN
    new_token = secrets.token_urlsafe(32)
    temporary = STATE / ("token." + secrets.token_hex(8) + ".tmp")
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "w") as stream:
            stream.write(new_token)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, STATE / "token")
    finally:
        temporary.unlink(missing_ok=True)
    TOKEN = new_token
    return new_token


ENCRYPTION_KEY = private_file("encryption.key", lambda: Fernet.generate_key().decode())
CIPHER = Fernet(ENCRYPTION_KEY)
LOCK = threading.RLock()
SCHEMA_VERSION = 1
DB = sqlite3.connect(STATE / "workbench.db", check_same_thread=False)


def validate_schema(database):
    expected = {"objects": ("kind", "id", "body"), "events": ("seq", "run", "time", "kind", "body")}
    for table, columns in expected.items():
        actual = tuple(row[1] for row in database.execute(f"PRAGMA table_info({table})"))
        if actual != columns:
            raise RuntimeError(f"State table {table} has an incompatible layout")


def initialize_schema(database):
    version = database.execute("PRAGMA user_version").fetchone()[0]
    if version > SCHEMA_VERSION:
        raise RuntimeError(f"State schema {version} is newer than this Desk Yantra build ({SCHEMA_VERSION})")
    if version == 0:
        database.execute("BEGIN IMMEDIATE")
        try:
            database.execute("CREATE TABLE IF NOT EXISTS objects (kind TEXT, id TEXT, body TEXT, PRIMARY KEY(kind,id))")
            database.execute("CREATE TABLE IF NOT EXISTS events (seq INTEGER PRIMARY KEY AUTOINCREMENT, run TEXT, time REAL, kind TEXT, body TEXT)")
            validate_schema(database)
            database.execute("CREATE INDEX IF NOT EXISTS events_run_sequence ON events(run,seq)")
            database.execute("PRAGMA user_version=1")
            database.commit()
        except Exception:
            database.rollback()
            raise
    validate_schema(database)
    database.execute("PRAGMA journal_mode=WAL")


initialize_schema(DB)


def storage_ready():
    try:
        with LOCK:
            return DB.execute("SELECT 1").fetchone() == (1,)
    except sqlite3.Error:
        return False

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


def touch_heartbeat(run_id, pid=None):
    with LOCK:
        heartbeat = {"id": run_id, "time": time.time(), "pid": pid or os.getpid()}
        DB.execute("INSERT OR REPLACE INTO objects VALUES ('heartbeats',?,?)", (run_id, json.dumps(heartbeat)))
        DB.commit()
    return heartbeat


def get_heartbeat(run_id):
    with LOCK:
        row = DB.execute("SELECT body FROM objects WHERE kind='heartbeats' AND id=?", (run_id,)).fetchone()
        return json.loads(row[0]) if row else None


def delete_heartbeat(run_id):
    with LOCK:
        DB.execute("DELETE FROM objects WHERE kind='heartbeats' AND id=?", (run_id,))
        DB.commit()



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


def artifact_path(item):
    """Resolve a stored artifact only inside the private artifact directory."""
    import stat

    root = STATE / "artifacts"
    path = Path(item["path"])
    if root.is_symlink() or path.parent != root or path.is_symlink():
        raise ValueError("Artifact path is outside private artifact storage")
    try:
        info = path.stat()
    except FileNotFoundError as error:
        raise ValueError("Artifact file is missing") from error
    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
        raise ValueError("Artifact is not a private regular file")
    return path


def sensitive_values():
    values = [TOKEN, current_token(), ENCRYPTION_KEY]
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
