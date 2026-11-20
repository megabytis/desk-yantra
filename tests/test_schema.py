import json
import os
import sqlite3
import subprocess
import sys


def run_import(path):
    return subprocess.run([sys.executable, "-c", "from workbench import store; print(store.DB.execute('PRAGMA user_version').fetchone()[0])"],
                          env=os.environ | {"PAW_STATE": str(path)}, capture_output=True, text=True)


def test_legacy_schema_migrates_without_losing_objects_or_events(tmp_path):
    db = sqlite3.connect(tmp_path / "workbench.db")
    db.execute("CREATE TABLE objects (kind TEXT, id TEXT, body TEXT, PRIMARY KEY(kind,id))")
    db.execute("CREATE TABLE events (seq INTEGER PRIMARY KEY AUTOINCREMENT, run TEXT, time REAL, kind TEXT, body TEXT)")
    db.execute("INSERT INTO objects VALUES (?,?,?)", ("runs", "legacy", json.dumps({"id": "legacy", "status": "completed"})))
    db.execute("INSERT INTO events (run,time,kind,body) VALUES (?,?,?,?)", ("legacy", 1, "result", json.dumps({"ok": True})))
    db.commit()
    db.close()
    result = run_import(tmp_path)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "1"
    db = sqlite3.connect(tmp_path / "workbench.db")
    assert json.loads(db.execute("SELECT body FROM objects WHERE id='legacy'").fetchone()[0])["status"] == "completed"
    assert json.loads(db.execute("SELECT body FROM events WHERE run='legacy'").fetchone()[0])["ok"] is True
    assert db.execute("SELECT name FROM sqlite_master WHERE type='index' AND name='events_run_sequence'").fetchone()
    db.close()


def test_future_schema_is_rejected_without_downgrade(tmp_path):
    db = sqlite3.connect(tmp_path / "workbench.db")
    db.execute("PRAGMA user_version=2")
    db.close()
    result = run_import(tmp_path)
    assert result.returncode != 0
    assert "newer than this Desk Yantra build" in result.stderr
    db = sqlite3.connect(tmp_path / "workbench.db")
    assert db.execute("PRAGMA user_version").fetchone()[0] == 2
    assert db.execute("SELECT count(*) FROM sqlite_master WHERE type='table'").fetchone()[0] == 0
    db.close()


def test_malformed_legacy_schema_is_not_stamped_current(tmp_path):
    db = sqlite3.connect(tmp_path / "workbench.db")
    db.execute("CREATE TABLE objects (kind TEXT, id TEXT)")
    db.commit()
    db.close()
    result = run_import(tmp_path)
    assert result.returncode != 0
    assert "incompatible layout" in result.stderr
    db = sqlite3.connect(tmp_path / "workbench.db")
    assert db.execute("PRAGMA user_version").fetchone()[0] == 0
    assert db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='events'").fetchone() is None
    db.close()
