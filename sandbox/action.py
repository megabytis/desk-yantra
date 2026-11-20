import json
import sys
import os
from pathlib import Path
from playwright.sync_api import sync_playwright

action = json.loads(sys.argv[1])
root = Path(os.environ.get("PAW_SANDBOX_ROOT", "/workspace")).resolve()
shared=Path('/shared')
def readable(path):
    return path.is_relative_to(root) or (shared.is_dir() and path.is_relative_to(shared))
if action["op"] == "list":
    path=(root/action.get('path','.')).resolve()
    if not readable(path):
        raise ValueError('Path outside workspace')
    entries=sorted(path.iterdir())
    print(json.dumps({'path':action.get('path','.'),'entries':[{'name':entry.name,'kind':'symlink' if entry.is_symlink() else 'directory' if entry.is_dir() else 'file'} for entry in entries[:200]],'truncated':len(entries)>200}))
elif action["op"] in ("read", "write"):
    path = (root / action["path"]).resolve()
    if not path.is_relative_to(root) and not (action['op']=='read' and readable(path)):
        raise ValueError("Path outside workspace")
    if action["op"] == "write":
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(action["content"])
        print("File written")
    else:
        sys.stdout.write(path.read_text()[:1000000])
elif action["op"] == "browser":
    import urllib.request
    request = urllib.request.Request("http://127.0.0.1:" + os.environ.get("PAW_BROWSER_PORT", "9111"), data=json.dumps(action).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=45) as response:
        print(response.read().decode())
else:
    raise ValueError("Unsupported sandbox operation")
