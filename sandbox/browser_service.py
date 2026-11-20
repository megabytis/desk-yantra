import json
import os
from pathlib import Path
from http.server import BaseHTTPRequestHandler, HTTPServer
from playwright.sync_api import sync_playwright


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            action = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            if action.get("url"):
                page.goto(action["url"], wait_until="domcontentloaded", timeout=30000)
            operation=action.get("browser_action","inspect")
            if operation=="click":
                page.mouse.click(float(action["x"]),float(action["y"]))
            elif operation=="type":
                page.keyboard.insert_text(action["content"])
            elif operation=="press":
                page.keyboard.press(action["key"])
            if action.get("selector"):
                if action.get("content"):
                    page.locator(action["selector"]).fill(action["content"])
                else:
                    page.locator(action["selector"]).click()
            page.screenshot(path=str(Path(os.environ.get("PAW_SANDBOX_ROOT", "/workspace")) / "browser.png"))
            result = {"url": page.url, "text": page.inner_text("body")[:100000], "screenshot": "browser.png"}
            self.send_response(200)
        except Exception as error:
            result = {"error": str(error)}
            self.send_response(400)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(result).encode())


with sync_playwright() as playwright:
    browser = playwright.chromium.launch(headless=True)
    page = browser.new_page()
    HTTPServer(("127.0.0.1", int(os.environ.get("PAW_BROWSER_PORT", "9111"))), Handler).serve_forever()
