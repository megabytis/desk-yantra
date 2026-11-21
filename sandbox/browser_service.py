import json
import os
import ipaddress
from urllib.parse import urlsplit, urljoin
from pathlib import Path
from http.server import BaseHTTPRequestHandler, HTTPServer
from playwright.sync_api import sync_playwright


def allowed_request(url, domains):
    """Apply the workspace's navigation rule to every browser network request."""
    try:
        parsed = urlsplit(url)
        host = (parsed.hostname or "").lower().rstrip(".")
        if parsed.scheme not in ("http", "https") or not host:
            return False
        if host in ("metadata.google.internal", "metadata.aws.internal", "fd00:ec2::254"):
            return False
        try:
            if ipaddress.ip_address(host).is_link_local:
                return False
        except ValueError:
            pass
        if domains:
            return any(
                host == domain or host == "www." + domain or
                (domain.startswith("*.") and (host == domain[2:] or host.endswith(domain[1:])))
                for item in domains if (domain := str(item).strip().lower().rstrip("."))
            )
        return True
    except ValueError:
        return False


policy = {"domains": [], "blocked": []}


def guard_request(route):
    url = route.request.url
    if allowed_request(url, policy["domains"]):
        try:
            # Playwright does not reroute Chromium's redirect hop. Refuse the
            # redirect before the browser can contact an unchecked host.
            response = route.fetch(max_redirects=0)
            if 300 <= response.status < 400 and response.headers.get("location"):
                policy["blocked"].append(urljoin(url, response.headers["location"]))
                route.abort()
            else:
                route.fulfill(response=response)
        except Exception:
            route.abort()
    else:
        policy["blocked"].append(url)
        route.abort()


def guard_websocket(route):
    parsed = urlsplit(route.url)
    web_url = parsed._replace(scheme="https" if parsed.scheme == "wss" else "http").geturl()
    if parsed.scheme in ("ws", "wss") and allowed_request(web_url, policy["domains"]):
        route.connect_to_server()
    else:
        policy["blocked"].append(route.url)
        route.close(code=1008, reason="Blocked by workspace network policy")


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        global page
        try:
            action = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            policy["domains"] = action.get("allowed_domains") or []
            policy["blocked"] = []
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
            if policy["blocked"]:
                raise ValueError("Browser request blocked by workspace network policy")
            page.screenshot(path=str(Path(os.environ.get("PAW_SANDBOX_ROOT", "/workspace")) / "browser.png"))
            result = {"url": page.url, "text": page.inner_text("body")[:100000], "screenshot": "browser.png"}
            self.send_response(200)
        except Exception as error:
            result = {"error": "Browser request or redirect blocked by workspace network policy" if policy["blocked"] else str(error)}
            try:
                page.close()
                page = context.new_page()
            except Exception:
                pass
            self.send_response(400)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(result).encode())


if __name__ == "__main__":
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context(accept_downloads=False, service_workers="block")
        context.route("**/*", guard_request)
        context.route_web_socket("**/*", guard_websocket)
        page = context.new_page()
        HTTPServer(("127.0.0.1", int(os.environ.get("PAW_BROWSER_PORT", "9111"))), Handler).serve_forever()
