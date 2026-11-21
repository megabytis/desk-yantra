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


EXTRACT_DOM_SCRIPT = """() => {
    const interactive = [];
    const selectors = 'button, a[href], input, select, textarea, [role="button"], [role="link"], [role="checkbox"], [role="radio"], [role="combobox"], [role="tab"], [role="menuitem"], [onclick], [tabindex="0"]';
    const elements = document.querySelectorAll(selectors);
    let idx = 0;
    for (const el of elements) {
        if (idx >= 100) break;
        const rect = el.getBoundingClientRect();
        const style = window.getComputedStyle(el);
        if (style.display === 'none' || style.visibility === 'hidden' || style.opacity === '0' || rect.width <= 0 || rect.height <= 0) {
            continue;
        }
        const tag = el.tagName.toLowerCase();
        const role = el.getAttribute('role') || tag;
        const type = el.getAttribute('type') || '';
        const name = el.getAttribute('name') || '';
        const id = el.id ? '#' + el.id : '';
        const ariaLabel = el.getAttribute('aria-label') || '';
        const placeholder = el.getAttribute('placeholder') || '';
        const text = (el.innerText || el.textContent || el.value || '').trim().slice(0, 80);
        const href = el.getAttribute('href') || '';
        const disabled = el.hasAttribute('disabled') || el.getAttribute('aria-disabled') === 'true';

        let selector = '';
        if (el.id) selector = '#' + el.id;
        else if (name) selector = tag + '[name="' + name + '"]';
        else if (ariaLabel) selector = tag + '[aria-label="' + ariaLabel + '"]';
        else if (text && (tag === 'button' || tag === 'a')) selector = tag + ':has-text("' + text.slice(0, 20).replace(/"/g, '\\\\"') + '")';
        else selector = tag;

        interactive.push({
            index: idx++,
            tag: tag,
            role: role,
            type: type,
            selector: selector,
            id: el.id || undefined,
            name: name || undefined,
            text: text || undefined,
            aria_label: ariaLabel || undefined,
            placeholder: placeholder || undefined,
            href: href || undefined,
            disabled: disabled,
            bounds: {
                x: Math.round(rect.left + rect.width / 2),
                y: Math.round(rect.top + rect.height / 2),
                width: Math.round(rect.width),
                height: Math.round(rect.height)
            }
        });
    }
    const hasPassword = !!document.querySelector('input[type="password"]');
    const hasCaptcha = !!document.querySelector('iframe[src*="recaptcha"], iframe[src*="hcaptcha"], iframe[src*="turnstile"], .g-recaptcha, .cf-turnstile');
    return {
        elements: interactive,
        has_password: hasPassword,
        has_captcha: hasCaptcha
    };
}"""

browser_state = {
    "playwright": None,
    "browser": None,
    "context": None,
    "pages": [],
    "active_index": 0,
}


def get_active_page():
    ctx = browser_state["context"]
    # Prune closed pages
    browser_state["pages"] = [p for p in browser_state["pages"] if not p.is_closed()]
    if not browser_state["pages"]:
        if ctx:
            p = ctx.new_page()
            browser_state["pages"] = [p]
            browser_state["active_index"] = 0
        else:
            return None
    elif browser_state["active_index"] >= len(browser_state["pages"]):
        browser_state["active_index"] = max(0, len(browser_state["pages"]) - 1)
    return browser_state["pages"][browser_state["active_index"]]


def get_tabs_summary():
    tabs = []
    browser_state["pages"] = [p for p in browser_state["pages"] if not p.is_closed()]
    for idx, p in enumerate(browser_state["pages"]):
        try:
            title = p.title()
        except Exception:
            title = ""
        try:
            url = p.url
        except Exception:
            url = ""
        tabs.append({
            "id": idx,
            "title": title or "Untitled",
            "url": url,
            "active": idx == browser_state["active_index"]
        })
    return tabs


