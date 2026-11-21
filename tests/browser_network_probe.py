"""Exercise the sandbox browser service with a real Chromium against loopback pages."""
import json
import os
import socket
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
visits = {"secret": 0, "image": 0, "ws": 0}


class Fixture(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/redirect":
            self.send_response(302)
            self.send_header("Location", f"http://localhost:{self.server.server_port}/secret")
            self.end_headers()
            return
        if self.path in ("/secret", "/image", "/ws"):
            visits[self.path[1:]] += 1
        body = (f'<img src="http://localhost:{self.server.server_port}/image">'
                f'<script>new WebSocket("ws://localhost:{self.server.server_port}/ws")</script>') if self.path == "/page" else "Allowed page"
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(body.encode())

    def log_message(self, *args):
        pass


def unused_port():
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


def request(port, action):
    payload = json.dumps(action).encode()
    try:
        with urllib.request.urlopen(urllib.request.Request(f"http://127.0.0.1:{port}", data=payload,
                 headers={"Content-Type": "application/json"}), timeout=40) as response:
            return response.status, json.loads(response.read())
    except urllib.error.HTTPError as error:
        return error.code, json.loads(error.read())


def main():
    fixture = HTTPServer(("127.0.0.1", 0), Fixture)
    threading.Thread(target=fixture.serve_forever, daemon=True).start()
    browser_port = unused_port()
    with tempfile.TemporaryDirectory(prefix="desk-yantra-browser-network-") as directory:
        environment = os.environ | {"PAW_BROWSER_PORT": str(browser_port), "PAW_SANDBOX_ROOT": directory}
        with open(Path(directory) / "browser.log", "wb") as log:
            process = subprocess.Popen([sys.executable, str(ROOT / "sandbox" / "browser_service.py")],
                                       env=environment, stdout=log, stderr=log)
            try:
                deadline = time.monotonic() + 20
                while time.monotonic() < deadline:
                    if process.poll() is not None:
                        raise AssertionError("Browser service exited before startup")
                    try:
                        with socket.create_connection(("127.0.0.1", browser_port), timeout=.2):
                            break
                    except OSError:
                        time.sleep(.1)
                else:
                    raise AssertionError("Browser service readiness timed out")
                base = {"allowed_domains": ["127.0.0.1"]}
                status, result = request(browser_port, base | {"url": f"http://127.0.0.1:{fixture.server_port}/redirect"})
                assert status == 400 and visits["secret"] == 0, f"Redirect policy failed: {status}, {result}, {visits}, {Path(directory, 'browser.log').read_text()}"
                status, result = request(browser_port, base | {"url": f"http://127.0.0.1:{fixture.server_port}/page"})
                assert status == 400 and visits["image"] == 0 and visits["ws"] == 0, f"Resource/WebSocket policy failed: {status}, {result}, {visits}"
                status, result = request(browser_port, base | {"url": f"http://127.0.0.1:{fixture.server_port}/ok"})
                assert status == 200 and "Allowed page" in result.get("text", ""), f"Allowed page failed: {status}, {result}, {Path(directory, 'browser.log').read_text()}"
            finally:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
    fixture.shutdown()
    print("Browser network probe passed: redirect/resource/WebSocket blocked, allowed page loaded")


if __name__ == "__main__":
    main()
