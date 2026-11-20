"""Explicitly invoked live capture probe. Never run automatically in CI."""
import tempfile
import uuid
from pathlib import Path

from fastapi.testclient import TestClient
from workbench.companion import app, capabilities
from workbench.store import TOKEN, get, put

ident = str(uuid.uuid4())
root = tempfile.mkdtemp(prefix="paw-desktop-")
put("grants", {"id": ident, "root": root, "mode": "host", "capabilities": ["screen"], "revoked": False})
put("runs", {"id": ident, "grant": ident, "mode": "host", "status": "running", "tools": ["screen"]})
action = {"op": "screen"}
put("approvals", {"id": ident, "run": ident, "action": action, "status": "approved"})
client = TestClient(app, headers={"Authorization": "Bearer " + TOKEN})
response = client.post("/execute/" + ident, json=action | {"approval": ident})
print("Capture HTTP status:", response.status_code)
if response.is_success:
    artifact = get("artifacts", ident + "-screen")
    print("PNG signature:", Path(artifact["path"]).read_bytes()[:8] == b"\x89PNG\r\n\x1a\n")
    print("Capture stored in private PAW_STATE; content not printed or uploaded.")
print("Input:", capabilities()["input_detail"])
