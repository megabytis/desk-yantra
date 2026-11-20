"""Local Chromium functional fixture; does not establish Docker isolation."""
import json
import os
import socket
import subprocess
import sys
import tempfile
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


class Page(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"""<title>Fixture page</title><h1>Browser fixture</h1><input id="text"><button id="copy" onclick='document.querySelector("h1").textContent=document.querySelector("input").value'>Copy</button>""")

    def log_message(self,*args):
        pass


server = ThreadingHTTPServer(("127.0.0.1",0),Page)
threading.Thread(target=server.serve_forever,daemon=True).start()
with socket.socket() as probe:
    probe.bind(("127.0.0.1",0))
    port = probe.getsockname()[1]
with tempfile.TemporaryDirectory(prefix="paw-browser-") as directory:
    environment = os.environ | {"PAW_SANDBOX_ROOT":directory,"PAW_BROWSER_PORT":str(port)}
    browser = subprocess.Popen([sys.executable,"sandbox/browser_service.py"],env=environment,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
    try:
        for attempt in range(100):
            try:
                with socket.create_connection(("127.0.0.1",port),timeout=.2):
                    break
            except OSError:
                if browser.poll() is not None:
                    raise RuntimeError(browser.stderr.read().decode())
                time.sleep(.1)
        def action(body):
            result = subprocess.run([sys.executable,"sandbox/action.py",json.dumps(body)],env=environment,capture_output=True,text=True,check=True)
            return result.stdout
        first = json.loads(action({"op":"browser","url":f"http://127.0.0.1:{server.server_port}"}))
        assert "Browser fixture" in first["text"]
        action({"op":"browser","selector":"#text","content":"Actual interaction"})
        final = json.loads(action({"op":"browser","selector":"#copy"}))
        assert "Actual interaction" in final["text"]
        action({"op":"browser","selector":"#text"})
        action({"op":"browser","browser_action":"press","key":"ControlOrMeta+A"})
        action({"op":"browser","browser_action":"type","content":"Manual browser input"})
        controlled = json.loads(action({"op":"browser","selector":"#copy"}))
        assert "Manual browser input" in controlled["text"]
        action({"op":"write","path":"page.txt","content":final["text"]})
        assert "Actual interaction" in Path(directory,"page.txt").read_text()
        assert Path(directory,"browser.png").read_bytes().startswith(b"\x89PNG")
        print("PASS local Chromium fixture: navigation, persistent fill/click, keyboard takeover, screenshot, file creation")
    finally:
        browser.terminate()
        browser.wait(timeout=10)
        server.shutdown()