def on_page_opened(p):
    if p not in browser_state["pages"]:
        browser_state["pages"].append(p)


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            raw_body = self.rfile.read(content_length)
            action = json.loads(raw_body) if raw_body else {}
            policy["domains"] = action.get("allowed_domains") or []
            policy["blocked"] = []

            operation = action.get("browser_action", "inspect")
            page = get_active_page()

            if operation == "new_tab":
                new_p = browser_state["context"].new_page()
                browser_state["pages"].append(new_p)
                browser_state["active_index"] = len(browser_state["pages"]) - 1
                page = new_p
                if action.get("url"):
                    page.goto(action["url"], wait_until="domcontentloaded", timeout=30000)
            elif operation == "switch_tab":
                target_id = int(action.get("tab_id", action.get("index", 0)))
                browser_state["pages"] = [p for p in browser_state["pages"] if not p.is_closed()]
                if 0 <= target_id < len(browser_state["pages"]):
                    browser_state["active_index"] = target_id
                page = get_active_page()
                page.bring_to_front()
            elif operation == "close_tab":
                target_id = int(action.get("tab_id", action.get("index", browser_state["active_index"])))
                browser_state["pages"] = [p for p in browser_state["pages"] if not p.is_closed()]
                if 0 <= target_id < len(browser_state["pages"]):
                    to_close = browser_state["pages"][target_id]
                    to_close.close()
                page = get_active_page()
            elif operation == "scroll":
                delta_y = float(action.get("delta_y", action.get("y", 300)))
                delta_x = float(action.get("delta_x", action.get("x", 0)))
                page.mouse.wheel(delta_x, delta_y)
            elif operation == "click":
                page.mouse.click(float(action["x"]), float(action["y"]))
            elif operation == "type":
                page.keyboard.insert_text(action["content"])
            elif operation == "press":
                page.keyboard.press(action["key"])
            elif action.get("url") and operation != "new_tab":
                page.goto(action["url"], wait_until="domcontentloaded", timeout=30000)

            if action.get("selector"):
                if action.get("content"):
                    page.locator(action["selector"]).fill(action["content"])
                else:
                    page.locator(action["selector"]).click()

            if policy["blocked"]:
                raise ValueError("Browser request blocked by workspace network policy")

            # Screenshot
            screenshot_path = Path(os.environ.get("PAW_SANDBOX_ROOT", "/workspace")) / "browser.png"
            page.screenshot(path=str(screenshot_path))

            # Extract DOM elements
            try:
                dom_data = page.evaluate(EXTRACT_DOM_SCRIPT)
            except Exception:
                dom_data = {"elements": [], "has_password": False, "has_captcha": False}

            tabs = get_tabs_summary()
            result = {
                "url": page.url,
                "title": page.title() if not page.is_closed() else "",
                "tabs": tabs,
                "active_tab": browser_state["active_index"],
                "text": page.inner_text("body")[:100000] if not page.is_closed() else "",
                "elements": dom_data.get("elements", []),
                "requires_user_takeover": dom_data.get("has_captcha", False),
                "sensitive_fields": ["password"] if dom_data.get("has_password", False) else [],
                "screenshot": "browser.png"
            }
            self.send_response(200)
        except Exception as error:
            result = {"error": "Browser request or redirect blocked by workspace network policy" if policy["blocked"] else str(error)}
            try:
                if page and not page.is_closed():
                    page.close()
                new_page = browser_state["context"].new_page()
                if 0 <= browser_state["active_index"] < len(browser_state["pages"]):
                    browser_state["pages"][browser_state["active_index"]] = new_page
                else:
                    browser_state["pages"] = [new_page]
                    browser_state["active_index"] = 0
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
        first_page = context.new_page()
        browser_state.update({
            "playwright": playwright,
            "browser": browser,
            "context": context,
            "pages": [first_page],
            "active_index": 0,
        })
        context.on("page", on_page_opened)
        HTTPServer(("127.0.0.1", int(os.environ.get("PAW_BROWSER_PORT", "9111"))), Handler).serve_forever()
